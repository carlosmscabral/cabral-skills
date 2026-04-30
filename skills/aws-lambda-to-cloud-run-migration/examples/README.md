# AWS Lambda to Google Cloud Run – Example Directory

This directory contains five representative Lambda projects used for testing the skill's analysis and migration workflow.

---

| # | Example | Language | IaC | AWS Lock-ins | Migration Class |
|---|---------|----------|-----|-------------|-----------------|
| 01 | `01-python-boto3-api-gateway` | Python 3.11 | AWS SAM (`template.yaml`) | boto3 (DynamoDB, SNS), raw HTTP + Basic Auth | Medium |
| 02 | `02-nodejs-s3-sqs-api-gateway` | Node.js 18 | *(none)* | @aws-sdk v3 (S3, SQS) | Low-Medium |
| 03 | `03-python-serverless-sns-cron` | Python 3.11 | Serverless Framework (`serverless.yml`) | boto3 (S3, SES), SNS trigger, EventBridge cron | Medium-High |
| 04 | `04-typescript-cdk` | TypeScript | AWS CDK (`OrderApiStack.ts`) | Lambda, API Gateway, DynamoDB, SNS, SQS via CDK constructs | High |
| 05 | `05-php-bref-api-gateway` | PHP 8.2 | Serverless Framework (`serverless.yml`) | aws-sdk-php (S3, SNS), Bref framework, Guzzle raw HTTP | Medium-High |
| 06 | `06-dotnet-api-gateway` | C# / .NET 8 | `aws-lambda-tools-defaults.json` | AWSSDK.DynamoDBv2, AWSSDK.SNS, Amazon.Lambda.Core, APIGatewayEvents | Medium |

---

## How to use with `analyze_lambda.py`

Run the analysis script from the skill root, targeting any example directory:

```bash
# Install optional dependency for accurate IaC parsing
pip install -r scripts/requirements.txt

# Analyze example 1 — output manifest to /tmp to avoid polluting source
python3 scripts/analyze_lambda.py examples/01-python-boto3-api-gateway --output /tmp

# Review findings
cat /tmp/migration_manifest.json
```

The script will produce a `migration_manifest.json` with sections for `code_analysis` and `iac_analysis`.
Pass that file to the Gemini CLI agent (or read it yourself) to begin the migration workflow described in `SKILL.md`.

---

## Migration complexity cheat sheet

- **Example 01** → Migrate to **Cloud Run Service** (API Gateway → built-in HTTPS URL). Replace DynamoDB with Firestore or Cloud SQL. Replace SNS with Pub/Sub.
- **Example 02** → Migrate to **Cloud Run Service**. Replace S3 with Cloud Storage. Replace SQS with Cloud Tasks.
- **Example 03 `process_notification`** → Migrate to **Cloud Run Service** + Pub/Sub Push Subscription (replaces SNS trigger). Replace SES with SendGrid via Cloud Tasks or Cloud Run.
- **Example 03 `daily_report`** → Migrate to a **Cloud Run Job** + Cloud Scheduler HTTP trigger (replaces EventBridge cron). Replace S3 with Cloud Storage.
- **Example 04** → **High-complexity CDK migration**. Convert `OrderApiStack.ts` to Terraform (`google` provider) or CDKTF. Each CDK construct maps to a GCP Terraform resource: Lambda→`google_cloud_run_v2_service`, APIGateway→built-in URL, DynamoDB→`google_firestore_document`, SNS→`google_pubsub_topic`, SQS→`google_cloud_tasks_queue`.
- **Example 05** → Migrate to **Cloud Run Service**. Wrap the Bref handler in Laravel/Slim or use FrankenPHP/RoadRunner. Replace `aws-sdk-php` calls with `google/cloud-*` SDKs (Cloud Storage, Pub/Sub). Refactor Guzzle call to use Workload Identity.
- **Example 06** → Migrate to **Cloud Run Service** running ASP.NET Core Minimal API. Remove all `Amazon.Lambda.*` + `AWSSDK.*` NuGet packages. Replace `AmazonDynamoDBClient` with `Google.Cloud.Firestore`, replace `AmazonSimpleNotificationServiceClient` with `Google.Cloud.PubSub.V1`. Use a multi-stage Dockerfile (`mcr.microsoft.com/dotnet/sdk:8.0` build → `aspnet:8.0` runtime). Set `ENV ASPNETCORE_HTTP_PORTS=${PORT:-8080}` to respect Cloud Run's injected port.
