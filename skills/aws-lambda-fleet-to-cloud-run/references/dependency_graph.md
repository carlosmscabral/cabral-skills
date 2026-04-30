# Dependency Graph & Migration Wave Sequencing

Migrating Lambdas in the wrong order can cause production outages. This guide explains how to read the dependency output from `analyze_fleet.py` and sequence migrations so that no function's dependencies are broken mid-migration.

---

## 1. Why Sequencing Matters

Consider `FnA` (API handler) that synchronously invokes `FnB` (validation service) via `boto3.client('lambda').invoke(...)`.

- If you migrate `FnA` to Cloud Run **before** `FnB`, `FnA` now needs to call `FnB` cross-environment. You must add a temporary bridge or the integration breaks.
- If you migrate `FnB` first, `FnA` (still a Lambda) can call the migrated `FnB` via its Cloud Run HTTPS URL — the bridge is simpler (Lambda → HTTPS is trivial).

**The rule:** Migrate functions that others depend *on* (callees) **before** the functions that call them (callers).

---

## 2. Reading `dependency_edges` from `fleet_manifest.json`

The fleet manifest contains a `dependency_edges` array:

```json
"dependency_edges": [
  { "from": "CreateOrder",  "to": "ProcessPayment",    "via": "sns_topic",     "resource": "order-events" },
  { "from": "CreateOrder",  "to": "SendNotification",  "via": "sns_topic",     "resource": "order-events" },
  { "from": "CreateOrder",  "to": "ProcessOrder",      "via": "direct_invoke", "resource": null },
  { "from": "NightlyReconcile", "to": null,            "via": "s3_write",      "resource": "reports-bucket" }
]
```

**Edge types detected by `analyze_fleet.py`:**

| `via` value | Meaning | Blocking? |
|---|---|---|
| `direct_invoke` | `boto3.client('lambda').invoke(...)` — synchronous | **Yes** — callee must migrate first |
| `step_function` | AWS Step Function ASL references this function | **Yes** — orchestrated; entire state machine is a unit |
| `sns_topic` | Publisher and subscriber share an SNS topic | **Partial** — async; bridge is possible but messy |
| `sqs_queue` | Producer and consumer share an SQS queue | **Partial** — async; bridge via Cloud Tasks is possible |
| `s3_write` | Function writes to an S3 bucket (no consumer here) | **No** — leaf node; migrate freely |

---

## 3. Topological Sort → Migration Waves

Apply a standard topological sort to `dependency_edges` (treat `from → to` as a directed edge meaning "from depends on to"):

1. **Find leaf nodes** (functions with no outbound `direct_invoke` or `step_function` edges). These go into **Wave 1**.
2. Remove Wave 1 nodes from the graph. Find the new leaf nodes → **Wave 2**.
3. Repeat until all nodes are assigned.

**Example using the e-commerce estate:**

Edges (blocking only):
- `CreateOrder → ProcessOrder` (direct_invoke)

SNS edges (non-blocking, async):
- `CreateOrder → ProcessPayment` (sns_topic)
- `CreateOrder → SendNotification` (sns_topic)

Topological sort result:

| Wave | Functions | Reason |
|---|---|---|
| **Wave 1** | `ProcessPayment`, `SendNotification`, `NightlyReconcile` | No outbound blocking dependencies (they are callees / leaf nodes) |
| **Wave 2** | `ProcessOrder` | Depended on by `CreateOrder`; must be migrated before it |
| **Wave 3** | `CreateOrder`, `GetOrderStatus` | Callers of Wave 2; domain consolidation into `svc-orders` |

---

## 4. Cross-Cloud Invocation Bridge

During the transition window (some Lambdas migrated, some not), you need temporary bridges. Remove all bridge code after full migration is complete.

### 4.1 Lambda → Cloud Run (Cloud Run is migrated first)

The Lambda still needs to call the logic that has moved to Cloud Run.

**In the Lambda code (Python example):**
```python
import urllib.request
import json
import google.auth
import google.auth.transport.requests

def call_cloud_run_service(url: str, payload: dict) -> dict:
    """Call a Cloud Run service from AWS Lambda using a service account key."""
    # NOTE: During migration only. Use a GCP service account JSON key stored
    # in AWS Secrets Manager. Remove after full migration.
    credentials, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    id_token = credentials.token

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {id_token}')
    req.add_header('Content-Type', 'application/json')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
```

**Required setup:**
1. Create a GCP Service Account with `roles/run.invoker` on the target Cloud Run service.
2. Export a JSON key (temporary, migration only).
3. Store key in AWS Secrets Manager. Retrieve in Lambda via `boto3.client('secretsmanager')`.

### 4.2 Cloud Run → Lambda (Lambda is NOT yet migrated)

A Cloud Run service needs to call a Lambda that hasn't been migrated yet.

**In the Cloud Run service (Python example):**
```python
import boto3
import json
import os

def call_lambda(function_name: str, payload: dict) -> dict:
    """Call an AWS Lambda from Cloud Run — temporary migration bridge."""
    # NOTE: Use Workload Identity Federation to avoid long-lived keys.
    # Store AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY in GCP Secret Manager
    # mounted at /secrets/aws-creds — remove after Lambda is migrated.
    client = boto3.client(
        'lambda',
        region_name=os.environ.get('AWS_REGION', 'us-east-1'),
        aws_access_key_id=open('/secrets/aws-creds/access_key').read().strip(),
        aws_secret_access_key=open('/secrets/aws-creds/secret_key').read().strip()
    )
    response = client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode('utf-8')
    )
    return json.loads(response['Payload'].read())
```

**Required setup:**
1. Create an AWS IAM user with `lambda:InvokeFunction` permission on the specific target Lambda ARN.
2. Store credentials in GCP Secret Manager.
3. Mount the secret as a volume in the Cloud Run service configuration.

### 4.3 SNS Bridge (async topics)

If a Lambda publishes to SNS and a Cloud Run service now needs to consume those messages:

1. Create a **Pub/Sub topic** on GCP (e.g., `order-events`).
2. Keep the AWS SNS subscription for the legacy Lambda consumer.
3. Add a new **HTTPS subscription** to the SNS topic pointing to the Cloud Run service URL — SNS will deliver directly via HTTP POST.
4. Once all consumers are on GCP, remove the SNS topic and replace the publisher with Pub/Sub.

---

## 5. Wave Planning Template

Fill this table in the Migration Program Document for the customer:

| Wave | Lambda(s) | Target Cloud Run Service | Migration Pattern | Cross-Cloud Bridge Required? | Status |
|---|---|---|---|---|---|
| 1 | `ProcessPayment` | `svc-payments` | 1:1 Service | No (callee, migrate first) | ⬜ |
| 1 | `SendNotification` | `svc-notifications` | 1:1 Service | No | ⬜ |
| 1 | `NightlyReconcile` | `job-reconcile` | 1:1 Job | No | ⬜ |
| 2 | `ProcessOrder` | `svc-order-processor` | 1:1 Service | Lambda→CR bridge for `CreateOrder` | ⬜ |
| 3 | `CreateOrder`, `GetOrderStatus` | `svc-orders` | Domain Consolidation | Remove bridge after this wave | ⬜ |

**Status legend:** ⬜ Not started · 🔄 In progress · ✅ Complete · ❌ Blocked
