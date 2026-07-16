import json
import httpx
import google.auth
import google.auth.transport.requests
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()

# Setup Google API Credentials
credentials, _ = google.auth.default()
auth_request = google.auth.transport.requests.Request()

def get_google_auth_headers():
    credentials.refresh(auth_request)
    return {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }

# Vertex AI App Gateway Configuration
GCP_REGION = "us-central1"
PROJECT_ID = "vibe-cabral"
ENGINE_ID = "1234567890123456789"  # Replace with actual Reasoning Engine ID
RE_GATEWAY = f"https://{GCP_REGION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{GCP_REGION}/reasoningEngines/{ENGINE_ID}/api"

# Auth Manager Provider configuration (V2)
AUTH_PROVIDER_NAME = "gcs-mcp-auth-provider"
AUTH_ENDPOINT = f"https://agentidentitycredentials.googleapis.com/v1alpha/projects/{PROJECT_ID}/locations/{GCP_REGION}/authProviders/{AUTH_PROVIDER_NAME}"

@router.post("/api/chat", response_model=None)
async def chat_proxy(request: Request):
    """
    Proxies user queries to the Vertex AI Reasoning Engine stream.
    Intercepts any 'adk_request_credential' toolcalls to fetch the consent URI
    or silent access token, and manages stateless cookies.
    """
    body = await request.json()
    user_id = body.get("user_id", "default-web-user")
    session_id = body.get("session_id")
    prompt = body.get("prompt")

    # Format the standard ADK/Reasoning Engine execution body
    re_payload = {
        "app_name": "app",
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": prompt}]
        },
        "streaming": True
    }

    async def stream_generator():
        headers = get_google_auth_headers()
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Post original user query to Reasoning Engine's stream endpoint
            async with client.stream(
                "POST",
                f"{RE_GATEWAY}/apps/{ENGINE_ID}/users/{user_id}/sessions/{session_id}/run_sse",
                json=re_payload,
                headers=headers
            ) as response:
                if response.status_code != 200:
                    yield f"event: error\ndata: Failed to query reasoning engine: {response.status_code}\n\n"
                    return

                # Read and yield original chunks line by line
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    yield f"{line}\n\n"

                    # 2. Look for the adk_request_credential toolcall signature
                    if "adk_request_credential" in line:
                        # Extract the function call properties to call Agent Identity
                        try:
                            # Parse out the function call ID from the event chunk
                            # In a real app, extract cleanly via JSON parsing or regex
                            # This payload contains: {'auth_config': ..., 'auth_request_function_call_id': ...}
                            
                            # Build callback redirection URI (continueUri)
                            # Must match your registered Authorized Redirect URIs in Google Console!
                            base_url = str(request.base_url).rstrip('/')
                            continue_uri = f"{base_url}/validateUserId"

                            # Call the credentials retrieve endpoint
                            retrieve_payload = {
                                "user_id": user_id,
                                "continue_uri": continue_uri
                            }
                            
                            retrieve_resp = await client.post(
                                f"{AUTH_ENDPOINT}/credentials:retrieve",
                                json=retrieve_payload,
                                headers=headers
                            )
                            
                            ret_data = retrieve_resp.json()
                            
                            if "response" in ret_data:
                                response_payload = ret_data["response"]
                                
                                # CASE A: Consent is required (returns authorizationUri and consentNonce)
                                if "authorizationUri" in response_payload:
                                    auth_uri = response_payload["authorizationUri"]
                                    nonce = response_payload.get("consentNonce")
                                    
                                    # Output a custom event payload to trigger client popup
                                    # Frontend will capture this and open the window
                                    payload = {
                                        "auth_uri": auth_uri,
                                        "nonce": nonce,
                                        "auth_provider_name": AUTH_PROVIDER_NAME
                                    }
                                    yield f"event: consent_required\ndata: {json.dumps(payload)}\n\n"
                                    return

                                # CASE B: Already authorized (returns active OAuth token directly)
                                elif "token" in response_payload:
                                    # Forwards token and seamlessly resumes the stream
                                    # See examples/stream_resumption.py for resumption details
                                    pass
                        except Exception as e:
                            yield f"event: error\ndata: Error handling credential retrieve: {str(e)}\n\n"

    # Define response to set cookies on the browser client
    return StreamingResponse(stream_generator(), media_type="text/event-stream")
