# Exporting AWS Lambda Configuration for Analysis

To perform a complete migration analysis, the agent needs both the **Source Code** and the **Function Metadata**. Use these AWS CLI commands to gather the necessary context.

## 1. Export Function Metadata

This includes the runtime, environment variables, handler, and timeout settings.

```bash
aws lambda get-function --function-name <FUNCTION_NAME> --output json > function_config.json
```

**Example output (`function_config.json`):**
```json
{
  "Configuration": {
    "FunctionName": "my-orders-api",
    "Runtime": "python3.11",
    "Handler": "handler.lambda_handler",
    "MemorySize": 256,
    "Timeout": 30,
    "Environment": {
      "Variables": {
        "ORDERS_TABLE": "orders",
        "SNS_TOPIC_ARN": "arn:aws:sns:us-east-1:123456789012:order-events"
      }
    },
    "Role": "arn:aws:iam::123456789012:role/my-lambda-execution-role",
    "VpcConfig": {
      "SubnetIds": [],
      "SecurityGroupIds": []
    }
  }
}
```

**Key fields to extract for migration:**
- `Runtime` → select matching base Docker image (e.g., `python:3.11-slim`)
- `MemorySize` → set Cloud Run `--memory` limit (e.g., `256Mi`)
- `Timeout` → set Cloud Run `--timeout` (max 3600s; Lambda max is 900s)
- `Environment.Variables` → map directly to Cloud Run env vars
- `Role` → use ARN to fetch the IAM policy in step 3

---

## 2. Export Resource-Based Policy

This identifies who/what can trigger the Lambda (API Gateway, S3, SNS, etc.).

```bash
aws lambda get-policy --function-name <FUNCTION_NAME> --output json > function_policy.json
```

**Example output (`function_policy.json`):**
```json
{
  "Policy": "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"AllowAPIGatewayInvoke\",\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"apigateway.amazonaws.com\"},\"Action\":\"lambda:InvokeFunction\",\"Resource\":\"arn:aws:lambda:us-east-1:123456789012:function:my-orders-api\"}]}"
}
```

**What to look for:**
- `Principal.Service: apigateway.amazonaws.com` → migrate trigger to Cloud Run's built-in HTTPS URL
- `Principal.Service: s3.amazonaws.com` → migrate trigger to Eventarc (Cloud Storage events)
- `Principal.Service: sns.amazonaws.com` → migrate trigger to Pub/Sub push subscription

---

## 3. Export IAM Role Policy

This identifies what AWS services the Lambda is allowed to access — the key input for mapping to GCP IAM Service Account roles.

```bash
# Step 1: Get the Role Name from function_config.json → Configuration.Role (last segment)
ROLE_NAME="my-lambda-execution-role"

# Step 2: List attached managed policies
aws iam list-attached-role-policies --role-name $ROLE_NAME --output json

# Step 3: Get inline policies (if any)
aws iam list-role-policies --role-name $ROLE_NAME --output json
aws iam get-role-policy --role-name $ROLE_NAME --policy-name <POLICY_NAME> > iam_policy.json
```

**Example IAM policy → GCP role mapping:**

| AWS Action in policy | GCP IAM role equivalent |
|---|---|
| `dynamodb:GetItem`, `dynamodb:PutItem` | `roles/datastore.user` (Firestore) |
| `s3:GetObject`, `s3:PutObject` | `roles/storage.objectUser` |
| `sns:Publish` | `roles/pubsub.publisher` |
| `sqs:SendMessage`, `sqs:ReceiveMessage` | `roles/cloudtasks.enqueuer` |
| `secretsmanager:GetSecretValue` | `roles/secretmanager.secretAccessor` |
| `ses:SendEmail` | *(no native GCP equiv — use SendGrid or Mailjet via Cloud Run env vars)* |

---

## 4. Export VPC Configuration

If the Lambda is inside a VPC, it likely accesses private resources (RDS, ElastiCache, internal APIs). This drives the Cloud Run VPC egress decision.

```bash
aws lambda get-function-configuration --function-name <FUNCTION_NAME> \
  --query 'VpcConfig' --output json > vpc_config.json
```

**Example output:**
```json
{
  "SubnetIds": ["subnet-0abc123", "subnet-0def456"],
  "SecurityGroupIds": ["sg-0aaa111"],
  "VpcId": "vpc-0xyz789"
}
```

**Migration decision:**
- `SubnetIds` populated → Lambda accesses private resources → Enable **Direct VPC Egress** on Cloud Run (`--vpc-egress=all-traffic`) and attach to the equivalent GCP VPC subnet.
- `SubnetIds` empty → Lambda is public → No VPC configuration needed on Cloud Run.

---

## 5. Export Tags

Tags often contain environment, team, or cost-center metadata useful for labelling Cloud Run services.

```bash
aws lambda list-tags --resource <FUNCTION_ARN> --output json > tags.json
```

**Example output:**
```json
{
  "Tags": {
    "env": "production",
    "team": "platform",
    "cost-center": "engineering"
  }
}
```

Map these directly to Cloud Run labels: `gcloud run services update my-service --update-labels env=production,team=platform`.

---

## Summary Checklist for Analysis

Provide these files to the migration agent:

| File | Purpose |
|---|---|
| `function_config.json` | Runtime, Env Vars, Memory, Timeout |
| `function_policy.json` | Triggers (what invokes the Lambda) |
| `iam_policy.json` | Permissions (what the Lambda can access) |
| `vpc_config.json` | Networking (private resource access) |
| `tags.json` | Metadata / labels |
| Source code + `template.yaml` / `serverless.yml` | Handler logic + IaC |
