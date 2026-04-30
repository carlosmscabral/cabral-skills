# Fleet Grouping Strategy: N Lambdas → M Cloud Run Services

This reference helps you decide how many Cloud Run services should replace N Lambda functions. The core trade-off is **operational simplicity** (fewer services) vs. **autonomy and isolation** (more services).

---

## The Three Grouping Patterns

### Pattern A: 1:1 Migration

Each Lambda becomes its own Cloud Run service (or Job). The function boundary is preserved.

**Characteristics:**
- Minimal refactoring — the handler runs in its own container unchanged.
- Independent scaling, independent IAM service accounts, independent deploy cycles.
- Straightforward rollback per function.

**Use when:**
- Functions are owned by different teams.
- Functions have meaningfully different traffic profiles (one is bursty, one is constant).
- Functions use different runtimes or languages.
- Functions have different security boundaries (different data sensitivity, different VPC requirements).
- Functions are already stateless and independent.

**Cloud Run mapping:**
- API Gateway trigger → Cloud Run Service with built-in HTTPS URL.
- EventBridge cron trigger → Cloud Run Job.
- SNS/SQS consumer → Cloud Run Service with Pub/Sub push subscription.

---

### Pattern B: Domain Consolidation

A group of closely related Lambdas (e.g., CRUD operations for the same entity) are merged into a single Cloud Run service with internal routing.

**Characteristics:**
- Reduces cold starts across the group (one container = one warm pool).
- Shared initialization for DB connections, SDK clients — major efficiency gain.
- Single IAM service account for the domain.
- Single deploy unit — simpler CI/CD pipeline.

**Use when:**
- Functions share the same database table, SNS topic, or SQS queue (high cohesion).
- Functions use the same runtime and language.
- Functions are latency-sensitive in calling each other (direct Lambda invocations between them).
- Single team owns all the functions in the group.
- Functions have similar traffic patterns.

**Cloud Run mapping:**
- Route each former Lambda handler to a distinct HTTP path or Pub/Sub topic within the single service.
- See `references/consolidation_patterns.md` for implementation mechanics.

---

### Pattern C: Sidecar / Shared API Platform

Multiple logical domains are placed behind a single API Gateway surface (Cloud Endpoints or Apigee) with path-based routing to separate Cloud Run services per domain.

**Characteristics:**
- Preserves a stable public API surface (same domain, same paths, no client-side changes).
- Each Cloud Run service is still a separate unit with its own scaling/IAM.
- Requires Apigee or Cloud Endpoints as the front-door (additional operational overhead).

**Use when:**
- The existing AWS API Gateway has dozens of paths across many Lambdas.
- Clients (mobile apps, third-party partners) cannot tolerate URL changes.
- The team wants to migrate backend services independently while keeping the public API stable.

---

## Decision Matrix

Score each dimension for your Lambda group. Higher = stronger signal for that pattern.

| Dimension | A: 1:1 | B: Domain Consolidation | C: Sidecar/Platform |
|---|---|---|---|
| **Multiple team owners** | ✅ Strong | ❌ Weak | ⚠️ Neutral |
| **Same runtime / language** | ⚠️ Neutral | ✅ Strong | ⚠️ Neutral |
| **Independent scaling needs** | ✅ Strong | ❌ Weak | ⚠️ Neutral |
| **Shared database / queue** | ❌ Weak | ✅ Strong | ⚠️ Neutral |
| **Direct Lambda→Lambda invocations** | ❌ Weak | ✅ Strong | ⚠️ Neutral |
| **Stable public API surface required** | ❌ Weak | ❌ Weak | ✅ Strong |
| **Latency-sensitive internal calls** | ❌ Weak | ✅ Strong (in-process) | ⚠️ Neutral |
| **Different security boundaries** | ✅ Strong | ❌ Weak | ⚠️ Neutral |

**Usage:** Tally strong signals per pattern for your target group. The pattern with the most strong signals is the recommended default. Use the rationale to explain the choice in the Migration Program Document.

---

## Complexity Classification

Use this to assign a complexity rating to each function in the Fleet Inventory Table:

| Rating | Criteria |
|---|---|
| **Low** | HTTP trigger only, no AWS SDK calls, no VPC, runtime is Python/Node.js |
| **Medium** | Uses S3/SNS/SQS, or is in a VPC, or uses Lambda Layers |
| **High** | Part of a Step Function, direct Lambda invocations from/to other functions, custom runtime, or heavy DynamoDB/RDS usage |

---

## Cloud Run Naming Conventions

When deriving Cloud Run service names from Lambda function names:

1. **Strip environment suffixes**: `orders-handler-prod` → `orders-handler`
2. **Strip app prefix if it's the same for all functions**: `myapp-orders-handler` + `myapp-users-handler` → `svc-orders` + `svc-users`
3. **For consolidated groups**: use the domain noun, not a function name: `svc-orders` (not `svc-create-order`)
4. **For Cloud Run Jobs**: prefix with `job-`: `job-nightly-reconcile`
5. **Max 49 characters**, lowercase, hyphens only (Cloud Run naming constraint).

---

## Worked Example: E-Commerce Estate

Given 5 Lambdas:

| Lambda | Trigger | Dependencies | Team |
|---|---|---|---|
| `CreateOrder` | API Gateway | Publishes to SNS `order-events`; writes DynamoDB | Orders team |
| `GetOrderStatus` | API Gateway | Reads DynamoDB | Orders team |
| `ProcessPayment` | SNS `order-events` | Calls external payment API | Payments team |
| `SendNotification` | SNS `order-events` | Calls SES | Notifications team |
| `NightlyReconcile` | EventBridge (cron) | Reads DynamoDB; writes S3 | Data team |

**Recommended grouping:**

| Cloud Run Service | Replaces | Pattern | Rationale |
|---|---|---|---|
| `svc-orders` | `CreateOrder`, `GetOrderStatus` | B: Domain Consolidation | Same team, same DB, HTTP triggers, latency-sensitive reads |
| `svc-payments` | `ProcessPayment` | A: 1:1 (Service) | Different team, different security boundary (PCI scope) |
| `svc-notifications` | `SendNotification` | A: 1:1 (Service) | Different team, independent scaling |
| `job-reconcile` | `NightlyReconcile` | A: 1:1 (Job) | Cron trigger → Cloud Run Job; different team |
