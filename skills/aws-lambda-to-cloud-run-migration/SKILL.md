---
name: aws-lambda-to-cloud-run-migration
description: Migrates AWS Lambda functions to Google Cloud Run. Analyzes AWS lock-ins (SNS, SQS, SDKs, IAM, Cold Starts), build/trigger mechanisms (API Gateway vs direct), and service integrations to provide a detailed migration report, containerization tips, and GCP service mapping.
---

# AWS Lambda to Google Cloud Run Migration Skill

This skill assists in the assessment, analysis, and migration of AWS Lambda functions to Google Cloud Run, following the [official Google Cloud migration framework](https://docs.cloud.google.com/architecture/migrate-aws-lambda-to-cloudrun).

## Available Resources

Before starting or when you need specific details, load the following resources into context:

- **`scripts/analyze_lambda.py`**: ALWAYS run this script first on the target directory (e.g., `python scripts/analyze_lambda.py <target_dir>`). Use the optional `--output <dir>` flag to control where `migration_manifest.json` is written (defaults to the current working directory, **not** the source tree). Use `--summary` for a human-readable terminal overview. It uses AST parsing, IaC traversal, `composer.json`, `package.json`, and `requirements.txt` scanning to automatically discover AWS SDK lock-ins, connection pools, and triggers, generating a `migration_manifest.json` file. **You MUST read this JSON file immediately after running the script** to understand the application's AWS footprint.
- **`references/migration_guide.md`**: Read this for the end-to-end migration strategy and detailed step-by-step methodology.
- **`references/advanced_mapping.md`**: Read this when you encounter complex AWS services (beyond basic SNS/SQS) that need to be mapped to GCP equivalents.
- **`references/containerization.md`**: Read this for boilerplate Dockerfiles and Cloud Run constraints (e.g., port handling) across Node.js, Python, PHP, Java, and Go.
- **`references/iac_translation.md`**: Read this for migrating AWS SAM, Serverless Framework, AWS CDK, or **raw AWS Terraform (`.tf`)** files to GCP. Covers **two output paths**: Path A (Terraform `google` provider) for production-grade IaC, and Path B (Cloud Build + `gcloud run deploy`) for scripted/CI-CD migrations.
- **`references/export_guide.md`**: Read this for strategies on exporting current AWS configurations (like CloudFormation or SAM templates) for analysis.

## Recommended External Tools

If the user's environment has the following MCP servers installed, **you MUST use them** to gather up-to-date information during the migration:
- **AWS Documentation Tools (`mcp_aws-docs_*`)**: Use `search_documentation` and `read_documentation` to look up precise behaviors of AWS Lambda features, API Gateway event payloads, or AWS SDK constraints.
- **Google Developer Knowledge Tools (`mcp_developer-knowledge_*`)**: Use `search_documents` and `get_documents` to find the latest official guides, API references, and best practices for Cloud Run, Eventarc, Pub/Sub, and GCP IAM.

## 1. Migration Framework

### Phase 1: Assess & Discover
- **Inventory:** Catalog all Lambda functions, triggers, and dependencies.
- **Complexity Assessment:**
    - **Low Complexity:** Stateless, simple HTTP trigger, minimal AWS SDK usage.
    - **Medium Complexity:** Uses S3/SNS/SQS, VPC access, or Lambda Layers.
    - **High Complexity:** Part of a Step Function, custom Runtimes, or heavy AWS-specific orchestration.

### Phase 2: Plan & Foundation
- **Resource Hierarchy:** Define GCP Projects and Folders.
- **IAM Strategy:** Map AWS IAM Roles to GCP Service Accounts.
- **Networking:** Plan VPC Connectors or Direct VPC Egress for internal access.

### Phase 3: Migrate & Refactor
- **Containerization:** Convert code to OCI-compliant images. *→ **ACTION:** Load `references/containerization.md` to select the right Buildpack or Dockerfile strategy for your target language (including FrankenPHP/RoadRunner for PHP).*
- **Service Mapping:** Replace AWS services with GCP equivalents. *→ **ACTION:** If dealing with API Gateway, SNS, SQS, or direct invokes, load `references/advanced_mapping.md` for proper translation architectures.*
- **Infrastructure as Code (IaC):** Convert AWS deployment templates to Terraform or a scripted `gcloud` + Cloud Build pipeline. *→ **ACTION:** Load `references/iac_translation.md` if the user provides `template.yaml`, `serverless.yml`, CDK code, or **AWS Terraform (`.tf`) files**. The guide offers two GCP deployment paths: **Path A (Terraform)** for production repeatability, and **Path B (Scripted — Cloud Build + `gcloud run deploy`)** for fast migrations. Ask the user which they prefer before generating output.*
- **Data Migration:** Plan migration for RDS/DynamoDB if necessary.

### Phase 4: Optimize
- **Scaling:** Configure Min/Max instances and Concurrency.
- **Performance:** Enable Startup CPU Boost for cold start mitigation.

## 2. Analysis Workflow

When provided with Lambda code or configuration (e.g., SAM, CloudFormation, Serverless Framework, AWS CDK, or AWS Terraform), follow these steps:

### #1 - Lock-in Analysis
- **Identify SDK Usage:** Look for `boto3` (Python), `aws-sdk` (Node.js/Go/Java), or `aws/aws-sdk-php` (PHP). Highlight specific service calls. Check `composer_analysis` in the output manifest for Laravel, Symfony, or Slim markers.
- **Messaging Services:** Identify dependencies on **SNS** (Simple Notification Service) or **SQS** (Simple Queue Service).
- **Raw API Calls vs. SDKs:** Identify usage of `requests`, `axios`, `guzzle`, or `curl` to call AWS services directly. Highlight hardcoded **Client IDs**, **Client Secrets**, or **API Keys**.
- **Auth Strategy:** Note if the code manually signs requests (SigV4) or uses basic auth. In GCP, we prioritize using **GCP Client Libraries** which handle authentication transparently via the attached Service Account. *→ **ACTION:** Load `references/migration_guide.md` if you find hardcoded secrets or raw HTTP calls that need refactoring to Workload Identity.*
- **Triggers:** Determine if it's an HTTP-based trigger (API Gateway, ALB) or event-driven (S3, DynamoDB Streams). For PHP, check if **Bref** (`php-82-fpm` or `php-82`) is used in `serverless.yml`.
- **Cold Start Considerations:** Note memory settings and runtime version, as these impact cold start profiles.

### #2 - Build and Trigger Analysis
- **Execution Paradigm (CRITICAL):** You must determine if this code should be a **Service** or a **Job**.
    - If the Lambda is triggered by API Gateway, Webhooks, or real-time events (Pub/Sub) → **Cloud Run Service**. It must listen on `$PORT`.
    - If the Lambda is a cron job (EventBridge scheduled), a data processing script, or an asynchronous batch task → **Cloud Run Job**. It does *not* need a web server; it should just execute as a script and exit.
- **Port Handling (For Services):** AWS Lambda doesn't listen on a port. A Cloud Run Service **MUST** listen on the port defined by the `PORT` environment variable (default 8080).

### #3 - Integration & Auth Analysis
- **IAM Strategy:** Map AWS IAM Execution Roles to GCP **IAM Service Accounts**.
- **Networking:** Identify if the Lambda is in a VPC (for RDS, internal ELBs) and recommend **Serverless VPC Access** or **Direct VPC egress** on GCP.
- **Database Access:** Check for DynamoDB (map to Firestore/Spanner) or RDS (map to Cloud SQL).

## 3. Migration Paths

### Service Mapping Table
| AWS Service | Google Cloud Equivalent | Migration Strategy |
| :--- | :--- | :--- |
| **API Gateway / ALB** | **Cloud Run built-in URL / GCLB** | Use built-in HTTPS URL; add Global LB for WAF or multi-region. |
| **SNS** | **Pub/Sub (Topics)** | Push subscriptions trigger Cloud Run URLs directly. |
| **SQS** | **Cloud Tasks / Pub/Sub** | Use Cloud Tasks for rate-limiting/queuing; Pub/Sub for async events. |
| **EventBridge / Cron** | **Eventarc / Cloud Scheduler** | Use Cloud Scheduler for cron; Eventarc for cross-service events. |
| **IAM Role** | **IAM Service Account** | Attach the service account to the Cloud Run service. |
| **DynamoDB** | **Firestore / Spanner / Cloud SQL** | Firestore for document-model; Spanner for relational scale; Cloud SQL for RDS migrations. |
| **S3** | **Cloud Storage** | Direct equivalent; use FUSE mount for file-system access patterns. |
| **Lambda Layers** | **Multi-stage Docker builds** | Shared libraries become Docker `COPY --from` base image layers. |
| **Step Functions** | **Cloud Workflows** | Convert ASL (Amazon States Language) to YAML Workflows; orchestrates HTTP calls to Cloud Run. |
| **Secrets Manager / SSM** | **Secret Manager** | Mount as volume (preferred) or env var in Cloud Run. |
| **SES (Email)** | **SendGrid / Mailchimp (3rd party)** | No native GCP email service; use a transactional email provider via Cloud Run env vars. |

### Containerization
All migrated code must be containerized. Cloud Run requires an OCI-compliant image.
- **Language Frameworks:** Convert raw Lambda handlers into web servers (e.g., Flask, Express, FastAPI, Go `net/http`).
- **Entry point:** Ensure the application listens on `0.0.0.0:$PORT`.

## 4. Interactive Guidance

If information is missing, use these prompts to guide the user:
- "Could you provide the `template.yaml` (SAM), `serverless.yml`, CDK stack, or Terraform `.tf` files to analyze the triggers and IAM roles?" *(→ **ACTION:** If the user doesn't know how to get these, load `references/export_guide.md` to help them export their AWS config).*
- "Does this Lambda require access to internal VPC resources like RDS or a private API?"
- "Is the traffic pattern predictable (allowing for Min Instances) or highly bursty (requiring Cold Start optimization)?"
- "For the GCP deployment: would you prefer **Path A — Terraform** (production-grade IaC, repeatable, state-managed) or **Path B — Scripted** (`gcloud run deploy` + Cloud Build, faster to get started)? *→ **ACTION:** Load `references/iac_translation.md` and present both options with trade-offs before generating any output templates.*"
## 5. Final Deliverable Structure

Your final report should include:
1. **Status Quo Analysis:** Detailed breakdown of current AWS dependencies.
2. **Lock-in Highlights:** Code snippets from the source that are "AWS-specific" and need refactoring.
3. **Target Architecture:** A proposed GCP diagram/description.
4. **Migration Steps:** Sequential steps for containerization, IAM setup, and service mapping.
5. **Code Snippets:** "Before" (AWS SDK) vs "After" (GCP Client Library) examples.
