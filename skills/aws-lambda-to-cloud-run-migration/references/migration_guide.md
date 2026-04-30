# Technical Migration Guide: AWS Lambda to Google Cloud Run

This reference provides deep-dive mapping for common AWS services and patterns.

## 1. Authentication & IAM

### AWS IAM Roles vs. GCP Service Accounts
- **AWS Lambda:** Uses an **IAM Execution Role** attached to the function. Permissions are defined in JSON policies.
- **Google Cloud Run:** Uses a **Service Account** (custom or default compute). 
- **Migration Path:**
    1.  Create a GCP Service Account.
    2.  Grant it predefined IAM roles (e.g., `roles/pubsub.publisher`, `roles/storage.objectViewer`).
    3.  Assign the service account to the Cloud Run service during deployment.

### Workload Identity Federation (WIF)
If the Cloud Run service still needs to call AWS APIs during the migration phase, use **Workload Identity Federation** to allow GCP identities to assume AWS IAM Roles securely without long-lived keys.

## 2. Messaging & Async Patterns

### SNS (Simple Notification Service)
- **Mapping:** Use **Google Cloud Pub/Sub**.
- **Triggering:** Cloud Run can be triggered by a Pub/Sub **Push Subscription**. The message is delivered as an HTTP POST request to the service URL.
- **Format:** AWS SNS messages have a specific JSON structure; GCP Pub/Sub also uses JSON but the schema differs (`message.data` is base64 encoded).

### SQS (Simple Queue Service)
- **Mapping:** Use **Google Cloud Tasks** (for task-oriented queues with rate limiting/retries) or **Pub/Sub** (for event-driven streams).
- **Behavior:** SQS requires "polling" (or Event Source Mapping in Lambda). Cloud Run prefers "push" via Cloud Tasks or Pub/Sub.

## 3. Networking & Access Control

### Public vs. Private Access
- **AWS Lambda:** 
  - **Public:** No VPC configuration; triggered by public API Gateway.
  - **Private:** Configured with VPC Subnets/Security Groups to reach private RDS, ElastiCache, or internal APIs.
- **Google Cloud Run:**
  - **Public:** Default. Controlled by IAM (`roles/run.invoker`).
  - **Private (Ingress):** Restrict to "Internal" or "Internal and Cloud Load Balancing" for private-only access.
  - **Private (Egress):** Use **Serverless VPC Access** (VPC Connector) or **Direct VPC Egress** to access private Cloud SQL, Memorystore, or other internal services in your VPC.

## 4. Environment Variables & Secrets

### Environment Variables
- **AWS:** Stored directly in function configuration.
- **GCP:** Stored directly in Cloud Run service configuration.
- **Migration Strategy:** 
  - Scan `function_config.json` for key-value pairs. 
  - Avoid hardcoding in Dockerfiles; use `--set-env-vars` during `gcloud run deploy`.

### Secrets (AWS vs GCP)
| Feature | AWS Service | Google Cloud Service |
| :--- | :--- | :--- |
| **Secrets Management** | **AWS Secrets Manager** | **Secret Manager** |
| **Simple KV Store** | **AWS Systems Manager (SSM) Parameter Store** | **Secret Manager / Config Maps** |
| **Usage Pattern** | `ssm.get_parameter()` or `secretsmanager.get_secret_value()` | **Mount as volume (preferred)** or as environment variable. |

**Best Practice:** On Cloud Run, mount secrets as files (e.g., `/secrets/app_config`). This is more secure than environment variables because they aren't exposed in standard environment lists (`ps`, `env`).

## 5. Trigger Mapping

| AWS Event Source | GCP Equivalent | Trigger Type |
| :--- | :--- | :--- |
| **API Gateway** | **Built-in HTTPS URL** | Direct HTTP(S) |
| **ALB (Application Load Balancer)** | **Global HTTPS Load Balancer** | Serverless NEGs |
| **S3 Events** | **Cloud Storage (Eventarc)** | Push (POST) |
| **DynamoDB Streams** | **Firestore / Pub/Sub** | Needs intermediary (Pub/Sub) |
| **Scheduled (EventBridge)** | **Cloud Scheduler** | HTTP(S) Cron |

## 5. Cold Starts & Resource Management

### Cold Start Mitigation
- **Min Instances:** Configure `min-instances` to keep containers warm (equivalent to Provisioned Concurrency).
- **Startup CPU Boost:** Enable `startup-cpu-boost` for faster container spin-up.
- **Concurrency:** Cloud Run instances can handle multiple requests (unlike Lambda), which significantly reduces the *impact* of cold starts on overall latency.

## 6. Deployment & Traffic Shifting (Canary)

AWS Lambda relies on Versions and Aliases for traffic shifting. Cloud Run has this built-in via **Traffic Splitting**, which is highly recommended during migrations.

- **Initial Deployment:** Deploy the migrated Cloud Run service with `--no-traffic`. It creates a new Revision but leaves 100% of traffic on the old version (if one exists).
- **Canary Rollout:** Gradually shift traffic to the new revision.
  ```bash
  gcloud run services update-traffic my-service --to-revisions=my-service-v2=10
  ```
- **Terraform:** Traffic splitting is native to the `google_cloud_run_v2_service` resource:
  ```terraform
  traffic {
    percent  = 10
    revision = "my-service-v2"
    type     = "TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION"
  }
  traffic {
    percent  = 90
    revision = "my-service-v1"
    type     = "TRAFFIC_TARGET_ALLOCATION_TYPE_REVISION"
  }
  ```

## 7. Refactoring Raw API Calls to GCP SDKs

If the Lambda code uses raw HTTP clients (`requests`, `axios`, `guzzle`) with hardcoded `clientID` and `Secrets` to call AWS services:

- **Security Risk:** Hardcoded credentials (even in environment variables) are a security risk. 
- **GCP Best Practice:** Move to **GCP Client Libraries**. 
- **Rationale:** GCP SDKs automatically handle token exchange using the **IAM Service Account** attached to the Cloud Run instance. This eliminates the need for managing secrets for internal GCP service communication.

**Example Migrations (Moving away from hardcoded secrets to Workload Identity):**

*Python:*
- **AWS (Raw HTTP):** `requests.post(url, auth=(client_id, client_secret), json=data)`
- **GCP (SDK):** `from google.cloud import pubsub_v1; publisher = pubsub_v1.PublisherClient(); publisher.publish(topic_path, data)`

*Node.js:*
- **AWS (Raw HTTP):** `axios.post(url, data, { auth: { username: client_id, password: client_secret } })`
- **GCP (SDK):** `const {PubSub} = require('@google-cloud/pubsub'); const pubsub = new PubSub(); pubsub.topic(topicName).publishMessage({data: Buffer.from(JSON.stringify(data))});`

*PHP:*
- **AWS (Raw HTTP with Guzzle):** `$client = new \GuzzleHttp\Client(); $client->post($url, ['auth' => [$clientId, $clientSecret], 'json' => $data]);`
- **GCP (SDK):** `use Google\Cloud\PubSub\PubSubClient; $pubsub = new PubSubClient(); $topic = $pubsub->topic($topicName); $topic->publish(['data' => $data]);`

*Java:*
- **AWS (Raw HTTP):** `HttpClient.newHttpClient().send(requestWithBasicAuth, HttpResponse.BodyHandlers.ofString());`
- **GCP (SDK):** `Publisher publisher = Publisher.newBuilder(topicName).build(); publisher.publish(PubsubMessage.newBuilder().setData(ByteString.copyFromUtf8(data)).build());`

*Go:*
- **AWS (Raw HTTP):** `req.SetBasicAuth(clientID, clientSecret); http.DefaultClient.Do(req)`
- **GCP (SDK):** `client, err := pubsub.NewClient(ctx, projectID); t := client.Topic(topicID); t.Publish(ctx, &pubsub.Message{Data: []byte(data)})`
