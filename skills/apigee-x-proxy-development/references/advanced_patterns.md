# Advanced Patterns

## Proxy Chaining (LocalTargetConnection)

Call another proxy within the same Apigee environment without network overhead:

```xml
<TargetEndpoint name="chained-target">
  <LocalTargetConnection>
    <APIProxy>user-service-proxy</APIProxy>
    <ProxyEndpoint>default</ProxyEndpoint>
  </LocalTargetConnection>
</TargetEndpoint>
```

- Benefits: Bypasses load balancers and network stack, lower latency
- Billing: Each proxy in the chain counts as one API call
- Data passing: Flow variables are shared across the chain
- CRITICAL: Avoid calling the SAME proxy (infinite loop). Apigee does not prevent this.
- Use case: Microservices composition where each proxy handles a domain

## Composite APIs (Service Aggregation)

Pattern: Call multiple backends, aggregate results, return unified response. Uses ServiceCallout policies + JavaScript aggregation.

### Flow Structure

```xml
<Flow name="composite-user-profile">
  <Condition>(proxy.pathsuffix MatchesPath "/profile") and (request.verb = "GET")</Condition>
  <Request>
    <Step><Name>EV-ExtractUserId</Name></Step>
    <Step><Name>SC-GetUserDetails</Name></Step>
    <Step><Name>SC-GetUserOrders</Name></Step>
    <Step><Name>SC-GetUserPreferences</Name></Step>
  </Request>
  <Response>
    <Step><Name>JS-AggregateProfile</Name></Step>
  </Response>
</Flow>
```

### ServiceCallout Example

```xml
<ServiceCallout name="SC-GetUserDetails">
  <Request>
    <Set>
      <Verb>GET</Verb>
      <Path>/users/{extracted.userId}</Path>
    </Set>
  </Request>
  <Response>userResponse</Response>
  <HTTPTargetConnection>
    <URL>https://user-service.example.com</URL>
  </HTTPTargetConnection>
</ServiceCallout>
```

### Aggregation JavaScript

```javascript
var user = JSON.parse(context.getVariable("userResponse.content"));
var orders = JSON.parse(context.getVariable("ordersResponse.content"));
var prefs = JSON.parse(context.getVariable("prefsResponse.content"));

var profile = {
  user: user,
  recentOrders: orders.items.slice(0, 5),
  preferences: prefs,
  generatedAt: new Date().toISOString()
};

context.setVariable("response.content", JSON.stringify(profile));
context.setVariable("response.header.Content-Type", "application/json");
```

### Error Handling in Composite APIs

Set `continueOnError` on non-critical callouts and check response status codes in JavaScript before aggregating:

```javascript
var userStatus = context.getVariable("userResponse.status.code");
if (userStatus != 200) {
  context.setVariable("custom.errorCode", "USER_SERVICE_ERROR");
  context.setVariable("custom.raiseError", "true");
}
```

## Circuit Breaker Pattern

From GoogleCloudPlatform/apigee-samples — uses Quota as a circuit breaker.

### How It Works

1. Quota policy tracks failure count with `continueOnError=true`
2. When backend fails, increment a failure counter
3. When counter exceeds threshold (quota exceeded), route to secondary backend
4. Counter auto-resets after quota interval

### Implementation

```xml
<!-- Check if circuit is open (quota exceeded = too many failures) -->
<PreFlow name="PreFlow">
  <Request>
    <Step>
      <Name>Q-CircuitBreaker</Name>
    </Step>
  </Request>
</PreFlow>

<!-- Route based on circuit state -->
<RouteRule name="primary">
  <Condition>ratelimit.Q-CircuitBreaker.failed = false</Condition>
  <TargetEndpoint>primary</TargetEndpoint>
</RouteRule>
<RouteRule name="fallback">
  <TargetEndpoint>secondary</TargetEndpoint>
</RouteRule>
```

Quota policy:

```xml
<Quota name="Q-CircuitBreaker" continueOnError="true">
  <Allow count="5"/>
  <Interval>2</Interval>
  <TimeUnit>minute</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <EnforceOnly>true</EnforceOnly>
  <Identifier>circuit-breaker</Identifier>
</Quota>
```

- `EnforceOnly`: only check quota, don't count (counting happens separately when backend fails)

### Incrementing on Backend Failure

In TargetEndpoint PostFlow response:

```xml
<Step>
  <Condition>response.status.code >= 500</Condition>
  <Name>Q-CircuitBreaker-Increment</Name>
</Step>
```

```xml
<Quota name="Q-CircuitBreaker-Increment">
  <Allow count="5"/>
  <Interval>2</Interval>
  <TimeUnit>minute</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <Identifier>circuit-breaker</Identifier>
</Quota>
```

## Traffic Mirroring

Pattern: Send a copy of requests to a secondary service without affecting the primary flow. Use PostClientFlow so mirroring happens AFTER the response is sent to the client:

```xml
<PostClientFlow>
  <Response>
    <Step>
      <Name>FC-TrafficMirror</Name>
    </Step>
  </Response>
</PostClientFlow>
```

The shared flow for mirroring uses ServiceCallout to the mirror target:

```xml
<ServiceCallout name="SC-MirrorRequest">
  <Request>
    <Copy source="request">
      <Headers/>
      <Payload>true</Payload>
      <Verb>true</Verb>
      <Path>true</Path>
    </Copy>
  </Request>
  <Response>mirrorResponse</Response>
  <HTTPTargetConnection>
    <URL>https://mirror-service.example.com</URL>
  </HTTPTargetConnection>
</ServiceCallout>
```

- Does not affect primary request latency
- Useful for canary testing, analytics pipelines, or migration validation

## Multi-Endpoint Proxies

A single proxy can have multiple ProxyEndpoints with different base paths:

```
apiproxy/proxies/
├── public.xml      (BasePath: /v1/api/public)
└── admin.xml       (BasePath: /v1/api/admin)
```

```xml
<!-- apiproxy/proxies/public.xml -->
<ProxyEndpoint name="public">
  <HTTPProxyConnection>
    <BasePath>/v1/api/public</BasePath>
  </HTTPProxyConnection>
  <PreFlow name="PreFlow">
    <Request>
      <Step><Name>VA-VerifyApiKey</Name></Step>
    </Request>
  </PreFlow>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

```xml
<!-- apiproxy/proxies/admin.xml -->
<ProxyEndpoint name="admin">
  <HTTPProxyConnection>
    <BasePath>/v1/api/admin</BasePath>
  </HTTPProxyConnection>
  <PreFlow name="PreFlow">
    <Request>
      <Step><Name>OAuth-VerifyToken</Name></Step>
      <Step><Name>JS-RequireAdminScope</Name></Step>
    </Request>
  </PreFlow>
  <RouteRule name="default">
    <TargetEndpoint>admin-target</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

- Each ProxyEndpoint can have its own flows, fault rules, and route rules
- Use case: Different auth requirements for public vs admin endpoints

## Google Authentication from Proxies

Access Google Cloud services (Cloud Run, Cloud Functions, BigQuery, Secret Manager) using service account auth.

### Access Token (for Google APIs)

```xml
<TargetEndpoint name="cloud-run-target">
  <HTTPTargetConnection>
    <URL>https://my-service-xyz.run.app/api</URL>
    <Authentication>
      <GoogleAccessToken>
        <Scopes>
          <Scope>https://www.googleapis.com/auth/cloud-platform</Scope>
        </Scopes>
      </GoogleAccessToken>
    </Authentication>
  </HTTPTargetConnection>
</TargetEndpoint>
```

### ID Token (for Cloud Run / Cloud Functions)

```xml
<TargetEndpoint name="cloud-function-target">
  <HTTPTargetConnection>
    <URL>https://my-function-xyz.cloudfunctions.net/process</URL>
    <Authentication>
      <GoogleIDToken>
        <Audience>https://my-function-xyz.cloudfunctions.net</Audience>
      </GoogleIDToken>
    </Authentication>
  </HTTPTargetConnection>
</TargetEndpoint>
```

- Apigee automatically generates and caches tokens using the proxy's service account
- No manual token management needed
- Use `GoogleAccessToken` for Google APIs; use `GoogleIDToken` for Cloud Run and Cloud Functions

## mTLS Southbound (Backend mTLS)

```xml
<TargetEndpoint name="mtls-backend">
  <HTTPTargetConnection>
    <SSLInfo>
      <Enabled>true</Enabled>
      <ClientAuthEnabled>true</ClientAuthEnabled>
      <KeyStore>ref://my-keystore</KeyStore>
      <KeyAlias>client-cert</KeyAlias>
      <TrustStore>ref://my-truststore</TrustStore>
    </SSLInfo>
    <URL>https://secure-backend.example.com</URL>
  </HTTPTargetConnection>
</TargetEndpoint>
```

- Always use `ref://` references for keystores/truststores (not direct names) so you can rotate certs without redeploying
- TLS 1.2+ required (Apigee X does not support TLS 1.0/1.1)

## Dynamic Target Routing

Set the target URL dynamically from JavaScript or AssignMessage.

### JavaScript Approach

```javascript
var region = context.getVariable("request.header.X-Region");
var targets = {
  "us": "https://us-api.example.com",
  "eu": "https://eu-api.example.com",
  "ap": "https://ap-api.example.com"
};
context.setVariable("target.url", targets[region] || targets["us"]);
```

### AssignMessage Approach

```xml
<AssignMessage name="AM-SetTarget">
  <AssignVariable>
    <Name>target.url</Name>
    <Value>https://{custom.targetHost}/api</Value>
  </AssignVariable>
</AssignMessage>
```

- `target.url` can be set in ProxyEndpoint request flows (before RouteRule evaluation)
- Combine with a null RouteRule so the proxy uses whatever `target.url` is set to:

```xml
<RouteRule name="dynamic">
  <!-- No TargetEndpoint — uses target.url variable -->
</RouteRule>
```

## AI/LLM Policies

Apigee X includes specialized policies for AI/LLM workloads.

### LLMTokenQuota

Enforce token-based quotas instead of (or alongside) request-count quotas:

```xml
<LLMTokenQuota name="LTQ-MonthlyTokens">
  <LLMTokenUsageSource ref="response"/>
  <LLMModelSource ref="request.header.x-model"/>
  <Allow>
    <Tokens count="1000000"/>
  </Allow>
  <Interval>1</Interval>
  <TimeUnit>month</TimeUnit>
</LLMTokenQuota>
```

### SanitizeUserPrompt (Model Armor)

Filters prompt injection, jailbreak attempts, and harmful content before reaching the LLM:

```xml
<SanitizeUserPrompt name="SUP-FilterPrompt">
  <ModelArmor>
    <TemplateName>projects/{org}/locations/{region}/templates/my-template</TemplateName>
  </ModelArmor>
  <Source>request</Source>
</SanitizeUserPrompt>
```

### SanitizeModelResponse (Model Armor)

Filters harmful or non-compliant content from LLM responses before returning to the client:

```xml
<SanitizeModelResponse name="SMR-FilterResponse">
  <ModelArmor>
    <TemplateName>projects/{org}/locations/{region}/templates/my-template</TemplateName>
  </ModelArmor>
  <Source>response</Source>
</SanitizeModelResponse>
```

### SemanticCacheLookup / SemanticCachePopulate

```xml
<!-- In ProxyEndpoint PreFlow Request -->
<Step><Name>SCL-CheckCache</Name></Step>
```

```xml
<SemanticCacheLookup name="SCL-CheckCache">
  <CacheConfig>
    <CacheResource>semantic-cache</CacheResource>
    <SimilarityThreshold>0.95</SimilarityThreshold>
  </CacheConfig>
  <Source>request</Source>
</SemanticCacheLookup>
```

```xml
<!-- In TargetEndpoint PostFlow Response -->
<Step><Name>SCP-PopulateCache</Name></Step>
```

```xml
<SemanticCachePopulate name="SCP-PopulateCache">
  <CacheConfig>
    <CacheResource>semantic-cache</CacheResource>
  </CacheConfig>
  <Source>response</Source>
</SemanticCachePopulate>
```

- Uses Vertex AI embeddings to find semantically similar prompts
- Dramatically reduces LLM costs for similar queries
- On cache hit, the proxy returns the cached response and skips the LLM backend entirely

---

See also: [Shared Flows](shared_flows.md) | [Endpoints and Routing](endpoints_and_routing.md) | [Policies: Integration](policies_integration.md) | [Policies: Security](policies_security.md)
