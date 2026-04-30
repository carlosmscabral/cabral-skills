# Advanced Service Mapping: AWS to Google Cloud

This reference provides mapping for complex AWS serverless architectures, specifically focusing on how invocations and triggers translate to Google Cloud native patterns.

## 1. Invocation & Trigger Strategy

AWS Lambda supports many proprietary invocation methods. In contrast, **Google Cloud Run is fundamentally an HTTP server**. Everything that triggers a Cloud Run service ultimately results in an HTTP request.

### Direct Invocations
- **AWS Pattern:** Another service or script uses the AWS SDK to call `boto3.client('lambda').invoke(...)` passing a custom JSON payload.
- **GCP Migration:** The caller must make a standard HTTP POST request to the Cloud Run service URL.
- **Security:** If the Cloud Run service is private (no unauthenticated access), the calling service must generate a **Google ID Token (OIDC)** using its IAM Service Account and pass it in the `Authorization: Bearer <TOKEN>` header.

### API Gateway & HTTP
- **AWS Pattern:** Lambda sits behind Amazon API Gateway or ALB for REST APIs, handling routing, rate limiting, and auth.
- **GCP Migration:**
  - **Direct URL (Most Common):** Cloud Run provides a built-in, auto-scaling HTTPS URL. Many AWS API Gateway use-cases can be retired simply by exposing the Cloud Run URL.
  - **Google Cloud API Gateway:** Use this if you specifically need API Keys, strict rate limiting, or protocol translation.
  - **Global Load Balancer + IAP:** Use this if you need multi-region routing, WAF, or enterprise auth mapping (Identity-Aware Proxy).

### Event-Driven Triggers (SNS / SQS / S3 / EventBridge)
In GCP, asynchronous events are routed to Cloud Run via HTTP POST requests containing data formatted to the open **CloudEvents** specification.

| AWS Source | GCP Equivalent | Trigger Mechanism |
| :--- | :--- | :--- |
| **S3 Events** | **Cloud Storage** | **Eventarc** listens to Cloud Storage and pushes a CloudEvent to the Cloud Run HTTP endpoint. |
| **SNS (Topics)** | **Pub/Sub (Topics)** | Configure a **Push Subscription** that POSTs the message to the Cloud Run URL. |
| **SQS (Queues)** | **Cloud Tasks** (or Pub/Sub) | **Cloud Tasks** is the preferred equivalent for triggering HTTP endpoints with rate limiting, retries, and scheduled execution. |
| **EventBridge / Cron** | **Eventarc / Cloud Scheduler** | Use **Cloud Scheduler** to fire regular HTTP requests (cron) or Eventarc for cross-service events. |

## 2. Advanced Orchestration & Logic

| AWS Service | Google Cloud Equivalent | Migration Strategy |
| :--- | :--- | :--- |
| **Step Functions** | **Workflows** | Convert JSON/YAML ASL (Amazon States Language) to YAML Workflows. Workflows orchestrates HTTP calls to Cloud Run. |
| **Lambda Layers** | **Multi-stage Docker Builds** | Instead of separate layers, use Dockerfile layers for shared dependencies. Install common libraries in a base image. |
| **Lambda Destinations** | **Eventarc / Pub/Sub** | Let the Cloud Run service emit HTTP calls to a Pub/Sub topic to signify success/failure routing. |

## 3. Operations & Observability

| AWS Feature | Google Cloud Feature | Implementation |
| :--- | :--- | :--- |
| **CloudWatch Logs** | **Cloud Logging** | Application logs sent to `stdout`/`stderr` are automatically captured. |
| **CloudWatch Metrics** | **Cloud Monitoring** | Pre-built dashboards for Cloud Run (Requests, Latency, CPU/Memory). |
| **X-Ray** | **Cloud Trace** | Use OpenTelemetry or the Google Cloud Trace SDK for distributed tracing. |

## 4. File Systems & Persistent Storage

AWS Lambda instances are ephemeral, but they allow mounting an Amazon EFS (Elastic File System) to share large datasets or persist files across invocations that exceed the local `/tmp` limit.

### AWS EFS Mapping to Cloud Run
Cloud Run instances are also ephemeral, but you have two primary options for mounting external file systems:

1.  **Cloud Storage FUSE (Recommended for most):**
    -   **AWS Counterpart:** S3 as a file system (often used as a cheaper EFS alternative).
    -   **Use Case:** Reading large machine learning models, configuration files, or serving static media.
    -   **Behavior:** Mounts a Google Cloud Storage bucket as a local file system path (e.g., `/mnt/bucket`). It is optimized for *reads*. Writes are supported but lack POSIX compliance for concurrent file locking.
2.  **NFS & Google Cloud Filestore (Enterprise):**
    -   **AWS Counterpart:** Amazon EFS.
    -   **Use Case:** True enterprise NFS. Best for legacy applications that require POSIX-compliant file locking, heavy concurrent read/writes, or shared state between thousands of instances.
    -   **Requirement:** Your Cloud Run service must be connected to the VPC where the NFS server resides (preferably using Direct VPC, `vpc-egress=all-traffic`). 
    -   **Implementation:** Cloud Run now supports native NFS volume mounts. You configure the volume type as `nfs` and point it to the Filestore IP address.
    -   *Example:* `gcloud run services update SERVICE --add-volume=name=nfs-vol,type=nfs,location=IP_ADDRESS:/share1 --add-volume-mount=volume=nfs-vol,mount-path=/mnt/nfs`

## 5. Database Connectivity — RDS Proxy → Cloud SQL Auth Proxy

### Why RDS Proxy Exists on Lambda

AWS Lambda cannot hold persistent TCP connections. Each cold-starting instance opens a fresh database connection, which can overwhelm RDS connection limits at scale. **RDS Proxy** acts as a managed connection pool that sits between Lambda and RDS/Aurora — Lambda talks to the proxy, which multiplexes connections to the real database.

**Cloud Run is fundamentally different.** Cloud Run instances can hold persistent connections for the lifetime of the container, so connection pooling can happen *in-process* (e.g., via `pg-pool`, `SQLAlchemy`, `HikariCP`). However, the auth challenge still exists: Cloud Run must authenticate to Cloud SQL securely without storing DB passwords in env vars.

### Cloud SQL Auth Proxy — The GCP Equivalent

The **Cloud SQL Auth Proxy** handles IAM-based authentication and TLS termination between Cloud Run and Cloud SQL. On Cloud Run Gen 2, it runs as a **sidecar container** — you don't need to install it in your main container.

**Architecture:**
```
Cloud Run Instance
┌────────────────────────────────────┐
│  [App Container]  →  localhost:5432│──→ [Cloud SQL Auth Proxy Sidecar] ──→ Cloud SQL
└────────────────────────────────────┘         (handles IAM auth + TLS)
```

### Terraform — Multi-Container Cloud Run with Cloud SQL Proxy Sidecar

```terraform
resource "google_cloud_run_v2_service" "app" {
  name     = "my-app"
  location = "us-central1"

  template {
    service_account = google_service_account.app_sa.email

    containers {
      # 1. Main application container
      name  = "app"
      image = "us-central1-docker.pkg.dev/${var.project_id}/my-repo/my-app:latest"

      env {
        name  = "DB_HOST"
        value = "localhost"  # Talks to the proxy sidecar on localhost
      }
      env {
        name  = "DB_PORT"
        value = "5432"
      }
      env {
        name  = "DB_NAME"
        value = "mydb"
      }
      env {
        name = "DB_USER"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_user.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "DB_PASS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_pass.secret_id
            version = "latest"
          }
        }
      }

      # Ensure app starts after the proxy is ready
      depends_on = ["cloud-sql-proxy"]
    }

    containers {
      # 2. Cloud SQL Auth Proxy sidecar
      name  = "cloud-sql-proxy"
      image = "gcr.io/cloud-sql-connectors/cloud-sql-proxy:2"
      args  = [
        "--structured-logs",
        "--port=5432",
        "${var.project_id}:${var.region}:${var.cloud_sql_instance_name}"
      ]
      resources {
        limits = { cpu = "0.5", memory = "128Mi" }
      }
    }
  }
}

# Grant the service account Cloud SQL access (replaces RDS Proxy IAM role)
resource "google_project_iam_member" "sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.app_sa.email}"
}
```

### gcloud — Sidecar Deployment (Path B)

```bash
gcloud run deploy my-app \
  --image="us-central1-docker.pkg.dev/${PROJECT_ID}/my-repo/my-app:latest" \
  --region=us-central1 \
  --service-account="app-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --container=app \                            # name the main container
  --add-cloudsql-instances="${PROJECT_ID}:us-central1:my-instance" \
  --set-env-vars="DB_HOST=/cloudsql/${PROJECT_ID}:us-central1:my-instance,DB_PORT=5432"
  # The --add-cloudsql-instances flag injects the proxy automatically (no sidecar yaml needed)
```

> **Note:** `--add-cloudsql-instances` is the simpler single-container path. Use the Terraform multi-container approach when you need fine-grained resource limits on the proxy or when you have multiple Cloud SQL instances.

### Migration Checklist: RDS → Cloud SQL

| AWS Config | Cloud Run Action |
| :--- | :--- |
| RDS Proxy endpoint in env var | Replace with `localhost:5432` (proxy runs as sidecar) |
| RDS IAM auth (`rds-db:connect`) | Grant `roles/cloudsql.client` to the Cloud Run Service Account |
| `DB_PASSWORD` in AWS Secrets Manager | Move to **Secret Manager**, mount as env var or volume |
| `ssl-mode=verify-full` | Proxy handles TLS automatically — set `ssl-mode=disable` in app (proxy connection is on localhost) |
| Connection pool size set to `1` (Lambda best practice) | Increase pool to `5–20` — Cloud Run instances are long-lived |

---

## 6. Caching & Sessions — ElastiCache → Memorystore

### Service Mapping

| AWS Service | GCP Equivalent | Notes |
| :--- | :--- | :--- |
| **ElastiCache for Redis** | **Memorystore for Redis** | Drop-in compatible — same Redis protocol/client libraries |
| **ElastiCache for Memcached** | **Memorystore for Memcached** | Same Memcached protocol; limited feature parity |
| **ElastiCache Serverless** | **Memorystore for Redis (Standard/Cluster)** | Choose tier based on throughput needs |

**Critical requirement:** Memorystore instances live inside a VPC. Cloud Run **must** use **Direct VPC Egress** or a **Serverless VPC Access Connector** to reach them.

```bash
# Enable VPC egress (required for any Memorystore access)
gcloud run services update my-service \
  --vpc-connector=projects/${PROJECT_ID}/locations/${REGION}/connectors/my-connector \
  --vpc-egress=private-ranges-only
  # OR for Direct VPC (Gen 2, preferred):
  # --network=my-vpc --subnet=my-subnet --vpc-egress=private-ranges-only
```

---

### Session Handling — Why This Matters on Cloud Run

AWS Lambda is effectively **stateless** — every invocation may hit a different instance, so session state *must* be stored externally (ElastiCache Redis). This maps directly to Cloud Run which is also multi-instance. The migration challenge is ensuring all Cloud Run instances point to the same **Memorystore** endpoint rather than in-process memory.

#### PHP — Session Handler Migration (Most Common Case)

PHP's default `session.save_handler = files` stores sessions on local disk — **this will break on Cloud Run** because each container instance has its own ephemeral filesystem.

**BEFORE (AWS Lambda + Bref — sessions fail silently, usually disabled):**
```php
// Lambda is stateless — most Bref apps disable sessions entirely
// or use a custom handler that writes to DynamoDB/ElastiCache
ini_set('session.save_handler', 'redis');
ini_set('session.save_path', 'tcp://' . getenv('ELASTICACHE_ENDPOINT') . ':6379');
```

**AFTER (Cloud Run + Memorystore for Redis):**

*Option A — php.ini / runtime configuration (recommended):*
```php
<?php
// config/bootstrap.php — loaded before any session_start()
ini_set('session.save_handler', 'redis');
ini_set('session.save_path', 'tcp://' . getenv('MEMORYSTORE_HOST') . ':6379');
// For Redis AUTH (if enabled on your Memorystore instance):
// ini_set('session.save_path', 'tcp://' . getenv('MEMORYSTORE_HOST') . ':6379?auth=' . getenv('REDIS_AUTH'));
session_start();
```

*Option B — php.ini in the Docker image (twelve-factor approach):*
```ini
; docker/php.ini — baked into the image, overridden by env var at runtime
session.save_handler = redis
session.save_path = "tcp://MEMORYSTORE_HOST_PLACEHOLDER:6379"
```
```dockerfile
FROM php:8.2-fpm-alpine
RUN pecl install redis && docker-php-ext-enable redis
COPY docker/php.ini /usr/local/etc/php/conf.d/sessions.ini
# Override the placeholder at runtime via entrypoint:
CMD ["/bin/sh", "-c", "sed -i \"s|MEMORYSTORE_HOST_PLACEHOLDER|${MEMORYSTORE_HOST}|g\" /usr/local/etc/php/conf.d/sessions.ini && php-fpm"]
```

*Option C — Laravel (SessionDriver):*
```php
// config/session.php
'driver' => env('SESSION_DRIVER', 'redis'),
'connection' => 'default',  // uses config/database.php redis config

// config/database.php
'redis' => [
    'default' => [
        'host'     => env('MEMORYSTORE_HOST', '127.0.0.1'),
        'password' => env('REDIS_AUTH', null),
        'port'     => env('REDIS_PORT', 6379),
        'database' => 0,
    ],
],
```
```bash
# Cloud Run env vars
gcloud run services update my-laravel-app \
  --set-env-vars="SESSION_DRIVER=redis,MEMORYSTORE_HOST=10.0.0.3,REDIS_PORT=6379"
```

> **PHP FrankenPHP / RoadRunner Warning:** When using persistent PHP workers (FrankenPHP, RoadRunner), PHP worker state *persists between requests*. If session data leaks into a global variable or singleton, it will pollute subsequent requests. Use `session_destroy()` and `session_write_close()` explicitly at the end of each request handler.

---

#### Python — Session Migration

**BEFORE (Flask + Lambda — stateless, no sessions, or DynamoDB sessions):**
```python
# Common Lambda pattern: no server-side sessions; JWTs or DynamoDB used instead
```

**AFTER (Flask + Cloud Run + Memorystore):**
```python
# requirements.txt additions:
# Flask-Session==0.8.0
# redis==5.0.1

from flask import Flask, session
from flask_session import Session
import redis, os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.Redis(
    host=os.environ['MEMORYSTORE_HOST'],
    port=int(os.environ.get('REDIS_PORT', 6379)),
    decode_responses=False
)
app.secret_key = os.environ['SECRET_KEY']
Session(app)
```

**AFTER (FastAPI — stateless JWT pattern, recommended for Cloud Run):**
```python
# FastAPI best practice on Cloud Run: avoid server-side sessions entirely.
# Use short-lived JWTs verified with google-auth or a custom secret.
# This eliminates the Memorystore dependency for auth flows.
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token = Depends(security)):
    # Verify JWT — no Redis needed
    ...
```

---

#### Node.js — Session Migration

**BEFORE (Express + Lambda — sessions usually not used or stored in DynamoDB):**
```javascript
// Lambda: most apps use stateless JWTs or custom DynamoDB session stores
```

**AFTER (Express + Cloud Run + Memorystore):**
```javascript
// npm install express-session connect-redis ioredis
const session = require('express-session');
const RedisStore = require('connect-redis').default;
const { Redis } = require('ioredis');

const redisClient = new Redis({
  host: process.env.MEMORYSTORE_HOST,
  port: process.env.REDIS_PORT || 6379,
  // password: process.env.REDIS_AUTH,  // if AUTH enabled on Memorystore
});

app.use(session({
  store: new RedisStore({ client: redisClient }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { secure: true, maxAge: 3600000 }  // 1 hour
}));
```

---

#### General Caching (All Languages) — ElastiCache → Memorystore

```python
# Python — identical Redis client, just swap the host env var
import redis, os
cache = redis.Redis(host=os.environ['MEMORYSTORE_HOST'], port=6379, decode_responses=True)
cache.setex('my-key', 300, 'value')       # TTL 5 min
value = cache.get('my-key')
```

```javascript
// Node.js — same ioredis client, different host
const { Redis } = require('ioredis');
const cache = new Redis({ host: process.env.MEMORYSTORE_HOST, port: 6379 });
await cache.setex('my-key', 300, JSON.stringify(data));
```

```go
// Go — same go-redis client
import "github.com/redis/go-redis/v9"
rdb := redis.NewClient(&redis.Options{
    Addr: os.Getenv("MEMORYSTORE_HOST") + ":6379",
})
rdb.Set(ctx, "my-key", value, 5*time.Minute)
```

### Migration Checklist: ElastiCache → Memorystore

| Item | Action |
| :--- | :--- |
| ElastiCache endpoint in env var | Replace `ELASTICACHE_ENDPOINT` with `MEMORYSTORE_HOST` (same Redis protocol) |
| Redis AUTH password | Store in **Secret Manager**, mount as env var `REDIS_AUTH` |
| VPC access | Enable Direct VPC Egress on Cloud Run (`--network`, `--subnet`) |
| PHP file sessions | Switch to `session.save_handler=redis` via `php.ini` or `ini_set()` |
| Security Group rule | Create a **Firestore VPC Firewall rule** allowing Cloud Run subnet → Memorystore port 6379 |
| `cluster_mode=enabled` | Memorystore supports Cluster mode — use `redis.RedisCluster()` client instead of `redis.Redis()` |

---

## 7. Environment & Secrets



### Environment Variables
- Map AWS Lambda environment variables directly to **Cloud Run Environment Variables**.

### Secrets
- **AWS Secrets Manager** -> **Secret Manager**.
- **Usage:** In Cloud Run, mount secrets as environment variables or as files volume-mounted directly within the container for better security.

## 8. Migration Complexity Matrix

- **Low:** Simple HTTP APIs via API Gateway, Cron jobs -> *Migrate to direct Cloud Run URLs or Cloud Scheduler.*
- **Medium:** Functions with S3/SQS/SNS triggers -> *Requires mapping proprietary AWS JSON event payloads to GCP CloudEvents / Pub/Sub payloads.*
- **High:** Heavy SDK usage for direct invocations (`lambda.invoke`), Step Functions, DynamoDB Streams -> *Requires significant refactoring of the calling services to handle standard HTTP+OIDC auth.*

---

## 9. Known Incompatibilities — Do NOT Migrate to Cloud Run

> **⚠️ WARNING:** The following Lambda variants are **architecturally incompatible** with Cloud Run. Identify these patterns early and recommend the correct GCP alternative instead — do not attempt a direct migration.

### Lambda@Edge and CloudFront Functions

**Why they are different:** Lambda@Edge and CloudFront Functions run *inside the AWS CDN layer* at edge PoPs worldwide, with strict constraints (sub-1 ms budget for CloudFront Functions, 5–30 s for Lambda@Edge, no VPC, no env vars for CloudFront Functions). They intercept and mutate HTTP requests/responses **at the CDN level** — not at the origin server level.

**Cloud Run is the wrong target.** Cloud Run is an origin server. Routing a request through Cloud Run negates the CDN-edge latency benefit entirely.

**Correct GCP alternatives:**

| Pattern | Use Case | GCP Equivalent |
| :--- | :--- | :--- |
| **CloudFront Functions** | URL rewrites, header injection, auth redirects at <1 ms | **Cloud CDN URL Maps** (routing rules / header actions) or **Media CDN** |
| **Lambda@Edge (viewer request/response)** | A/B testing, bot detection, auth at edge | **Google Cloud Armor** (WAF + bot protection) + **Cloud CDN custom headers** |
| **Lambda@Edge (origin request/response)** | Dynamic origin selection, SSR at edge | **Cloud Run** at origin behind **Global External HTTPS LB** + **Cloud CDN** — but this is a *cache-miss* path, not edge compute |

**Detection signals — stop and warn the user if you see any of these:**

```javascript
// Lambda@Edge: the `cf` field in the event record is the key signal
exports.handler = async (event) => {
    const request = event.Records[0].cf.request; // ← cf = Lambda@Edge, NOT Cloud Run compatible
};
```

```yaml
# serverless.yml or SAM — trigger type is "cloudfront", not "http" or "api"
events:
  - cloudFront:
      eventType: viewer-request  # ← out of scope for Cloud Run migration
```

**Agent Action:** If you detect `event.Records[0].cf` in code, or `cloudFront:` / `Type: CloudFront` in IaC files, **stop immediately and inform the user** that this workload cannot be directly migrated to Cloud Run. Recommend a Cloud CDN / Cloud Armor / Global LB architecture review instead.