# Shared Flows

## What Are Shared Flows?

- Reusable sequences of policies that can be called from any API proxy or other shared flow
- Similar to functions in programming — define once, use everywhere
- Package as a separate bundle (`sharedflowbundle/`) independent from API proxies
- Must be deployed to the same environment as consuming proxies

## SharedFlow Bundle Structure

```
sharedflowbundle/
├── auth-shared-flow.xml              # Root config (name + revision)
├── sharedflows/
│   └── default.xml                   # Flow definition with Steps
└── policies/
    ├── OAuth-VerifyToken.xml
    ├── AM-SetAuthHeaders.xml
    └── EV-ExtractClaims.xml
```

### Root Config (auth-shared-flow.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharedFlowBundle revision="1" name="auth-shared-flow">
  <DisplayName>Authentication Shared Flow</DisplayName>
  <Description>Verifies OAuth token and extracts claims</Description>
</SharedFlowBundle>
```

### Flow Definition (sharedflows/default.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharedFlow name="default">
  <Step>
    <Name>OAuth-VerifyToken</Name>
  </Step>
  <Step>
    <Name>EV-ExtractClaims</Name>
  </Step>
  <Step>
    <Condition>oauthv2accesstoken.OAuth-VerifyToken.scope != "admin"</Condition>
    <Name>AM-SetAuthHeaders</Name>
  </Step>
</SharedFlow>
```

- Steps execute sequentially (like PreFlow)
- Steps can have Conditions for conditional execution
- Policies are defined the same way as in regular proxies

## Invoking Shared Flows with FlowCallout

```xml
<FlowCallout name="FC-AuthSharedFlow">
  <SharedFlowBundle>auth-shared-flow</SharedFlowBundle>
</FlowCallout>
```

### With Parameters

```xml
<FlowCallout name="FC-RateLimitFlow">
  <SharedFlowBundle>rate-limit-shared-flow</SharedFlowBundle>
  <Parameters>
    <Parameter name="quota.limit">{apiproduct.developer.quota.limit}</Parameter>
    <Parameter name="quota.interval">{apiproduct.developer.quota.interval}</Parameter>
    <Parameter name="quota.timeunit">{apiproduct.developer.quota.timeunit}</Parameter>
  </Parameters>
</FlowCallout>
```

- Parameters are accessible as flow variables inside the shared flow
- The shared flow can read `quota.limit`, `quota.interval`, etc.

## Flow Hooks

- Attach shared flows at the environment level to execute for ALL proxies
- Four hook points:
  - **Pre-proxy FlowHook**: Before ProxyEndpoint PreFlow
  - **Post-proxy FlowHook**: After ProxyEndpoint PostFlow
  - **Pre-target FlowHook**: Before TargetEndpoint PreFlow
  - **Post-target FlowHook**: After TargetEndpoint PostFlow
- Configured via Apigee API or UI (not in proxy bundle XML)
- Use for org-wide concerns: logging, security baseline, compliance checks

## Deployment Order

- Shared flow MUST be deployed before any proxy that references it via FlowCallout
- If you update a shared flow, redeploy it — consuming proxies pick up changes automatically (no proxy redeployment needed)
- If the shared flow is not deployed, FlowCallout raises a fault at runtime

## Common Shared Flow Patterns

### Authentication/Authorization

```xml
<SharedFlow name="default">
  <Step><Name>OAuth-VerifyToken</Name></Step>
  <Step><Name>EV-ExtractScopes</Name></Step>
  <Step>
    <Condition>custom.requiredScope != null</Condition>
    <Name>JS-ValidateScope</Name>
  </Step>
</SharedFlow>
```

### Logging and Correlation ID

```xml
<SharedFlow name="default">
  <Step><Name>AM-SetCorrelationId</Name></Step>
  <Step><Name>AM-AddResponseHeaders</Name></Step>
</SharedFlow>
```

Where AM-SetCorrelationId:

```xml
<AssignMessage name="AM-SetCorrelationId">
  <AssignVariable>
    <Name>custom.correlationId</Name>
    <Ref>request.header.X-Correlation-ID</Ref>
    <Value>{system.uuid}</Value>
  </AssignVariable>
</AssignMessage>
```

### Error Handling

```xml
<SharedFlow name="default">
  <Step><Name>AM-SetErrorDefaults</Name></Step>
  <Step><Name>AM-FormatErrorResponse</Name></Step>
</SharedFlow>
```

### Rate Limiting (Dynamic)

```xml
<SharedFlow name="default">
  <Step><Name>SA-GlobalProtection</Name></Step>
  <Step>
    <Condition>quota.limit != null</Condition>
    <Name>Q-DynamicQuota</Name>
  </Step>
</SharedFlow>
```

### CORS

```xml
<SharedFlow name="default">
  <Step><Name>CORS-AllowOrigins</Name></Step>
</SharedFlow>
```

## When to Extract to a Shared Flow

- The same policy sequence appears in 2+ proxies
- Organization-wide concerns (security baseline, logging format)
- Policies that must be updated atomically across all proxies
- Complex logic that benefits from encapsulation (OAuth + scope validation + claims extraction)

## Complete Example: Shared Flow + Consuming Proxy

### Shared Flow Bundle

```xml
<!-- sharedflowbundle/auth-validation.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<SharedFlowBundle revision="1" name="auth-validation">
  <DisplayName>Auth Validation</DisplayName>
  <Description>Validates API key and extracts developer attributes</Description>
</SharedFlowBundle>
```

```xml
<!-- sharedflowbundle/sharedflows/default.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<SharedFlow name="default">
  <Step><Name>VA-VerifyApiKey</Name></Step>
  <Step><Name>AM-SetDeveloperInfo</Name></Step>
  <Step>
    <Condition>verifyapikey.VA-VerifyApiKey.developer.app.status != "approved"</Condition>
    <Name>RF-AppNotApproved</Name>
  </Step>
</SharedFlow>
```

```xml
<!-- sharedflowbundle/policies/VA-VerifyApiKey.xml -->
<VerifyAPIKey name="VA-VerifyApiKey">
  <APIKey ref="request.header.x-api-key"/>
</VerifyAPIKey>
```

```xml
<!-- sharedflowbundle/policies/AM-SetDeveloperInfo.xml -->
<AssignMessage name="AM-SetDeveloperInfo">
  <AssignVariable>
    <Name>custom.developerEmail</Name>
    <Ref>verifyapikey.VA-VerifyApiKey.developer.email</Ref>
  </AssignVariable>
</AssignMessage>
```

### Consuming Proxy

```xml
<!-- apiproxy/proxies/default.xml -->
<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request>
      <Step><Name>FC-AuthValidation</Name></Step>
    </Request>
  </PreFlow>
  <Flows>
    <Flow name="get-resources">
      <Condition>(proxy.pathsuffix MatchesPath "/resources") and (request.verb = "GET")</Condition>
      <Request/>
    </Flow>
  </Flows>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

```xml
<!-- apiproxy/policies/FC-AuthValidation.xml -->
<FlowCallout name="FC-AuthValidation">
  <SharedFlowBundle>auth-validation</SharedFlowBundle>
</FlowCallout>
```

---

See also: [Proxy Bundle Anatomy](proxy_bundle_anatomy.md) | [Flows and Execution](flows_and_execution.md) | [Policies: Security](policies_security.md)
