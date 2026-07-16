import json
import httpx

async def handle_already_authorized_stream_resumption(
    client: httpx.AsyncClient,
    token: str,
    user_id: str,
    session_id: str,
    function_call_id: str,
    auth_provider_name: str,
    re_gateway: str,
    google_headers: dict
):
    """
    Handles 'Case B' (user has already authorized the application).
    Retrieves the OAuth access token silently, structures the ADK-compliant
    function_response schema, posts it back to the active Vertex AI /run_sse stream,
    and returns a generator to pipe the resumed stream chunks seamlessly.
    """

    # Structure the precise Pydantic-compliant HttpAuth schema that ADK expects
    function_response_payload = {
        "app_name": "app",
        "user_id": user_id,
        "session_id": session_id,
        "streaming": True,
        "new_message": {
            "role": "user",
            "parts": [
                {
                    "function_response": {
                        "id": function_call_id,
                        "name": "adk_request_credential",
                        "response": {
                            "auth_scheme": {
                                "type": "http",
                                "scheme": "bearer",
                                "bearerFormat": "JWT"
                            },
                            "exchanged_auth_credential": {
                                "auth_type": "http",
                                "http": {
                                    "scheme": "bearer",
                                    "credentials": {
                                        "token": token
                                    }
                                }
                            },
                            "credential_key": auth_provider_name
                        }
                    }
                }
            ]
        }
    }

    # Post the resumption payload to Vertex AI's run_sse endpoint inline
    # This acts as a nested stream resumption
    async with client.stream(
        "POST",
        f"{re_gateway}/apps/app/users/{user_id}/sessions/{session_id}/run_sse",
        json=function_response_payload,
        headers=google_headers
    ) as resumed_response:
        if resumed_response.status_code != 200:
            yield f"event: error\ndata: Failed to resume authorized session stream: {resumed_response.status_code}\n\n"
            return

        # Direct-pipe the resumed chunks to the client's original HTTP connection
        # From the client side, there is zero pause, zero popups, and total fluidity!
        async for line in resumed_response.aiter_lines():
            if not line.strip():
                continue
            yield f"{line}\n\n"
