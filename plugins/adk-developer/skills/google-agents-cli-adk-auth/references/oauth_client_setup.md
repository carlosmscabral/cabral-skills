# OAuth Client Registration & Auth Manager Setup

Before an agent can authorize users against a third-party or GCP service, you must configure the OAuth 2.0 credentials and register the Auth Provider (or Connector) in GCP.

---

## 🔑 1. Create Google OAuth 2.0 Credentials
1. Navigate to the [Google Cloud Console Credentials Page](https://console.cloud.google.com/apis/credentials).
2. Click **Create Credentials** -> **OAuth client ID**.
3. Select Application type: **Web application**.
4. Configure **Authorized Redirect URIs**:
   * You **MUST** add the GCP Auth Broker's callback URI here, **NOT your frontend application's URI**.
   * When using the modern V2 `authProviders` API:
     `https://agentidentitycredentials.googleapis.com/v1alpha/projects/<PROJECT_ID>/locations/<LOCATION>/authProviders/<PROVIDER_NAME>/oauthcallback`
   * When using the legacy V1 `connectors` API (what we used):
     `https://iamconnectorcredentials.googleapis.com/v1/projects/<PROJECT_ID>/locations/<LOCATION>/connectors/<PROVIDER_NAME>/oauthcallback`
   * **Failure to match this perfectly will result in a `400 redirect_uri_mismatch` error.**
5. Save the generated **Client ID** and **Client Secret**.

---

## 🛠️ 2. Provision the Auth Provider via gcloud CLI

Use the `gcloud alpha agent-identity authProviders` command suite to register your client details into the GCP Agent Identity Auth Manager.

```bash
# Define your configuration variables
PROJECT_ID="your-gcp-project-id"
LOCATION="us-central1"
PROVIDER_NAME="gcs-mcp-auth-provider"
CLIENT_ID="your-client-id.apps.googleusercontent.com"
CLIENT_SECRET="your-client-secret"

# Create the Auth Provider
gcloud alpha agent-identity authProviders create $PROVIDER_NAME \
    --project=$PROJECT_ID \
    --location=$LOCATION \
    --client-id=$CLIENT_ID \
    --client-secret=$CLIENT_SECRET \
    --scopes="https://www.googleapis.com/auth/devstorage.read_write"
```

> [!IMPORTANT]
> **Enabling the OAuth Scopes:**
> Make sure to specify the precise scopes that your MCP tool or service requires under the `--scopes` flag (e.g., GCS, BigQuery, Jira, or GitHub scopes).

---

## 🛡️ 3. Set Up Workload Identity / Platform IAM Bindings

To allow the deployed Vertex AI Reasoning Engine or custom frontend proxy to communicate securely with the Auth Provider, grant them the `roles/iamconnectors.user` or appropriate agent-identity role:

```bash
# Grant access to your Vertex AI Reasoning Engine's Service Account / Agent Identity
gcloud alpha agent-identity authProviders add-iam-policy-binding $PROVIDER_NAME \
    --project=$PROJECT_ID \
    --location=$LOCATION \
    --member="serviceAccount:service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com" \
    --role="roles/iamconnectors.user"
```
