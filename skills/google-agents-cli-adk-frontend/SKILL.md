---
name: google-agents-cli-adk-frontend
description: >
  This skill should be used when the user wants to "build a frontend for an ADK agent",
  "connect a client to Vertex AI Reasoning Engine", "parse agent streaming responses",
  "integrate a browser client", "implement dynamic session creation on GCP",
  or needs client-side parsing and routing gotchas for GCP Agent Runtime.
  It compiles the exact schemas, parsing pathways, headers, and FastAPI proxy gotchas.
metadata:
  author: Google
  license: Apache-2.0
  version: 1.0.0
---

# ADK Frontend & Client Integration Playbook

This reference guide serves as an operational AI Skill for downstream coding agents and developers building decoupled frontends (CLI, Textual TUI, Web Dashboards) that interact with custom **Agent Development Kit (ADK)** agents running on **GCP Agent Runtime (Vertex AI Reasoning Engines)**.

---

## 🧭 Architectural Architecture: The Passthrough Gateway

When an ADK agent is deployed to Vertex AI, the platform exposes the FastAPI container behind a secure external gateway:

```text
https://{location}-aiplatform.googleapis.com/reasoningEngines/v1/projects/{project}/locations/{location}/reasoningEngines/{engine_id}/api
```

### 💡 Golden Rule: Communicate via Pure HTTP, bypass ReasoningEngine SDK classes
Do NOT use GenAI or preview ReasoningEngine Python classes to invoke queries in the client. Interact directly with the REST endpoints (like `/run` or `/run_sse`) over standard HTTP/HTTPS.

---

## 🔐 1. Authentication & Bearer Tokens

To access the external gateway, every client request must carry an active Google OAuth Bearer token in the headers.

### Standard Authentication Block (Python)
```python
import google.auth
import google.auth.transport.requests

credentials, _ = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())
headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Content-Type": "application/json"
}
```

---

## 🧩 2. The Double-Namespace App Name Mismatch

There is a strict separation between database management (handled by the platform) and execution routing (handled inside our container):

1.  **Platform Route Namespace (URL)**:
    *   `/apps/{engine_id}/users/{user_id}/sessions`
    *   The `{engine_id}` in the URL **must be the numeric GCP Reasoning Engine ID** (e.g., `6326449168734748672`) so the platform knows which session cluster to access.
2.  **Container Execution Namespace (JSON Payload)**:
    *   `{"app_name": "app", "message": "..."}`
    *   The `app_name` inside the JSON body **must match your container's internal registered ADK application name** (which defaults to `"app"`), NOT the numeric engine ID.

### Target Mapping Reference
```http
POST https://us-east1-aiplatform.googleapis.com/reasoningEngines/v1/projects/my-project/locations/us-east1/reasoningEngines/6326449168734748672/api/run_sse
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "app_name": "app",
  "session_id": "session-123",
  "new_message": {
    "role": "user",
    "parts": [{"text": "Hello, Agent!"}]
  }
}
```

---

## 🗄️ 3. Vertex AI Dynamic Session Creation

On local mock SQLite pipelines, you can assign arbitrary session IDs. In cloud production, the Vertex AI Sessions REST service enforces strict creation structures.

> [!WARNING]
> **No client-assigned IDs or underscores in creation payloads!**
> Vertex AI will throw a `400 FAILED_PRECONDITION` if you supply custom names during the initial session creation, and it rejects underscores (`_`) entirely inside session identifiers.

### How to Create a Session Programmatically (REST):
1.  **Request**: Post an **empty JSON object** to the sessions route.
2.  **GCP Action**: Vertex AI auto-generates a secure, unique 64-bit integer ID.
3.  **Retrieval**: Extract the allocated ID from the response payload.

#### Python Proxy Integration
```python
# Create Session
async with httpx.AsyncClient() as client:
    resp = await client.post(
        f"{GCP_GATEWAY_URL}/apps/{GCP_ENGINE_ID}/users/{USER_ID}/sessions",
        json={}, # MUST be empty!
        headers=headers
    )
    data = resp.json()
    session_id = data.get("id") # Keep this ID for subsequent chat queries!
```

---

## 🌊 4. SSE Stream Parsing Structure

The ADK framework streams Server-Sent Events using standard chunked encoding. Downstream web clients must iterate through nested object arrays to extract text tokens cleanly.

> [!CAUTION]
> **The `[object Object]` Rendering Trap**:
> In streaming events, `chunk.content` is NOT a plain string. It is a nested schema. Concatenating `chunk.content` directly to your UI buffers will print `[object Object]` blocks.

### Standard Stream Event JSON Chunk Structure
```json
{
  "content": {
    "role": "model",
    "parts": [
      {
        "text": "Hello, world!"
      }
    ]
  }
}
```

### Clean JavaScript SSE Stream Parser
```javascript
if (chunk.content && chunk.content.parts) {
    chunk.content.parts.forEach(part => {
        const textChunk = part.text || "";
        if (textChunk) {
            // Append textChunk to your active message bubble in the DOM!
            currentAgentText += textChunk;
        }
    });
}
```

---

## 🚨 5. FastAPI Response Model Compilation Errors

When building a middle-tier proxy server in Python (e.g. FastAPI) that forwards streams to browser clients, Pydantic type annotation errors can prevent the container from booting up.

### The Gotcha
If your path operation return type is annotated with complex starlette streams (e.g. `async def chat(...) -> StreamingResponse | dict`), FastAPI will attempt to compile a Pydantic schema for `StreamingResponse` and crash:
`fastapi.exceptions.FastAPIError: Invalid args for response field!`

### The Fix
Always define `response_model=None` on the decorator of endpoints that can yield streaming or mixed responses.
```python
@app.post("/api/chat", response_model=None)
async def chat_proxy(request: Request):
    # safe to return StreamingResponse!
```

---

## ⚡ Quick Reference Matrix for AI Generators

| Variable Context | Local Mock Mode | GCP Agent Runtime Production Mode |
| :--- | :--- | :--- |
| **Auth Pipeline** | None | `Authorization: Bearer <OAuth_Token>` |
| **Session URL** | `/apps/app/users/{user_id}/sessions` | `/apps/{gcp_numeric_engine_id}/users/{user_id}/sessions` |
| **Create Payload** | `{"session_id": "custom", "state": {}}` | `{}` (Empty JSON. Retrieve dynamic 64-bit ID from response) |
| **Allowed ID Syntax** | Any alphanumeric + special | Lowercase, numbers, and hyphens (`-`) only. **No underscores (`_`)!** |
| **FastAPI Decorators** | Standard | Must use `@app.post(..., response_model=None)` for streams |
| **Stream Chunk Parsing** | Direct text access | Deep path recursion: `chunk.content.parts[i].text` |
