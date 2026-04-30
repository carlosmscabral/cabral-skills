# Infrastructure as Code (IaC) Translation Guide

Migrating the application code is only half the battle. Serverless applications on AWS rely heavily on IaC frameworks. This guide covers:

- **Inputs (AWS side):** SAM, Serverless Framework, CDK, and Terraform
- **Outputs (GCP side):** Two deployment strategies for each input

---

## Choosing a GCP Deployment Strategy

Before translating any AWS IaC, help the user choose **which GCP deployment path** to target.

| | Path A — Terraform (`google` provider) | Path B — Scripted (Cloud Build + `gcloud`) |
| :--- | :--- | :--- |
| **Best for** | Teams already using Terraform for GCP; production repeatability | Quick migrations; `gcloud`-native teams; CI/CD-first shops |
| **Build** | Cloud Build or GitHub Actions → Artifact Registry | `gcloud builds submit` → Artifact Registry |
| **Deploy** | `terraform apply` | `gcloud run deploy` |
| **State management** | GCS backend (`backend "gcs"`) | None — live service is source of truth |
| **Rollback** | `terraform plan/destroy` | `gcloud run services update-traffic` |
| **Learning curve** | Higher (Terraform HCL) | Lower (shell scripts + `gcloud` flags) |

> **Agent Action:** Ask the user which path they prefer before generating any output IaC. Default to **Path A (Terraform)** for production workloads and **Path B (Scripted)** for fast proofs-of-concept.

---

## 1. AWS SAM to GCP

AWS SAM uses a YAML template extension of CloudFormation.

**BEFORE: AWS SAM (`template.yaml`)**
```yaml
Resources:
  MyFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: src/
      Handler: app.handler
      Runtime: nodejs18.x
      Events:
        ApiEvent:
          Type: Api
          Properties:
            Path: /api
            Method: get
```

### Path A — Terraform

*Note: In GCP, building the container and deploying infrastructure are explicitly decoupled.*

```terraform
# main.tf
resource "google_cloud_run_v2_service" "my_function" {
  name     = "my-function-service"
  location = "us-central1"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "us-central1-docker.pkg.dev/my-project/my-repo/my-image:latest"
      env {
        name  = "PORT"
        value = "8080"
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.my_function.location
  service  = google_cloud_run_v2_service.my_function.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

### Path B — Scripted (Cloud Build + gcloud)

**Step 1 — Prerequisites (run once)**
```bash
# Enable required APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com

# Create Artifact Registry repository
gcloud artifacts repositories create my-repo \
  --repository-format=docker \
  --location=us-central1
```

**Step 2 — `cloudbuild.yaml`** (add to repo root)
```yaml
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-image:$COMMIT_SHA
      - .
  - name: gcr.io/cloud-builders/docker
    args:
      - push
      - us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-image:$COMMIT_SHA
images:
  - us-central1-docker.pkg.dev/$PROJECT_ID/my-repo/my-image:$COMMIT_SHA
```

**Step 3 — `deploy.sh`**
```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="my-function-service"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/my-repo/my-image:latest"

# Build and push via Cloud Build
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080

echo "✅ Deployed: $(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')"
```

---

## 2. Serverless Framework to GCP

**BEFORE: Serverless Framework (`serverless.yml`)**
```yaml
service: my-service
provider:
  name: aws
  runtime: python3.9
  environment:
    TABLE_NAME: users
functions:
  hello:
    handler: handler.hello
    events:
      - sns: user-signup-topic
```

### Path A — Terraform

An SNS trigger maps to a Pub/Sub topic + Eventarc trigger.

```terraform
resource "google_cloud_run_v2_service" "my_service" {
  name     = "my-service-hello"
  location = "us-central1"
  template {
    containers {
      image = "us-central1-docker.pkg.dev/my-project/my-repo/my-image:latest"
      env {
        name  = "TABLE_NAME"
        value = "users"
      }
    }
  }
}

resource "google_pubsub_topic" "user_signup" {
  name = "user-signup-topic"
}

resource "google_service_account" "eventarc_invoker" {
  account_id   = "eventarc-invoker"
  display_name = "Eventarc Invoker Service Account"
}

resource "google_project_iam_member" "eventarc_invoker_binding" {
  project = "my-project-id"
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.eventarc_invoker.email}"
}

resource "google_eventarc_trigger" "sns_equivalent" {
  name     = "user-signup-trigger"
  location = "us-central1"
  matching_criteria {
    attribute = "type"
    value     = "google.cloud.pubsub.topic.v1.messagePublished"
  }
  transport {
    pubsub { topic = google_pubsub_topic.user_signup.id }
  }
  destination {
    cloud_run_service {
      service = google_cloud_run_v2_service.my_service.name
      region  = google_cloud_run_v2_service.my_service.location
    }
  }
  service_account = google_service_account.eventarc_invoker.email
}
```

### Path B — Scripted (Cloud Build + gcloud)

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="my-service-hello"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/my-repo/my-image:latest"
SA_EMAIL="eventarc-invoker@${PROJECT_ID}.iam.gserviceaccount.com"

# Build and push
gcloud builds submit --config cloudbuild.yaml .

# Create Pub/Sub topic (SNS equivalent)
gcloud pubsub topics create user-signup-topic --project="${PROJECT_ID}" || true

# Create service account for the trigger
gcloud iam service-accounts create eventarc-invoker \
  --display-name="Eventarc Invoker" --project="${PROJECT_ID}" || true
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker"

# Deploy Cloud Run service
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --no-allow-unauthenticated \
  --set-env-vars TABLE_NAME=users

# Create Eventarc trigger (Pub/Sub → Cloud Run)
gcloud eventarc triggers create user-signup-trigger \
  --location="${REGION}" \
  --destination-run-service="${SERVICE_NAME}" \
  --destination-run-region="${REGION}" \
  --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
  --transport-topic=user-signup-topic \
  --service-account="${SA_EMAIL}"

echo "✅ Service deployed and Pub/Sub trigger wired."
```

---

## 3. AWS CDK to GCP

If the user is using AWS CDK (TypeScript/Python), they are accustomed to writing infrastructure as imperative code.

- **Path A:** Convert AWS CDK to standard HCL Terraform (`google` provider) — see templates in section 1 above as the pattern.
- **Path B (CDK preference):** Convert AWS CDK to **CDKTF** (Cloud Development Kit for Terraform) — keeps TypeScript/Python but targets GCP via the Terraform provider. Or use the scripted `gcloud` path.

### Common Mapping Entities

| AWS IaC Concept | GCP Terraform Resource | GCP `gcloud` equivalent |
| :--- | :--- | :--- |
| `AWS::Serverless::Function` / `aws_lambda_function` | `google_cloud_run_v2_service` | `gcloud run deploy` |
| `AWS::IAM::Role` / `aws_iam_role` | `google_service_account` | `gcloud iam service-accounts create` |
| `AWS::IAM::Policy` / `aws_iam_role_policy` | `google_project_iam_member` | `gcloud projects add-iam-policy-binding` |
| `AWS::Serverless::Api` / `aws_api_gateway_rest_api` | *(Built-in Cloud Run URL)* or `google_api_gateway_api` | URL auto-assigned on `gcloud run deploy` |
| `AWS::SNS::Topic` / `aws_sns_topic` | `google_pubsub_topic` | `gcloud pubsub topics create` |
| `AWS::SQS::Queue` / `aws_sqs_queue` | `google_cloud_tasks_queue` | `gcloud tasks queues create` |
| `AWS::DynamoDB::Table` / `aws_dynamodb_table` | `google_firestore_database` / Cloud SQL | `gcloud firestore databases create` |
| `AWS::S3::Bucket` / `aws_s3_bucket` | `google_storage_bucket` | `gcloud storage buckets create` |

---

## 4. AWS Terraform to GCP

Teams using raw Terraform with the `hashicorp/aws` provider can migrate to the `hashicorp/google` provider directly — staying entirely within Terraform.

**BEFORE: AWS Terraform (`main.tf`)**
```hcl
provider "aws" { region = "us-east-1" }

resource "aws_lambda_function" "orders_api" {
  function_name = "orders-api"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "handler.handler"
  runtime       = "nodejs18.x"
  memory_size   = 256
  timeout       = 30
  environment {
    variables = { ORDERS_TABLE = aws_dynamodb_table.orders.name }
  }
}

resource "aws_api_gateway_rest_api" "orders_api_gw" {
  name = "orders-api"
}

resource "aws_dynamodb_table" "orders" {
  name         = "orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"
  attribute {
    name = "order_id"
    type = "S"
  }
}
```

### Path A — Terraform (`google` provider)

```terraform
# main.tf — GCP equivalent
terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
  # Store state in GCS (equivalent to S3 backend)
  backend "gcs" {
    bucket = "my-tf-state-bucket"
    prefix = "orders-api/state"
  }
}

provider "google" {
  project = var.project_id
  region  = "us-central1"
}

# Firestore (DynamoDB equivalent)
resource "google_firestore_database" "orders" {
  name        = "(default)"
  location_id = "us-central1"
  type        = "FIRESTORE_NATIVE"
}

# Service Account (IAM Role equivalent)
resource "google_service_account" "orders_api" {
  account_id   = "orders-api-sa"
  display_name = "Orders API Service Account"
}

resource "google_project_iam_member" "firestore_access" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.orders_api.email}"
}

# Cloud Run Service (Lambda + API Gateway equivalent)
resource "google_cloud_run_v2_service" "orders_api" {
  name     = "orders-api"
  location = "us-central1"
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.orders_api.email
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/my-repo/orders-api:latest"
      env {
        name  = "ORDERS_COLLECTION"
        value = "orders"
      }
      resources {
        limits = {
          memory = "256Mi"
          cpu    = "1"
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.orders_api.location
  service  = google_cloud_run_v2_service.orders_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_url" {
  value = google_cloud_run_v2_service.orders_api.uri
}
```

### Path B — Scripted (Cloud Build + gcloud)

For teams that want to migrate away from Terraform entirely, or just want a fast path first:

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
SERVICE_NAME="orders-api"
IMAGE="us-central1-docker.pkg.dev/${PROJECT_ID}/my-repo/orders-api:latest"
SA_NAME="orders-api-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

# Create service account
gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="Orders API SA" --project="${PROJECT_ID}" || true

# Grant Firestore access (DynamoDB equivalent)
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/datastore.user"

# Build and push image via Cloud Build
gcloud builds submit --config cloudbuild.yaml .

# Deploy to Cloud Run
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --service-account "${SA_EMAIL}" \
  --set-env-vars ORDERS_COLLECTION=orders \
  --memory 256Mi \
  --allow-unauthenticated

echo "✅ URL: $(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')"
```

---

## 5. Key Considerations for the Agent

1. **Decoupled builds:** SAM/Serverless bundle code and infra in one command (`sam deploy`, `sls deploy`). Both GCP paths require explicitly building and pushing a container image **before** deploying.
2. **State management (Path A):** Always configure a `backend "gcs"` block in Terraform to store state in Cloud Storage.
3. **Artifact Registry setup (both paths):** Remind the user to create an Artifact Registry Docker repository if one doesn't exist. A reusable `cloudbuild.yaml` can be shared across all services.
4. **Path recommendation logic:**
   - User already uses `google` Terraform provider → **Path A**
   - User is AWS Terraform-only, migrating everything → **Path A** (smooth transition, same tooling)
   - User wants to move fast / try Cloud Run first → **Path B**
   - User's CI/CD is script-based (Jenkins pipelines, bash) → **Path B**