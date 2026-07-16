# Flows and Execution Order

This reference covers the complete request/response pipeline in Apigee X, including all flow types, their execution order, policy attachment points, PostClientFlow deep dive, FaultRules evaluation, and guidance on policy placement across ProxyEndpoint and TargetEndpoint.

## Request/Response Pipeline

```
                           ProxyEndpoint                          TargetEndpoint
                ┌────────────────────────────────┐     ┌────────────────────────────────┐
                │                                │     │                                │
  Client ──────>│  PreFlow ──> Conditional ──> PostFlow │──> PreFlow ──> Conditional ──> PostFlow │──> Backend
  Request       │             Flows            │     │             Flows            │    Service
                │         (REQUEST phase)        │     │         (REQUEST phase)        │
                └────────────────────────────────┘     └────────────────────────────────┘
                                                                      │
                                                                      v
                ┌────────────────────────────────┐     ┌────────────────────────────────┐
                │                                │     │                                │
  Client <──────│  PostFlow <── Conditional <── PreFlow │<── PostFlow <── Conditional <── PreFlow │<── Backend
  Response      │             Flows            │     │             Flows            │    Response
                │        (RESPONSE phase)        │     │        (RESPONSE phase)        │
                └────────────────────────────────┘     └────────────────────────────────┘
                         │
                         v
                ┌────────────────────────────────┐
                │     PostClientFlow             │
                │  (after response sent to client│
                │   ProxyEndpoint ONLY)          │
                └────────────────────────────────┘
```

**Execution summary (request direction):**
1. ProxyEndpoint Request: PreFlow -> Conditional Flows -> PostFlow
2. RouteRule evaluation and routing
3. TargetEndpoint Request: PreFlow -> Conditional Flows -> PostFlow
4. Backend call
5. TargetEndpoint Response: PreFlow -> Conditional Flows -> PostFlow
6. ProxyEndpoint Response: PreFlow -> Conditional Flows -> PostFlow
7. Response sent to client
8. PostClientFlow (asynchronous, after response delivery)

## PreFlow

Always executes for every request. Runs before any conditional flows. Use for policies that must apply universally: security validation, authentication, rate limiting, CORS preflight checks.

```xml
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>VA-VerifyAPIKey</Name></Step>
    <Step><Name>SA-SpikeArrest</Name></Step>
    <Step><Name>QU-EnforceQuota</Name></Step>
  </Request>
  <Response>
    <Step><Name>AM-AddCORSHeaders</Name></Step>
  </Response>
</PreFlow>
```

PreFlow is the right place for any policy that must run on every request regardless of the path or verb. If a policy in PreFlow raises a fault, no conditional flows execute.

## Conditional Flows

Only the **first matching flow** executes. Flows are evaluated in XML document order -- the first `<Flow>` whose `<Condition>` evaluates to true wins. A flow with no `<Condition>` element always matches and acts as a catch-all default. Place it last.

```xml
<Flows>
  <Flow name="GetUsers">
    <Condition>(proxy.pathsuffix MatchesPath "/users") and (request.verb = "GET")</Condition>
    <Request>
      <Step><Name>AM-AssignGetUsersRequest</Name></Step>
    </Request>
    <Response>
      <Step><Name>EV-ExtractUsersResponse</Name></Step>
    </Response>
  </Flow>
  <Flow name="CreateUser">
    <Condition>(proxy.pathsuffix MatchesPath "/users") and (request.verb = "POST")</Condition>
    <Request>
      <Step><Name>JTP-ValidateUserPayload</Name></Step>
    </Request>
  </Flow>
  <Flow name="GetUserById">
    <Condition>(proxy.pathsuffix MatchesPath "/users/*") and (request.verb = "GET")</Condition>
    <Request>
      <Step><Name>EV-ExtractUserId</Name></Step>
    </Request>
  </Flow>
  <!-- Catch-all: no Condition means it matches any unmatched request -->
  <Flow name="UnmatchedRoute">
    <Request>
      <Step><Name>RF-RaiseNotFound</Name></Step>
    </Request>
  </Flow>
</Flows>
```

**Key behavior:** Because only the first match executes, order matters. Place more specific paths before general ones. For example, `/users/*` should appear before a bare `/users` catch-all if you want ID-based routes to match first.

## PostFlow

Always executes after conditional flows. Use for response headers, populating cache, or any processing that applies regardless of which conditional flow matched.

```xml
<PostFlow name="PostFlow">
  <Request>
    <Step><Name>AM-SetTargetHeaders</Name></Step>
  </Request>
  <Response>
    <Step><Name>AM-SetStandardResponseHeaders</Name></Step>
    <Step><Name>RC-PopulateResponseCache</Name></Step>
  </Response>
</PostFlow>
```

**Important:** Do NOT place MessageLogging in PostFlow. If the proxy faults before reaching PostFlow, logging will be skipped. Use PostClientFlow for guaranteed logging.

## PostClientFlow -- Deep Dive

### What PostClientFlow Is

PostClientFlow executes **after** the response has been fully sent to the client. It is asynchronous with respect to the client -- it does not affect response latency. The client has already received their response and the connection may already be closed by the time PostClientFlow policies run.

PostClientFlow is defined at the **ProxyEndpoint level only**. It cannot be defined on a TargetEndpoint.

### Allowed Policies -- ONLY TWO

PostClientFlow has strict policy restrictions. Only two policy types are permitted:

1. **MessageLogging** -- log to Cloud Logging, syslog, or file-based destinations
2. **FlowCallout** -- invoke a shared flow

**No other policies are allowed.** Not AssignMessage, not JavaScript, not ServiceCallout, not RaiseFault, not any other policy type. This restriction exists because the response has already been sent to the client -- there is nothing to modify.

**The restriction propagates into shared flows.** When a FlowCallout in PostClientFlow invokes a shared flow, that shared flow is also restricted to MessageLogging and FlowCallout policies only. You cannot use a FlowCallout as a workaround to run arbitrary policies after the response is sent.

### Execution Guarantees

PostClientFlow provides guarantees that no other flow can offer:

- **Executes even if the proxy raised a fault** -- if a RaiseFault policy fired, PostClientFlow still runs
- **Executes even if a FaultRule was triggered** -- error handling does not prevent PostClientFlow execution
- **Executes even if the backend returned an error** -- 5xx responses from the target do not skip PostClientFlow

This makes PostClientFlow the **only place** where you can guarantee logging happens regardless of the outcome of the request. It is the last thing that runs in the entire proxy pipeline.

### Available Variables in PostClientFlow

All variables from the request/response lifecycle remain available in PostClientFlow, plus additional variables that are only populated after the response is sent:

- `client.sent.end.timestamp` -- the timestamp (epoch milliseconds) when the response was fully sent to the client
- `client.sent.start.timestamp` -- the timestamp when the first byte of the response was sent
- `client.received.start.timestamp` -- the timestamp when the first byte of the request was received
- `client.received.end.timestamp` -- the timestamp when the last byte of the request was received

**Calculating total round-trip latency:**
```
Total latency = client.sent.end.timestamp - client.received.start.timestamp
```

This latency calculation is only accurate in PostClientFlow because `client.sent.end.timestamp` is not populated until after the response is fully delivered.

### PostClientFlow Best Practices

- **Always place MessageLogging in PostClientFlow**, not in PostFlow or any other flow. PostClientFlow guarantees execution regardless of errors.
- **Use conditional steps** to log different detail levels for errors vs. successes.
- **Use FlowCallout to shared flows** to organize complex logging into reusable components. Remember that the shared flow is also restricted to MessageLogging and FlowCallout.
- **Do not attempt async webhooks or external calls** from PostClientFlow. ServiceCallout is not allowed, and FlowCallout to a shared flow containing ServiceCallout is also not allowed.
- **Leverage PostClientFlow-only variables** like `client.sent.end.timestamp` for accurate latency metrics.

### PostClientFlow XML Example

```xml
<PostClientFlow name="PostClientFlow">
  <Request/>
  <Response>
    <Step>
      <Name>ML-AuditLog</Name>
    </Step>
    <Step>
      <Condition>response.status.code >= 400</Condition>
      <Name>ML-ErrorLog</Name>
    </Step>
    <Step>
      <Name>FC-AnalyticsSharedFlow</Name>
    </Step>
  </Response>
</PostClientFlow>
```

Note that PostClientFlow uses the `<Response>` element, not `<Request>`. Steps in the `<Request>` element of PostClientFlow are ignored.

### MessageLogging Policy Example for PostClientFlow

```xml
<MessageLogging name="ML-AuditLog">
  <CloudLogging>
    <LogName>projects/{organization.name}/logs/api-audit</LogName>
    <Message contentType="application/json">
      {
        "requestId": "{system.uuid}",
        "timestamp": "{system.timestamp}",
        "verb": "{request.verb}",
        "path": "{request.path}",
        "statusCode": "{response.status.code}",
        "clientIp": "{client.ip}",
        "proxy": "{apiproxy.name}",
        "environment": "{environment.name}",
        "totalLatencyMs": "{client.sent.end.timestamp - client.received.start.timestamp}"
      }
    </Message>
    <Labels>
      <Label>
        <Key>proxy</Key>
        <Value>{apiproxy.name}</Value>
      </Label>
      <Label>
        <Key>env</Key>
        <Value>{environment.name}</Value>
      </Label>
      <Label>
        <Key>status</Key>
        <Value>{response.status.code}</Value>
      </Label>
    </Labels>
    <ResourceType>api</ResourceType>
  </CloudLogging>
</MessageLogging>
```

## Step Configuration

### Name Element

The `<Name>` element references a policy file name **without** the `.xml` extension. The value must match the filename exactly, including case. For example, `<Name>VA-VerifyAPIKey</Name>` references the file `policies/VA-VerifyAPIKey.xml`.

### Condition Element on Step

A `<Condition>` on a `<Step>` determines whether **this specific policy** executes within the flow. This is different from the flow-level `<Condition>`, which controls whether the entire flow is selected. The flow-level condition determines flow selection; the step-level condition determines individual policy execution within the selected flow.

```xml
<Flow name="CreateOrder">
  <!-- Flow-level condition: this flow is selected for POST /orders -->
  <Condition>(proxy.pathsuffix MatchesPath "/orders") and (request.verb = "POST")</Condition>
  <Request>
    <!-- Always runs when this flow is selected -->
    <Step><Name>JTP-ValidateOrderSchema</Name></Step>
    <!-- Only runs if the request has an idempotency key -->
    <Step>
      <Condition>request.header.Idempotency-Key != null</Condition>
      <Name>LC-IdempotencyCheck</Name>
    </Step>
    <!-- Only runs for premium API consumers -->
    <Step>
      <Condition>apiproduct.name = "premium"</Condition>
      <Name>AM-EnrichWithPremiumFields</Name>
    </Step>
  </Request>
</Flow>
```

### continueOnError Attribute

The `continueOnError` attribute is set on the **policy XML itself**, not on the `<Step>` element in the flow. When set to `true`, the flow continues executing subsequent steps even if this policy raises a fault.

```xml
<!-- In the policy file (policies/SC-OptionalEnrichment.xml), NOT in the flow XML -->
<ServiceCallout name="SC-OptionalEnrichment" continueOnError="true">
  <Request>
    <Set>
      <Verb>GET</Verb>
    </Set>
  </Request>
  <HTTPTargetConnection>
    <URL>https://enrichment.example.com/data</URL>
  </HTTPTargetConnection>
  <Response>enrichment.response</Response>
</ServiceCallout>
```

When `continueOnError="true"` and the policy faults, the flow variable `{policy-name}.failed` is set to `true` (e.g., `SC-OptionalEnrichment.failed`). You can check this in subsequent steps.

## Request vs Response Phase

The **request phase** processes the client-to-backend flow. Policies in `<Request>` elements execute in order: ProxyEndpoint request flows first, then TargetEndpoint request flows.

The **response phase** processes the backend-to-client flow. Policies in `<Response>` elements execute in order: TargetEndpoint response flows first, then ProxyEndpoint response flows.

A policy can be attached to either or both phases within the same flow:

```xml
<Flow name="TransformData">
  <Condition>(proxy.pathsuffix MatchesPath "/data")</Condition>
  <Request>
    <Step><Name>AM-TransformRequestToBackendFormat</Name></Step>
  </Request>
  <Response>
    <Step><Name>AM-TransformResponseToClientFormat</Name></Step>
  </Response>
</Flow>
```

## ProxyEndpoint vs TargetEndpoint Flows

### When to Use ProxyEndpoint Flows

ProxyEndpoint flows handle **client-facing concerns**:
- Authentication and authorization: VerifyAPIKey, OAuthV2, VerifyJWT
- CORS headers and preflight handling
- Client request validation and schema enforcement
- Rate limiting (SpikeArrest, Quota)
- Client-specific response formatting
- Client-specific error handling and error message shaping

### When to Use TargetEndpoint Flows

TargetEndpoint flows handle **backend-facing concerns**:
- Backend authentication: Google Auth tokens, mTLS configuration, ServiceCallout for tokens
- Request format conversion to match backend expectations
- Response transformation from backend format to client format
- Backend-specific error handling (timeouts, connection failures, retry logic)
- Circuit breaker logic and backend health checks

### Policy Placement Guide

```
ProxyEndpoint Request PreFlow:       Security, CORS, rate limiting, API key validation
ProxyEndpoint Request Conditionals:  Business logic per operation, schema validation
ProxyEndpoint Request PostFlow:      Final request preparation before routing

TargetEndpoint Request PreFlow:      Backend auth, request transformation, target headers
TargetEndpoint Request Conditionals: Backend-specific logic per operation
TargetEndpoint Request PostFlow:     Final backend request adjustments

TargetEndpoint Response PreFlow:     Initial response processing from backend
TargetEndpoint Response Conditionals: Backend-specific response handling
TargetEndpoint Response PostFlow:    Response transformation, circuit breaker state updates

ProxyEndpoint Response PreFlow:      Initial response processing for client
ProxyEndpoint Response Conditionals: Client-specific response formatting
ProxyEndpoint Response PostFlow:     Standard response headers, caching

PostClientFlow (ProxyEndpoint only): Guaranteed logging, audit trail, analytics
```

## FaultRules Placement

When a policy raises a fault (or a fault is raised explicitly via RaiseFault), the normal flow pipeline stops and FaultRules are evaluated.

### Evaluation Order

**Evaluation order differs by endpoint type:**
- **ProxyEndpoint: Bottom to top** -- last FaultRule in XML is evaluated first
- **TargetEndpoint: Top to bottom** -- first FaultRule in XML is evaluated first

The first FaultRule whose `<Condition>` matches is executed. Only one FaultRule executes (unless DefaultFaultRule with AlwaysEnforce is also configured).

```xml
<!-- ProxyEndpoint example: evaluated BOTTOM TO TOP -->
<!-- Evaluated THIRD -->
<FaultRule name="AuthenticationFault">
  <Condition>(fault.name = "InvalidApiKey")</Condition>
  <Step><Name>AM-AuthErrorResponse</Name></Step>
</FaultRule>
<!-- Evaluated SECOND -->
<FaultRule name="QuotaFault">
  <Condition>(fault.name = "QuotaViolation")</Condition>
  <Step><Name>AM-QuotaErrorResponse</Name></Step>
</FaultRule>
<!-- Evaluated FIRST (bottom-to-top in ProxyEndpoint) -->
<FaultRule name="ThreatFault">
  <Condition>(fault.name Matches "Body*")</Condition>
  <Step><Name>AM-ThreatErrorResponse</Name></Step>
</FaultRule>
```

### ProxyEndpoint FaultRules

FaultRules defined on the ProxyEndpoint catch:
- Faults raised by ProxyEndpoint policies (request and response phases)
- Faults that were not handled by TargetEndpoint FaultRules (faults propagate up)

### TargetEndpoint FaultRules

FaultRules defined on the TargetEndpoint catch:
- Faults raised by TargetEndpoint policies
- Backend communication errors (timeouts, connection refused, SSL errors)

If a TargetEndpoint FaultRule handles the fault, the response flows back through ProxyEndpoint response flows normally. If no TargetEndpoint FaultRule matches, the fault propagates to ProxyEndpoint FaultRules.

### DefaultFaultRule

The `<DefaultFaultRule>` provides a catch-all error handler:

- **`AlwaysEnforce="true"`**: The DefaultFaultRule runs **in addition to** whichever FaultRule matched. It runs after the matching FaultRule. Use this for policies that must always execute during error handling (e.g., setting standard error headers).
- **`AlwaysEnforce="false"` (or omitted)**: The DefaultFaultRule runs **only if** no other FaultRule matched. This is the default behavior.

```xml
<DefaultFaultRule name="DefaultErrorHandler">
  <AlwaysEnforce>true</AlwaysEnforce>
  <Step><Name>AM-StandardErrorFormat</Name></Step>
  <Step><Name>AM-AddErrorCORSHeaders</Name></Step>
</DefaultFaultRule>
```

## Complete ProxyEndpoint Example

This example demonstrates all flow types, FaultRules, DefaultFaultRule, PostClientFlow, and RouteRules in a single ProxyEndpoint:

```xml
<ProxyEndpoint name="default">
  <!-- FaultRules: evaluated in REVERSE XML order -->
  <FaultRules>
    <FaultRule name="AuthenticationErrors">
      <Condition>(fault.name = "InvalidApiKey") or (fault.name = "InvalidAccessToken")</Condition>
      <Step><Name>AM-AuthErrorResponse</Name></Step>
    </FaultRule>
    <FaultRule name="QuotaErrors">
      <Condition>(fault.name = "QuotaViolation") or (fault.name = "SpikeArrestViolation")</Condition>
      <Step><Name>AM-RateLimitErrorResponse</Name></Step>
    </FaultRule>
    <FaultRule name="ValidationErrors">
      <Condition>(fault.name = "JsonThreatProtection") or (fault.name = "SchemaValidation")</Condition>
      <Step><Name>AM-ValidationErrorResponse</Name></Step>
    </FaultRule>
  </FaultRules>

  <!-- DefaultFaultRule: always runs (even after a FaultRule match) -->
  <DefaultFaultRule name="DefaultErrorHandler">
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step><Name>AM-StandardErrorHeaders</Name></Step>
    <Step><Name>AM-AddCORSHeadersOnError</Name></Step>
  </DefaultFaultRule>

  <!-- PreFlow: runs on every request -->
  <PreFlow name="PreFlow">
    <Request>
      <Step><Name>VA-VerifyAPIKey</Name></Step>
      <Step><Name>SA-SpikeArrest</Name></Step>
      <Step><Name>QU-EnforceQuota</Name></Step>
    </Request>
    <Response>
      <Step><Name>AM-AddCORSHeaders</Name></Step>
    </Response>
  </PreFlow>

  <!-- Conditional Flows: first match wins, evaluated in XML order -->
  <Flows>
    <Flow name="ListProducts">
      <Condition>(proxy.pathsuffix MatchesPath "/products") and (request.verb = "GET")</Condition>
      <Request>
        <Step><Name>LC-ProductsCacheLookup</Name></Step>
      </Request>
      <Response>
        <Step><Name>RC-ProductsCachePopulate</Name></Step>
      </Response>
    </Flow>
    <Flow name="CreateProduct">
      <Condition>(proxy.pathsuffix MatchesPath "/products") and (request.verb = "POST")</Condition>
      <Request>
        <Step><Name>JTP-ValidateProductPayload</Name></Step>
        <Step><Name>AM-AssignCreateProductRequest</Name></Step>
      </Request>
    </Flow>
    <Flow name="GetProductById">
      <Condition>(proxy.pathsuffix MatchesPath "/products/*") and (request.verb = "GET")</Condition>
      <Request>
        <Step><Name>EV-ExtractProductId</Name></Step>
      </Request>
    </Flow>
    <Flow name="OptionsPreFlight">
      <Condition>request.verb = "OPTIONS"</Condition>
      <Request>
        <Step><Name>AM-CORSPreflightResponse</Name></Step>
      </Request>
    </Flow>
    <Flow name="UnmatchedRoute">
      <Request>
        <Step><Name>RF-RaiseNotFound</Name></Step>
      </Request>
    </Flow>
  </Flows>

  <!-- PostFlow: runs after the selected conditional flow -->
  <PostFlow name="PostFlow">
    <Request>
      <Step><Name>AM-SetRequestTraceId</Name></Step>
    </Request>
    <Response>
      <Step><Name>AM-SetStandardResponseHeaders</Name></Step>
    </Response>
  </PostFlow>

  <!-- PostClientFlow: runs AFTER response is sent to client -->
  <PostClientFlow name="PostClientFlow">
    <Response>
      <Step>
        <Name>ML-AuditLog</Name>
      </Step>
      <Step>
        <Condition>response.status.code >= 400</Condition>
        <Name>ML-ErrorLog</Name>
      </Step>
      <Step>
        <Name>FC-AnalyticsSharedFlow</Name>
      </Step>
    </Response>
  </PostClientFlow>

  <!-- RouteRules: evaluated in order, first match wins -->
  <RouteRule name="NoRoute-OPTIONS">
    <Condition>request.verb = "OPTIONS"</Condition>
    <!-- No TargetEndpoint: returns response directly without calling backend -->
  </RouteRule>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

---

See also: [Flow Variables and Conditions](flow_variables_and_conditions.md) | [Mediation Policies](policies_mediation.md) | [Fault Handling](fault_handling.md) | [Shared Flows](shared_flows.md)
