# Anti-patterns and Best Practices

## Policy Anti-patterns

### Caching Error Responses

- **Problem**: ResponseCache by default caches ALL responses including 4xx/5xx errors
- **Impact**: Clients receive cached error responses even after the issue is resolved
- **Fix**: Always set `<ExcludeErrorResponse>true</ExcludeErrorResponse>` on ResponseCache

```xml
<ResponseCache name="RC-CacheResponse">
  <CacheKey>
    <Prefix>v1</Prefix>
    <KeyFragment ref="request.uri"/>
  </CacheKey>
  <ExpirySettings>
    <TimeoutInSec>300</TimeoutInSec>
  </ExpirySettings>
  <ExcludeErrorResponse>true</ExcludeErrorResponse>
</ResponseCache>
```

### Long-lived OAuth Tokens

- **Problem**: Setting ExpiresIn to very long durations (hours/days)
- **Impact**: Compromised tokens remain valid for extended periods
- **Fix**: Use short-lived access tokens (minutes) with refresh tokens

```xml
<!-- WRONG: token valid for 24 hours -->
<OAuthV2 name="OAuth-GenerateToken">
  <Operation>GenerateAccessToken</Operation>
  <ExpiresIn>86400000</ExpiresIn>
</OAuthV2>

<!-- CORRECT: short-lived token (30 minutes) -->
<OAuthV2 name="OAuth-GenerateToken">
  <Operation>GenerateAccessToken</Operation>
  <ExpiresIn>1800000</ExpiresIn>
  <RefreshTokenExpiresIn>86400000</RefreshTokenExpiresIn>
  <SupportedGrantTypes>
    <GrantType>client_credentials</GrantType>
  </SupportedGrantTypes>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
</OAuthV2>
```

### Using continueOnError on Security Policies

- **Problem**: `continueOnError="true"` on VerifyAPIKey, OAuthV2, VerifyJWT
- **Impact**: Failed authentication silently passes, allowing unauthorized access
- **Fix**: NEVER use continueOnError on security policies. Only use on optional/best-effort policies like ServiceCallout for enrichment

```xml
<!-- WRONG: failed auth silently passes -->
<VerifyAPIKey name="VAK-VerifyKey" continueOnError="true">
  <APIKey ref="request.header.x-api-key"/>
</VerifyAPIKey>

<!-- CORRECT: failed auth raises a fault -->
<VerifyAPIKey name="VAK-VerifyKey">
  <APIKey ref="request.header.x-api-key"/>
</VerifyAPIKey>

<!-- SAFE: optional enrichment callout -->
<ServiceCallout name="SC-GetRecommendations" continueOnError="true">
  <Request clearPayload="true" variable="recoRequest">
    <Set>
      <URL>https://recommendations.example.com/suggest</URL>
      <Verb>GET</Verb>
    </Set>
  </Request>
  <Response>recoResponse</Response>
  <Timeout>3000</Timeout>
</ServiceCallout>
```

## Architecture Anti-patterns

### Invoking Management API from Proxies

- **Problem**: Calling Apigee management API endpoints from within running proxies
- **Impact**: Creates circular dependencies, performance issues, potential security risks
- **Fix**: Use KVM, PropertySet, or external config management for runtime configuration

### Proxy Nesting Without LocalTargetConnection

- **Problem**: One proxy calling another via HTTPTargetConnection to the same Apigee host
- **Impact**: Unnecessary network hops through load balancers, added latency
- **Fix**: Use LocalTargetConnection for proxy-to-proxy communication within the same environment

```xml
<!-- WRONG: network round-trip through load balancer -->
<TargetEndpoint name="chained">
  <HTTPTargetConnection>
    <URL>https://my-apigee-host.com/v1/other-proxy</URL>
  </HTTPTargetConnection>
</TargetEndpoint>

<!-- CORRECT: direct in-memory proxy chain -->
<TargetEndpoint name="chained">
  <LocalTargetConnection>
    <APIProxy>other-proxy</APIProxy>
    <ProxyEndpoint>default</ProxyEndpoint>
  </LocalTargetConnection>
</TargetEndpoint>
```

### Not Using Shared Flows for Reusable Logic

- **Problem**: Copy-pasting the same policy sequences across multiple proxies
- **Impact**: Maintenance burden, inconsistency when updating logic
- **Fix**: Extract common policy sequences (auth, logging, error handling) into shared flows

### Not Version-Controlling Proxy Bundles

- **Problem**: Editing proxies only through the UI without source control
- **Impact**: No audit trail, no rollback capability, team collaboration issues
- **Fix**: Store all proxy bundles in git. Use the `apiproxy/` directory structure as-is.

## Performance Anti-patterns

### Processing Large Payloads Repeatedly

- **Problem**: Multiple policies that parse the same large payload (multiple ExtractVariables on same body, XSL + XMLtoJSON)
- **Impact**: High memory and CPU usage, slow proxy execution
- **Fix**: Parse once, store results in variables. Enable streaming for passthrough scenarios.

### Disabling HTTP Keep-Alive Unnecessarily

- **Problem**: Disabling keep-alive connections to backend services
- **Impact**: TCP connection overhead on every request, increased latency
- **Fix**: Only disable keep-alive when specifically required by the backend

### MaxFailures With Single TargetServer

- **Problem**: Setting MaxFailures on a LoadBalancer with only one server
- **Impact**: When failures exceed threshold, the server is marked down with no fallback
- **Fix**: Use multiple TargetServers, or remove MaxFailures for single-server configs

```xml
<!-- WRONG: single server with MaxFailures -->
<HTTPTargetConnection>
  <LoadBalancer>
    <Server name="only-server"/>
    <MaxFailures>3</MaxFailures>
  </LoadBalancer>
</HTTPTargetConnection>

<!-- CORRECT: multiple servers with MaxFailures -->
<HTTPTargetConnection>
  <LoadBalancer>
    <Server name="server-1"/>
    <Server name="server-2"/>
    <MaxFailures>3</MaxFailures>
  </LoadBalancer>
</HTTPTargetConnection>
```

## Best Practices

### Policy Ordering

Place policies in this order within flows:

1. **Security** (PreFlow): VerifyAPIKey/OAuthV2/VerifyJWT, AccessControl, ThreatProtection
2. **Mediation** (Request): ExtractVariables, AssignMessage, transformations
3. **Traffic management** (PreFlow, after auth): SpikeArrest, Quota
4. **Business logic** (Conditional Flows): ServiceCallout, JavaScript, custom logic
5. **Caching** (PostFlow Response): ResponseCache
6. **Logging** (PostClientFlow): MessageLogging

### Naming Conventions

- Policy files: `[Abbreviation]-[Purpose].xml` (AM-SetHeaders, SC-GetProfile, RF-ValidationError)
- ProxyEndpoint files: descriptive name (default.xml, public.xml, admin.xml)
- Flow names: lowercase with hyphens matching API operations (get-users, create-order)
- Base paths: versioned (`/v1/resource`, `/v2/resource`)
- SharedFlow bundles: descriptive kebab-case (auth-shared-flow, rate-limit-shared-flow)

### Code vs Policies Decision Matrix

| Need | Use |
|---|---|
| Set/remove/add headers | AssignMessage or HTTPModifier |
| Extract values from payload | ExtractVariables |
| Simple payload with templates | AssignMessage |
| Complex JSON transformation | JavaScript |
| Multi-branch conditional logic | JavaScript |
| HTTP calls to external services | ServiceCallout |
| Rate limiting | SpikeArrest + Quota |
| Authentication | VerifyAPIKey, OAuthV2, VerifyJWT |
| Format conversion (JSON/XML) | JSONtoXML / XMLtoJSON |
| Response aggregation | JavaScript |

### Base Path Design

- Always include version: `/v1/resource`, `/v2/resource`
- Keep paths RESTful: `/v1/users/{userId}/orders`
- Base path must be unique per environment group
- Limit: 3000 base paths per environment group

### PostClientFlow Usage

- Always use PostClientFlow for MessageLogging (guaranteed execution even on error)
- PostClientFlow is async -- does not affect response latency
- Only MessageLogging and FlowCallout are allowed in PostClientFlow

```xml
<PostClientFlow name="PostClientFlow">
  <Response>
    <Step>
      <Name>ML-LogToCloud</Name>
    </Step>
  </Response>
</PostClientFlow>
```

### Fault Handling

- Every proxy MUST have a DefaultFaultRule
- Use consistent error response format across all proxies (extract to shared flow)
- Include correlation IDs (`system.uuid` or X-Request-ID header) in all error responses
- Handle known fault names explicitly with FaultRules
- See [fault_handling.md](./fault_handling.md) for the complete pattern

### Security

- Authenticate in PreFlow (executes for every request, no conditional bypass)
- Use ThreatProtection policies for public-facing APIs
- Remove sensitive headers before sending to backend (Authorization, internal tokens)
- Use encrypted KVM for storing secrets
- Short-lived tokens with refresh mechanisms

---

See also:
- [Fault Handling](./fault_handling.md)
- [Flows and Execution](./flows_and_execution.md)
- [Policies: Security](./policies_security.md)
- [Policies: Traffic Management](./policies_traffic_management.md)
- [Policies: Caching](./policies_caching.md)
- [Shared Flows](./shared_flows.md)
- [End-to-End Examples](./end_to_end_examples.md)
