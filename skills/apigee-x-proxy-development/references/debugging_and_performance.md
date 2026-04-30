# Debugging and Performance Optimization

## Debug Sessions

### What Debug Sessions Are

Debug sessions capture request/response data as it flows through the proxy pipeline. They record variables, headers, payloads, and policy execution details at each flow phase. This is the primary tool for understanding what happens inside a proxy at runtime.

Key characteristics:
- Default: 5 minutes (300 seconds), max 10 minutes (600 seconds)
- Maximum transactions per session: 15
- Available via the Apigee UI or REST API
- Sessions are scoped to a specific proxy revision in a specific environment
- Multiple sessions can run concurrently, but this increases overhead

### Creating Debug Sessions via REST API

```bash
# Create a debug session
curl -X POST \
  "https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/apis/{api}/revisions/{rev}/debugsessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 600, "count": 15, "tracesize": 5120}'
```

Parameters:
- `timeout`: session duration in seconds (default 300 = 5 minutes, max 600 = 10 minutes)
- `count`: max transactions to capture (default 10, max 15)
- `tracesize`: max bytes captured from payload (0-5120, default 5120)

```bash
# List active debug sessions
curl -X GET \
  "https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/apis/{api}/revisions/{rev}/debugsessions" \
  -H "Authorization: Bearer $TOKEN"

# Get debug session data
curl -X GET \
  "https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/apis/{api}/revisions/{rev}/debugsessions/{session_id}/data" \
  -H "Authorization: Bearer $TOKEN"

# Delete a debug session
curl -X DELETE \
  "https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/apis/{api}/revisions/{rev}/debugsessions/{session_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Filtering Debug Sessions

Capture only matching requests. This is essential for production environments where traffic volume is high and you need to isolate specific transactions:

```bash
# Filter by header
curl -X POST "...debugsessions?header_x-tenant-id=acme" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 300}'

# Filter by query parameter
curl -X POST "...debugsessions?qparam_debug=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 300}'

# Multiple filters (all must match)
curl -X POST "...debugsessions?header_x-tenant-id=acme&qparam_version=2" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"timeout": 300}'
```

All filter conditions must match for a request to be captured. This is an AND operation, not OR.

### What Debug Sessions Capture

At each flow phase (PreFlow, conditional flows, PostFlow, each policy execution):
- HTTP headers (request and response)
- Message body content (up to tracesize bytes)
- Flow variable values and mutations
- Policy execution results and timing (nanoseconds)
- Conditional flow decisions (which conditions evaluated, which matched)
- Error and fault details including fault.name and fault.category
- Target request and response details

### JavaScript print() for Debug Output

```javascript
// Basic variable inspection
print("User ID: " + context.getVariable("custom.userId"));
print("Target URL: " + context.getVariable("target.url"));
print("Response status: " + context.getVariable("response.status.code"));

// Inspecting complex objects
var payload = JSON.parse(context.getVariable("request.content"));
print("Request keys: " + Object.keys(payload).join(", "));
print("Item count: " + payload.items.length);

// Conditional debug output
var debugMode = context.getVariable("request.header.x-debug");
if (debugMode === "verbose") {
    print("Full request content: " + context.getVariable("request.content"));
    print("All query params: " + context.getVariable("request.querystring"));
}
```

Behavior:
- Output appears in debug session under `stepExecution-stdout`
- In UI: visible under the JavaScript policy step in the debug trace
- Only visible when a debug session is active -- no performance impact in production otherwise
- Use liberally during development; remove or guard with conditions in production

### Private Variable Masking

Variables prefixed with `private.` are masked (shown as `*****`) in debug output:

```javascript
// MASKED in debug output -- safe for secrets
context.setVariable("private.api_secret", "s3cr3t");
context.setVariable("private.internal_token", bearerToken);

// VISIBLE in debug output -- do NOT store secrets here
context.setVariable("api_secret", "s3cr3t");
```

Critical: if you copy a `private.` variable to a non-private variable, the value becomes visible in debug sessions. This is a common mistake:

```javascript
// BAD: exposes the secret in debug
var secret = context.getVariable("private.api_secret");
context.setVariable("exposed_secret", secret);  // now visible in debug

// GOOD: keep it in private namespace
var secret = context.getVariable("private.api_secret");
context.setVariable("private.derived_key", computeKey(secret));
```

### Data Masking Configuration

Beyond the `private.` prefix (which hides variables completely), Apigee supports configuration-based data masking that replaces sensitive values with asterisks in debug sessions.

Configure masking at the environment or proxy level via the API:

```bash
curl -X POST "https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/debugmask" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "requestJSONPaths": ["$.creditCard", "$.ssn"],
    "responseJSONPaths": ["$.secret"],
    "requestXPaths": ["/request/password"],
    "faultJSONPaths": ["$.internalError"]
  }'
```

**Key distinction:**
- `private.` prefix: variable is **hidden entirely** from debug sessions (not visible at all)
- Data masking config: value is **replaced with asterisks** (`*****`) but the variable name remains visible

Masking occurs at the Apigee gateway before data reaches the management plane -- sensitive data never leaves the runtime.

### Debug Best Practices

**In production:**
- Always use filters to target specific requests
- Keep sessions short (2-5 minutes)
- Use small tracesize (1024-2048) to minimize overhead
- Debug one proxy revision at a time
- Check for existing sessions before creating new ones
- Coordinate with team members to avoid multiple concurrent sessions

**During development:**
- Full tracesize (5120) for payload visibility
- Use print() statements in JavaScript policies
- Add temporary AssignMessage policies to inspect variable values
- Check variable availability per flow phase (request.* not available in response flow)
- Use the UI debug tool for interactive exploration

### Common Debugging Scenarios

**"Policy not executing"** -- check:
1. Flow condition: is the conditional flow being matched? Remember first-match-wins in conditional flows
2. Step condition: is the Step-level `<Condition>` evaluating to true?
3. Policy name: does the `<Name>` in the Step match the policy XML filename exactly?
4. Flow phase: is the policy in the request flow but you are looking for it in the response flow?

**"Variable is null"** -- check:
1. Flow phase: `request.*` variables are unavailable in the response flow; use `message.*` for phase-independent access
2. Policy order: is the policy that populates the variable running BEFORE the one that reads it?
3. Variable name: exact match including case sensitivity
4. Error in populating policy: did the upstream policy execute successfully or raise a fault?

**"Fault not caught"** -- check:
1. FaultRule condition: does `fault.name` match exactly? Values are case-sensitive
2. FaultRule placement: ProxyEndpoint FaultRules catch proxy faults plus bubbled target faults; TargetEndpoint FaultRules catch only target faults
3. FaultRules are evaluated in REVERSE XML order (last FaultRule in XML is checked first)
4. DefaultFaultRule: is one defined as a catch-all?

**"Unexpected response from target"** -- check:
1. Inspect `target.url` to verify the actual URL sent to the backend
2. Check `target.copy.pathsuffix` and path suffix behavior
3. Look at `target.received.status.code` vs `response.status.code` (the latter may be modified by response policies)
4. Verify headers sent to target: load balancing headers, host headers, authentication headers

## Performance Optimization

### Streaming for Large Payloads

Enable streaming when proxying large files or real-time streams without inspecting payloads:

```xml
<ProxyEndpoint name="default">
  <HTTPProxyConnection>
    <BasePath>/v1/files</BasePath>
    <Properties>
      <Property name="request.streaming.enabled">true</Property>
      <Property name="response.streaming.enabled">true</Property>
    </Properties>
  </HTTPProxyConnection>
  ...
</ProxyEndpoint>
```

Similarly for the target endpoint:

```xml
<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <URL>https://storage.example.com</URL>
    <Properties>
      <Property name="request.streaming.enabled">true</Property>
      <Property name="response.streaming.enabled">true</Property>
    </Properties>
  </HTTPTargetConnection>
</TargetEndpoint>
```

**Policies INCOMPATIBLE with streaming** (they require full payload buffering):
- JSONtoXML / XMLtoJSON
- ExtractVariables (payload extraction -- header/queryparam extraction still works)
- JSONThreatProtection / XMLThreatProtection
- JavaScript (when accessing `request.content` or `response.content`)
- XSLTransform
- OASValidation (body validation)

If any of these execute while streaming is enabled, Apigee silently buffers the entire payload, defeating the purpose. For large payloads this can cause OutOfMemory errors.

**When to use streaming:**
- File upload/download proxies
- Video/media streaming
- Large dataset passthrough
- Server-Sent Events (SSE)
- Any proxy where payload inspection is not needed

### Payload Size Limits

| Limit | Value |
|---|---|
| Default max request/response body | 10 MB |
| Error on exceeding limit | HTTP 413 `protocol.http.TooBigBody` |
| Cache entry max size | 256 KB |
| With streaming enabled | Effectively unlimited (requires sufficient memory) |

### Timeout Configuration

```xml
<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <URL>https://backend.example.com</URL>
    <Properties>
      <Property name="connect.timeout.millis">5000</Property>
      <Property name="io.timeout.millis">30000</Property>
      <Property name="keepalive.timeout.millis">60000</Property>
    </Properties>
  </HTTPTargetConnection>
</TargetEndpoint>
```

| Property | Default | Description |
|---|---|---|
| `connect.timeout.millis` | 3000 | TCP connection establishment timeout |
| `io.timeout.millis` | 55000 | Data read/write timeout after connection established |
| `keepalive.timeout.millis` | 60000 | Idle connection timeout before close |

Interaction with `api.timeout`: total proxy time is bounded by `api.timeout` (if set). The actual I/O timeout used is `min(api.timeout - elapsed, io.timeout.millis)`.

Property values MUST be literals. Variable substitution is not supported for these properties.

### Policy Performance Tiers

**Lightweight (nanoseconds to microseconds):**
- AssignMessage (variable assignment, header manipulation)
- Condition evaluation
- HTTPModifier
- ReadPropertySet

**Medium (microseconds to low milliseconds):**
- ExtractVariables (header/param extraction)
- VerifyAPIKey
- SpikeArrest / Quota (distributed counter check)
- ResponseCache (cache lookup)
- CORS

**Heavy (milliseconds and above):**
- JavaScript (custom computation, JSON parsing)
- ServiceCallout (network I/O -- depends on backend latency)
- JSONtoXML / XMLtoJSON (full DOM parse)
- XSLTransform (full DOM parse + transformation)
- OAuthV2 (token generation/verification)
- OASValidation (spec parsing + validation)

### Optimization Strategies

**1. Consolidate policies:**

```xml
<!-- BAD: Three separate AssignMessage policies -->
<Step><Name>AM-SetHeader1</Name></Step>
<Step><Name>AM-SetHeader2</Name></Step>
<Step><Name>AM-SetHeader3</Name></Step>

<!-- GOOD: One AssignMessage with all headers -->
<Step><Name>AM-SetAllHeaders</Name></Step>
```

Each policy invocation has overhead. Combining related operations into a single policy reduces the total number of steps in the pipeline.

**2. Fail fast with condition ordering:**

```xml
<!-- GOOD: Most selective condition first, cheapest checks earliest -->
<Flows>
  <Flow name="admin-delete">
    <Condition>(proxy.pathsuffix MatchesPath "/admin/*") and (request.verb = "DELETE")</Condition>
    ...
  </Flow>
  <Flow name="get-resource">
    <Condition>request.verb = "GET"</Condition>
    ...
  </Flow>
</Flows>
```

Place authentication and authorization checks early in the request PreFlow so unauthorized requests are rejected before expensive processing.

**3. Prefer policies over JavaScript:**

Use AssignMessage, ExtractVariables, and HTTPModifier for simple transformations. Reserve JavaScript for logic that policies cannot express declaratively: multi-branch decisions, aggregation, complex string manipulation, and crypto operations.

| Task | Preferred Approach |
|---|---|
| Set/remove headers | AssignMessage |
| Extract from JSON/XML payload | ExtractVariables |
| Simple conditional assignment | AssignMessage with condition |
| Multi-branch routing logic | JavaScript |
| Data aggregation from multiple sources | JavaScript |
| Complex string formatting | JavaScript |

**4. Cache aggressively:**

- ResponseCache for GET endpoints returning stable data
- PopulateCache / LookupCache for ServiceCallout results
- Set appropriate TTLs: stable data (hours), semi-fresh data (minutes)
- Always set `<ExcludeErrorResponse>true</ExcludeErrorResponse>` to avoid caching errors
- Use cache keys that reflect the actual variation (tenant, locale, version)

**5. Minimize payload processing:**

- Do not parse payloads you do not need to inspect
- Extract only the fields you need using specific JSONPath expressions, not the entire body
- Enable streaming for passthrough scenarios
- Avoid JSONtoXML/XMLtoJSON unless the consumer truly needs a different format

**6. Connection reuse:**

- Keep `keepalive.timeout.millis` greater than 0 (do NOT disable keep-alive)
- Higher values reduce TCP handshake overhead but consume memory on the runtime
- Default of 60000 ms (60 seconds) is appropriate for most use cases
- For high-traffic proxies with stable backends, consider increasing to 120000 ms

**7. ServiceCallout optimization:**

- Set tight timeouts for non-critical callouts
- Use `continueOnError="true"` for optional enrichment calls
- Cache ServiceCallout responses with PopulateCache / LookupCache
- Consider whether the callout can be moved to PostClientFlow (if only for logging/analytics -- the response is already sent to the client)
- Parallelize independent ServiceCallouts by placing them in the same flow step (not natively supported; use JavaScript with httpClient for parallel calls)

**8. Quota and SpikeArrest placement:**

- Place SpikeArrest as early as possible in the request PreFlow
- Place Quota after VerifyAPIKey (Quota often uses the API product from the key)
- Both use distributed counters; avoid placing them in conditional flows where they might execute unnecessarily

---

See also:
- [Proxy Bundle Anatomy](proxy_bundle_anatomy.md)
- [Flows and Execution](flows_and_execution.md)
- [Flow Variables and Conditions](flow_variables_and_conditions.md)
- [Fault Handling](fault_handling.md)
- [JavaScript Development](javascript_development.md)
- [Caching Policies](policies_caching.md)
- [Traffic Management Policies](policies_traffic_management.md)
- [Advanced Patterns](advanced_patterns.md)
