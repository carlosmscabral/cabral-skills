# Lambda Consolidation Patterns

This reference covers the mechanics of merging multiple AWS Lambda handlers into a single Cloud Run service. These patterns apply when the fleet grouping strategy (see `references/fleet_strategy.md`) recommends **Pattern B: Domain Consolidation**.

---

## When to Consolidate

Before applying these patterns, confirm the grouping meets Pattern B criteria:
- Functions share the same database table or message queue (high cohesion).
- Functions use the same runtime and language.
- The same team owns all functions in the group.
- Functions have direct Lambda-to-Lambda invocations (in-process calls eliminate network latency).

---

## Pattern 1: Router Pattern

Add a thin HTTP routing layer that dispatches requests to the original handler functions. The handler logic is **not refactored** — each former Lambda handler becomes a callable function.

**Use this when:** Functions have minimal shared initialization and you want the quickest path to Cloud Run.

### Before (3 separate Lambdas, Python)

```python
# create_order/handler.py
def handler(event, context):
    # ... Lambda event parsing, DynamoDB write, SNS publish
    return {"statusCode": 201, "body": json.dumps({"id": order_id})}

# get_order/handler.py
def handler(event, context):
    # ... Lambda event parsing, DynamoDB read
    return {"statusCode": 200, "body": json.dumps(order)}

# delete_order/handler.py
def handler(event, context):
    # ... Lambda event parsing, DynamoDB delete
    return {"statusCode": 204, "body": ""}
```

### After (Single Cloud Run service, Python + Flask)

```python
# app.py — Cloud Run entrypoint
from flask import Flask, request, jsonify
import os

# Import former Lambda handlers as modules
from handlers.create_order import handler as create_handler
from handlers.get_order import handler as get_handler
from handlers.delete_order import handler as delete_handler

app = Flask(__name__)

# Shim: translate HTTP request → Lambda-style event dict
def http_to_lambda_event(req, path_params=None):
    return {
        "httpMethod": req.method,
        "path": req.path,
        "headers": dict(req.headers),
        "queryStringParameters": req.args.to_dict(),
        "pathParameters": path_params or {},
        "body": req.get_data(as_text=True),
    }

@app.route("/orders", methods=["POST"])
def create_order():
    result = create_handler(http_to_lambda_event(request), {})
    return jsonify(result.get("body", {})), result.get("statusCode", 200)

@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    result = get_handler(http_to_lambda_event(request, {"orderId": order_id}), {})
    return jsonify(result.get("body", {})), result.get("statusCode", 200)

@app.route("/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    result = delete_handler(http_to_lambda_event(request, {"orderId": order_id}), {})
    return result.get("body", ""), result.get("statusCode", 204)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
```

**Dockerfile:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## Pattern 2: Handler-as-Module Pattern

Each Lambda handler is refactored into a class or module with a clean interface. The Cloud Run service instantiates them and routes requests via a dispatch table. Shared resources (DB connections, SDK clients) are initialized once at startup.

**Use this when:** You want to fully refactor the handlers and maximize shared initialization efficiency.

### Before (Node.js — 3 separate Lambda handlers)

```javascript
// Each in its own Lambda function
exports.handler = async (event) => { /* DynamoDB init + logic */ };
```

### After (Node.js + Express — Single Cloud Run service)

```javascript
// app.js
const express = require('express');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb'); // still present during migration
// OR: const { Firestore } = require('@google-cloud/firestore'); // after migration

const app = express();
app.use(express.json());

// --- Shared initialization (runs once at container startup) ---
// BEFORE (AWS): const db = new DynamoDBClient({ region: 'us-east-1' });
// AFTER (GCP):  const db = new Firestore();
const db = new Firestore(); // initialize once, reuse across all requests

// --- Import handler modules ---
const { createOrder } = require('./handlers/createOrder')(db);
const { getOrder }    = require('./handlers/getOrder')(db);
const { deleteOrder } = require('./handlers/deleteOrder')(db);

// --- Routes ---
app.post('/orders',          createOrder);
app.get('/orders/:id',       getOrder);
app.delete('/orders/:id',    deleteOrder);

const port = process.env.PORT || 8080;
app.listen(port, () => console.log(`Listening on port ${port}`));
```

```javascript
// handlers/createOrder.js — handler module accepting injected db
module.exports = (db) => ({
    createOrder: async (req, res) => {
        const order = req.body;
        // ... use injected db client
        res.status(201).json({ id: newOrderId });
    }
});
```

---

## 3. Shared Initialization

This is the largest efficiency gain from consolidation. In Lambda, every function initializes its own DB connection pool, SDK clients, and config on each cold start. In a consolidated Cloud Run service, initialization happens **once** when the container starts.

### Connection Pool Example (Python + PostgreSQL)

**Before (Lambda — re-initialized per invocation):**
```python
# In each Lambda handler — connection created every cold start
import psycopg2
def handler(event, context):
    conn = psycopg2.connect(os.environ['DB_URL'])  # cold start cost!
    # ... use conn
    conn.close()
```

**After (Cloud Run — connection pool initialized once):**
```python
# app.py — at module level, before any request handler
import psycopg2.pool
import os

# Initialized once when the container starts, reused for all concurrent requests
_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,  # tune to Cloud Run concurrency setting
    dsn=os.environ['DB_URL']
)

def get_conn():
    return _pool.getconn()

def release_conn(conn):
    _pool.putconn(conn)
```

> [!WARNING]
> **PHP-specific risk**: PHP-FPM runs one request per worker (similar to Lambda). Only FrankenPHP or RoadRunner enable shared worker state. See `aws-lambda-to-cloud-run-migration/references/containerization.md` for PHP consolidation details.

---

## 4. Pitfalls & Anti-Patterns

| Pitfall | Description | Mitigation |
|---|---|---|
| **Global mutable state** | Lambda handlers written assuming single-threaded isolation will fail when running concurrently in one container | Audit for module-level variables mutated per-request; move to request-scoped locals |
| **Timeout mismatch** | Lambda max timeout is 15 min; Cloud Run Service max is 60 min. Consolidated services may aggregate timeout budget incorrectly | Set per-route timeouts explicitly; use Cloud Run Jobs for long-running work |
| **Memory allocation** | Lambda memory = CPU proxy. Cloud Run separates memory and CPU. A consolidated service handling multiple workload profiles needs tuning | Start at the sum of constituent Lambda memory settings; tune down after load testing |
| **Conflicting env vars** | Two Lambdas may have `TABLE_NAME` pointing to different DynamoDB tables | Rename env vars in the consolidated service: `ORDERS_TABLE_NAME`, `USERS_TABLE_NAME` |
| **Different IAM needs** | Consolidating Lambdas with different IAM roles into one service means the service account needs the union of all permissions — potential over-privilege | Review combined permissions; consider splitting if security boundary is critical |

---

## 5. Recommended Directory Structure for Consolidated Service

```
svc-orders/
├── app.py                  # Cloud Run entrypoint + router
├── handlers/
│   ├── __init__.py
│   ├── create_order.py     # Former Lambda handler, refactored to module
│   ├── get_order.py
│   └── delete_order.py
├── shared/
│   ├── __init__.py
│   ├── db.py               # Shared DB connection pool
│   └── clients.py          # Shared GCP SDK client initialization
├── Dockerfile
└── requirements.txt
```
