# E-Commerce Monorepo Example

This example represents a realistic, common customer scenario: an e-commerce order processing backend built with 5 AWS Lambda functions deployed from a single monorepo using AWS SAM.

## Architecture

```
ecommerce-monorepo/
├── template.yaml                          # SAM IaC — defines all 5 functions
└── functions/
    ├── create_order/handler.py            # POST /orders (API Gateway)
    ├── get_order_status/handler.py        # GET /orders/{id} (API Gateway)
    ├── process_payment/handler.py         # SNS subscriber — calls payment API
    ├── send_notification/handler.py       # SNS subscriber — sends SES email
    └── nightly_reconcile/handler.py       # EventBridge cron — writes S3 report
```

## Lambda Inventory

| Function | Trigger | Runtime | Memory | Timeout | AWS Services Used |
|---|---|---|---|---|---|
| `CreateOrder` | API Gateway (POST /orders) | Python 3.12 | 256 MB | 30s | DynamoDB, SNS |
| `GetOrderStatus` | API Gateway (GET /orders/{id}) | Python 3.12 | 256 MB | 30s | DynamoDB |
| `ProcessPayment` | SNS `order-events` | Python 3.12 | 512 MB | 60s | DynamoDB, external HTTP API |
| `SendNotification` | SNS `order-events` | Python 3.12 | 256 MB | 30s | SES |
| `NightlyReconcile` | EventBridge cron (02:00 UTC) | Python 3.12 | 1024 MB | 900s | DynamoDB, S3 |

## What This Example Demonstrates

### Mixed Trigger Types
- **HTTP triggers** (`CreateOrder`, `GetOrderStatus`) → Cloud Run **Service**
- **Event-driven triggers** (`ProcessPayment`, `SendNotification`) → Cloud Run **Service** with Pub/Sub push
- **Cron trigger** (`NightlyReconcile`) → Cloud Run **Job**

### Dependency Relationships
- `CreateOrder` publishes to the shared `order-events` SNS topic
- `ProcessPayment` and `SendNotification` both subscribe to `order-events`
- `NightlyReconcile` is an independent leaf node (no inbound dependencies)

This creates a **natural grouping signal**: `CreateOrder` and `GetOrderStatus` share a domain (orders CRUD) and are strong candidates for **Domain Consolidation** into a single `svc-orders` Cloud Run service.

### Common AWS Lock-ins to Refactor
- `boto3` → `google-cloud-*` SDK dependencies
- `dynamodb.put_item / get_item` → Firestore or Cloud SQL
- `sns.publish` → `google-cloud-pubsub` publisher
- `ses.send_email` → SendGrid or Mailgun (no native GCP email service)
- Raw `requests.post` with hardcoded API key → Secret Manager mount in Cloud Run

## Running the Fleet Analyzer

From the skill root:
```bash
python3 scripts/analyze_fleet.py examples/ecommerce-monorepo --output /tmp --summary
```

Expected output:
- 5 functions discovered via SAM `template.yaml`
- Runtimes: `python3.12 (5)`
- Trigger types: `Api (2)`, `SNS (2)`, `Schedule (1)`
- Dependency edges from source scanning (SNS publish patterns)

## Suggested Migration Plan

Based on `references/fleet_strategy.md` analysis:

| Wave | Function(s) | Target | Pattern | Rationale |
|---|---|---|---|---|
| 1 | `ProcessPayment` | `svc-payments` | 1:1 Service | Different security boundary (PCI); SNS consumer migrates first |
| 1 | `SendNotification` | `svc-notifications` | 1:1 Service | Independent; leaf node for SNS edges |
| 1 | `NightlyReconcile` | `job-reconcile` | 1:1 Job | Cron → Cloud Run Job; completely independent |
| 2 | `CreateOrder`, `GetOrderStatus` | `svc-orders` | Domain Consolidation | Same team, same DynamoDB table, HTTP triggers, shared domain |
