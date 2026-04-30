---
name: apigee-x-proxy-development
description: >
  Use when developing, reviewing, debugging, or explaining Apigee X API proxy
  configurations — proxy bundles, policies, flows, endpoints, shared flows,
  fault handling, and JavaScript callouts.
---

# Apigee X API Proxy Development

Comprehensive skill for building API proxies on Google Cloud's Apigee X platform. Covers the full proxy development lifecycle: bundle structure, endpoint configuration, flow design, policy implementation, fault handling, JavaScript extensibility, shared flows, and advanced patterns.

**This skill covers:** API proxy bundle authoring, policy configuration (42+ policy types), flow execution design, conditional routing, fault handling, JavaScript callouts, shared flows, and advanced development patterns.

**This skill does NOT cover:** Apigee X deployment/provisioning, CI/CD pipelines, Apigee Hybrid-specific configuration, GCP infrastructure setup, or Apigee management API usage. Focus is exclusively on proxy development artifacts.

## When to Use This Skill

Use this skill when the user is:
- Building new API proxy bundles from scratch
- Writing or configuring Apigee policies (security, mediation, traffic management, etc.)
- Designing flow pipelines (PreFlow, conditional flows, PostFlow, PostClientFlow)
- Configuring ProxyEndpoints, TargetEndpoints, or RouteRules
- Implementing fault handling (FaultRules, DefaultFaultRule, RaiseFault)
- Writing JavaScript callout code for Apigee proxies
- Creating or consuming shared flows
- Debugging proxy execution or policy errors
- Reviewing existing proxy configurations for correctness or best practices
- Asking about Apigee X policy behavior, flow variables, or conditions

Do NOT use this skill when the user is:
- Deploying proxies to Apigee environments (use deployment tooling instead)
- Configuring Apigee Hybrid runtime infrastructure
- Setting up CI/CD for proxy bundles
- Managing Apigee organizations, environments, or environment groups via API
- Working with non-Apigee API gateways

## Consulting Official Documentation

When you need to look up specific policy syntax, verify behavior, or find recent changes:

- **Web search**: Use `site:cloud.google.com/apigee` to restrict results to official Apigee X docs
- **Policy reference**: Fetch `https://cloud.google.com/apigee/docs/api-platform/reference/policies/[policy-name]-policy`
- **Configuration reference**: Fetch `https://cloud.google.com/apigee/docs/api-platform/reference/api-proxy-configuration-reference`
- **Flow variables**: Fetch `https://cloud.google.com/apigee/docs/api-platform/reference/variables-reference`
- **Conditions**: Fetch `https://cloud.google.com/apigee/docs/api-platform/reference/conditions-reference`
- **Vetted examples**: Browse `https://github.com/GoogleCloudPlatform/apigee-samples` for production patterns

**Important**: Do NOT use `docs.apigee.com` — that is legacy Apigee Edge documentation. Always use `cloud.google.com/apigee` for Apigee X.

## API Proxy Bundle Quick Reference

```
apiproxy/
├── MyProxy.xml                    # Root proxy definition (name + revision)
├── proxies/                       # ProxyEndpoint definitions
│   └── default.xml
├── targets/                       # TargetEndpoint definitions
│   └── default.xml
├── policies/                      # All policy XML files
│   ├── AM-SetHeaders.xml
│   ├── EV-ExtractPath.xml
│   └── ...
└── resources/                     # Custom code and resources
    ├── jsc/                       # JavaScript files
    ├── java/                      # Java JAR files
    └── xsl/                       # XSLT transformations
```

### Policy Naming Conventions

Follow the `[Abbreviation]-[Purpose].xml` pattern from [GoogleCloudPlatform/apigee-samples](https://github.com/GoogleCloudPlatform/apigee-samples):

| Abbreviation | Policy Type | Example |
|---|---|---|
| AM | AssignMessage | `AM-SetHeaders.xml` |
| EV | ExtractVariables | `EV-ExtractUserId.xml` |
| SC | ServiceCallout | `SC-CallBackend.xml` |
| RF | RaiseFault | `RF-InvalidInput.xml` |
| FC | FlowCallout | `FC-AuthSharedFlow.xml` |
| SA | SpikeArrest | `SA-ProtectBackend.xml` |
| Q | Quota | `Q-DailyLimit.xml` |
| RC | ResponseCache | `RC-CacheResponse.xml` |
| LC | LookupCache | `LC-GetCachedValue.xml` |
| PC | PopulateCache | `PC-StoreValue.xml` |
| IC | InvalidateCache | `IC-ClearCache.xml` |
| KVM | KeyValueMapOperations | `KVM-GetConfig.xml` |
| JS | JavaScript | `JS-TransformResponse.xml` |
| JWT | JWT policies | `JWT-GenerateToken.xml` |
| OAuth | OAuthV2 | `OAuth-VerifyToken.xml` |
| VAK | VerifyAPIKey | `VAK-CheckKey.xml` |
| ML | MessageLogging | `ML-LogToCloud.xml` |
| DC | DataCapture | `DC-CaptureMetrics.xml` |
| CORS | CORS | `CORS-AllowOrigins.xml` |
| JTP | JSONThreatProtection | `JTP-ValidatePayload.xml` |
| XTP | XMLThreatProtection | `XTP-ValidateXML.xml` |
| OAS | OASValidation | `OAS-ValidateRequest.xml` |

See [proxy_bundle_anatomy.md](./references/proxy_bundle_anatomy.md) for full details.

## Development Workflow

### Phase 1: Define Proxy Structure

1. Create the `apiproxy/` directory with root XML, `proxies/`, `targets/`, `policies/`
2. Configure ProxyEndpoint: set BasePath, define HTTPProxyConnection
3. Configure TargetEndpoint: set backend URL or LoadBalancer
4. Set up RouteRules to connect proxy to target

Reference: [proxy_bundle_anatomy.md](./references/proxy_bundle_anatomy.md), [endpoints_and_routing.md](./references/endpoints_and_routing.md)

### Phase 2: Design Flow Pipeline

1. Map API operations to conditional flows using verb + path conditions
2. Place security policies in PreFlow (execute for every request)
3. Place business logic in conditional flows (execute per operation)
4. Place response headers and caching in PostFlow
5. Place MessageLogging in PostClientFlow (guarantees execution even on fault — PostFlow is skipped if proxy errors before reaching it)

Reference: [flows_and_execution.md](./references/flows_and_execution.md), [flow_variables_and_conditions.md](./references/flow_variables_and_conditions.md)

### Phase 3: Implement Policies

Follow this ordering within flows — security first, then mediation, then traffic:

1. **Security**: VerifyAPIKey, OAuthV2, VerifyJWT, AccessControl, threat protection
2. **Mediation**: ExtractVariables, AssignMessage, transformations
3. **Traffic management**: SpikeArrest, Quota
4. **Caching**: ResponseCache (typically in PostFlow response)
5. **Logging**: MessageLogging (typically in PostClientFlow)

Reference: [policies_security.md](./references/policies_security.md), [policies_mediation.md](./references/policies_mediation.md), [policies_traffic_management.md](./references/policies_traffic_management.md), [policies_caching.md](./references/policies_caching.md), [policies_integration.md](./references/policies_integration.md)

### Phase 4: Add Fault Handling

1. Define FaultRules for known error types (auth failures, quota exceeded, backend errors)
2. Add DefaultFaultRule as catch-all with consistent error format
3. Use RaiseFault for custom validation errors
4. Set `continueOnError` only for policies where failure is acceptable

Reference: [fault_handling.md](./references/fault_handling.md)

### Phase 5: Optimize and Extend

1. Extract reusable policy sequences into shared flows
2. Add response caching where appropriate
3. Consider advanced patterns: proxy chaining, composite APIs, circuit breakers
4. Add JavaScript callouts for complex transformations only when policies don't suffice

Reference: [shared_flows.md](./references/shared_flows.md), [javascript_development.md](./references/javascript_development.md), [advanced_patterns.md](./references/advanced_patterns.md), [anti_patterns_and_best_practices.md](./references/anti_patterns_and_best_practices.md)

## Flow Execution Model

```
CLIENT REQUEST
     │
     ▼
┌─────────────────────────────────────────────────┐
│  PROXY ENDPOINT                                 │
│  ┌──────────┐  ┌────────────────┐  ┌─────────┐ │
│  │ PreFlow  │→ │ Conditional    │→ │PostFlow │ │
│  │ (Request)│  │ Flows (Request)│  │(Request)│ │
│  └──────────┘  └────────────────┘  └─────────┘ │
│                                                 │
│  RouteRule evaluation → select TargetEndpoint   │
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│  TARGET ENDPOINT                                │
│  ┌──────────┐  ┌────────────────┐  ┌─────────┐ │
│  │ PreFlow  │→ │ Conditional    │→ │PostFlow │ │
│  │ (Request)│  │ Flows (Request)│  │(Request)│ │
│  └──────────┘  └────────────────┘  └─────────┘ │
└─────────────────────────────────────────────────┘
     │
     ▼
  BACKEND SERVICE (request sent, response received)
     │
     ▼
┌─────────────────────────────────────────────────┐
│  TARGET ENDPOINT                                │
│  ┌──────────┐  ┌─────────────────┐ ┌─────────┐ │
│  │ PreFlow  │→ │ Conditional     │→│PostFlow │ │
│  │(Response)│  │ Flows (Response)│ │(Response│ │
│  └──────────┘  └─────────────────┘ └─────────┘ │
└─────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────┐
│  PROXY ENDPOINT                                 │
│  ┌──────────┐  ┌─────────────────┐ ┌─────────┐ │
│  │ PreFlow  │→ │ Conditional     │→│PostFlow │ │
│  │(Response)│  │ Flows (Response)│ │(Response│ │
│  └──────────┘  └─────────────────┘ └─────────┘ │
└─────────────────────────────────────────────────┘
     │
     ▼
CLIENT RESPONSE SENT
     │
     ▼
┌─────────────────────────────────────────────────┐
│  PostClientFlow (async — after response sent)   │
│  Only: MessageLogging, FlowCallout              │
└─────────────────────────────────────────────────┘
```

**Key rules:**
- **Conditional flows**: Only the FIRST flow whose condition evaluates to true executes. Order matters.
- **PostClientFlow**: Executes even if the proxy errored. Only MessageLogging and FlowCallout policies allowed.
- **FaultRules**: Execute when a policy raises a fault. Skip remaining flow steps and enter error flow.

## Policy Catalog

### Traffic Management
| Policy | Purpose | Reference |
|---|---|---|
| SpikeArrest | Throttle request rate to protect backends | [policies_traffic_management.md](./references/policies_traffic_management.md) |
| Quota | Enforce consumption limits over time periods | [policies_traffic_management.md](./references/policies_traffic_management.md) |
| ResetQuota | Dynamically adjust quota counters mid-cycle | [policies_traffic_management.md](./references/policies_traffic_management.md) |

### Caching
| Policy | Purpose | Reference |
|---|---|---|
| ResponseCache | Cache backend responses by request attributes | [policies_caching.md](./references/policies_caching.md) |
| LookupCache | Retrieve values from general-purpose cache | [policies_caching.md](./references/policies_caching.md) |
| PopulateCache | Store values in general-purpose cache | [policies_caching.md](./references/policies_caching.md) |
| InvalidateCache | Remove entries from cache | [policies_caching.md](./references/policies_caching.md) |

### Security
| Policy | Purpose | Reference |
|---|---|---|
| VerifyAPIKey | Validate API key from header or query param | [policies_security.md](./references/policies_security.md) |
| BasicAuthentication | Encode/decode Base64 Basic auth credentials | [policies_security.md](./references/policies_security.md) |
| OAuthV2 | Generate/verify OAuth 2.0 tokens | [policies_security.md](./references/policies_security.md) |
| GenerateJWT | Create signed or encrypted JWT tokens | [policies_security.md](./references/policies_security.md) |
| VerifyJWT | Validate JWT signatures and claims | [policies_security.md](./references/policies_security.md) |
| DecodeJWT | Decode JWT without signature verification | [policies_security.md](./references/policies_security.md) |
| HMAC | Compute/verify hash-based message auth codes | [policies_security.md](./references/policies_security.md) |
| CORS | Enable cross-origin resource sharing | [policies_security.md](./references/policies_security.md) |
| AccessControl | IP-based allow/deny rules | [policies_security.md](./references/policies_security.md) |
| VerifyIAM | Google Cloud IAM-based authorization | [policies_security.md](./references/policies_security.md) |
| JSONThreatProtection | Protect against malicious JSON payloads | [policies_security.md](./references/policies_security.md) |
| XMLThreatProtection | Protect against malicious XML payloads | [policies_security.md](./references/policies_security.md) |

### Mediation
| Policy | Purpose | Reference |
|---|---|---|
| AssignMessage | Modify/create request or response messages | [policies_mediation.md](./references/policies_mediation.md) |
| ExtractVariables | Extract content from messages into variables | [policies_mediation.md](./references/policies_mediation.md) |
| HTTPModifier | Add/remove/set HTTP headers and params | [policies_mediation.md](./references/policies_mediation.md) |
| XMLtoJSON | Convert XML payloads to JSON | [policies_mediation.md](./references/policies_mediation.md) |
| JSONtoXML | Convert JSON payloads to XML | [policies_mediation.md](./references/policies_mediation.md) |
| JavaScript | Execute custom JavaScript code | [javascript_development.md](./references/javascript_development.md) |

### Integration & Extension
| Policy | Purpose | Reference |
|---|---|---|
| ServiceCallout | Call external REST services during flow | [policies_integration.md](./references/policies_integration.md) |
| FlowCallout | Invoke a shared flow | [policies_integration.md](./references/policies_integration.md) |
| ExternalCallout | Send gRPC requests to external servers | [policies_integration.md](./references/policies_integration.md) |
| KeyValueMapOperations | Read/write key-value map entries | [policies_integration.md](./references/policies_integration.md) |
| ReadPropertySet | Read property set values into variables | [policies_integration.md](./references/policies_integration.md) |
| AccessEntity | Look up entity profiles at runtime | [policies_integration.md](./references/policies_integration.md) |
| RaiseFault | Generate custom fault responses | [fault_handling.md](./references/fault_handling.md) |
| AssertCondition | Evaluate conditional statements | [policies_integration.md](./references/policies_integration.md) |
| MessageLogging | Log to Cloud Logging or syslog | [policies_integration.md](./references/policies_integration.md) |
| PublishMessage | Publish to Pub/Sub topics | [policies_integration.md](./references/policies_integration.md) |
| DataCapture | Capture custom analytics data into Data Collectors | [policies_integration.md](./references/policies_integration.md) |

### Validation
| Policy | Purpose | Reference |
|---|---|---|
| OASValidation | Validate against OpenAPI 3.0 specs | [policies_security.md](./references/policies_security.md) |
| GraphQL | Parse and validate GraphQL payloads | [policies_security.md](./references/policies_security.md) |

### AI/LLM
| Policy | Purpose | Reference |
|---|---|---|
| LLMTokenQuota | Enforce token consumption limits | [advanced_patterns.md](./references/advanced_patterns.md) |
| PromptTokenLimit | Throttle token consumption per request | [advanced_patterns.md](./references/advanced_patterns.md) |
| SanitizeUserPrompt | Filter harmful content from prompts | [advanced_patterns.md](./references/advanced_patterns.md) |
| SanitizeModelResponse | Filter harmful content from LLM responses | [advanced_patterns.md](./references/advanced_patterns.md) |
| SemanticCacheLookup | Semantic similarity cache lookup | [advanced_patterns.md](./references/advanced_patterns.md) |
| SemanticCachePopulate | Cache responses by semantic similarity | [advanced_patterns.md](./references/advanced_patterns.md) |

## Reference Documentation

| Document | Description |
|---|---|
| [proxy_bundle_anatomy.md](./references/proxy_bundle_anatomy.md) | Bundle directory structure, file types, naming conventions |
| [endpoints_and_routing.md](./references/endpoints_and_routing.md) | ProxyEndpoint, TargetEndpoint, RouteRules, proxy chaining |
| [flows_and_execution.md](./references/flows_and_execution.md) | Flow pipeline, PreFlow/PostFlow/conditional flows, execution order |
| [flow_variables_and_conditions.md](./references/flow_variables_and_conditions.md) | Variable system, conditions syntax, message templates |
| [policies_traffic_management.md](./references/policies_traffic_management.md) | SpikeArrest, Quota, ResetQuota |
| [policies_caching.md](./references/policies_caching.md) | ResponseCache, cache-aside pattern, PopulateCache, LookupCache, InvalidateCache |
| [policies_security.md](./references/policies_security.md) | API keys, OAuth 2.0, JWT, CORS, threat protection, IAM |
| [policies_mediation.md](./references/policies_mediation.md) | AssignMessage, ExtractVariables, JSON/XML transforms |
| [policies_integration.md](./references/policies_integration.md) | ServiceCallout, FlowCallout, KVM deep dive, PropertySets, logging, RaiseFault |
| [load_balancing_and_routing.md](./references/load_balancing_and_routing.md) | Target servers, load balancing algorithms, health monitors, advanced routing |
| [fault_handling.md](./references/fault_handling.md) | FaultRules, DefaultFaultRule, error flows, error responses |
| [javascript_development.md](./references/javascript_development.md) | JavaScript object model, patterns, best practices |
| [shared_flows.md](./references/shared_flows.md) | Creating and consuming shared flows, flow hooks |
| [advanced_patterns.md](./references/advanced_patterns.md) | Proxy chaining, composite APIs, circuit breaker, AI/LLM |
| [anti_patterns_and_best_practices.md](./references/anti_patterns_and_best_practices.md) | Common mistakes, production best practices |
| [debugging_and_performance.md](./references/debugging_and_performance.md) | Debug sessions, trace methodology, performance optimization |
| [multi_tenant_patterns.md](./references/multi_tenant_patterns.md) | Multi-tenant routing, isolation, per-tenant config and rate limiting |
| [websockets_and_streaming.md](./references/websockets_and_streaming.md) | WebSocket proxying, SSE, HTTP streaming, timeout gotchas |
| [end_to_end_examples.md](./references/end_to_end_examples.md) | 4 complete proxy bundle walkthroughs |

## Quick Start: Minimal Proxy Bundle

### apiproxy/MinimalProxy.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<APIProxy name="MinimalProxy" revision="1">
  <DisplayName>Minimal Proxy</DisplayName>
  <Description>Simple passthrough proxy</Description>
</APIProxy>
```

### apiproxy/proxies/default.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProxyEndpoint name="default">
  <HTTPProxyConnection>
    <BasePath>/v1/minimal</BasePath>
  </HTTPProxyConnection>

  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>

  <Flows/>

  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>

  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

### apiproxy/targets/default.xml
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <URL>https://mocktarget.apigee.net</URL>
  </HTTPTargetConnection>

  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>

  <Flows/>

  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
</TargetEndpoint>
```

## Common Development Recipes

### Add API Key Protection
Add VerifyAPIKey to PreFlow — all requests must include a valid key:
```xml
<PreFlow name="PreFlow">
  <Request>
    <Step>
      <Name>VAK-VerifyKey</Name>
    </Step>
  </Request>
</PreFlow>
```
See [policies_security.md](./references/policies_security.md) for VerifyAPIKey policy XML.

### Add OAuth 2.0
Create a token endpoint flow + verify tokens on resource flows:
```xml
<Flow name="token">
  <Condition>(proxy.pathsuffix MatchesPath "/token") and (request.verb = "POST")</Condition>
  <Request>
    <Step><Name>OAuth-GenerateToken</Name></Step>
  </Request>
</Flow>
<Flow name="protected-resource">
  <Condition>proxy.pathsuffix MatchesPath "/resource"</Condition>
  <Request>
    <Step><Name>OAuth-VerifyToken</Name></Step>
  </Request>
</Flow>
```
See [policies_security.md](./references/policies_security.md) for OAuthV2 policy configuration.

### Add Rate Limiting
Combine SpikeArrest (protection) with Quota (SLA enforcement):
```xml
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>SA-ProtectBackend</Name></Step>
    <Step><Name>Q-DailyLimit</Name></Step>
  </Request>
</PreFlow>
```
See [policies_traffic_management.md](./references/policies_traffic_management.md).

### Add Response Caching
Place ResponseCache in the flow — it handles both lookup and population:
```xml
<PostFlow name="PostFlow">
  <Response>
    <Step><Name>RC-CacheResponse</Name></Step>
  </Response>
</PostFlow>
```
See [policies_caching.md](./references/policies_caching.md).

### Add CORS
Attach CORS policy in PreFlow to handle preflight and response headers:
```xml
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>CORS-AllowOrigins</Name></Step>
  </Request>
</PreFlow>
```
See [policies_security.md](./references/policies_security.md) for CORS policy XML.

### Call an External Service
Use ServiceCallout to call external APIs during request processing:
```xml
<Flow name="enrich-request">
  <Request>
    <Step><Name>SC-GetUserProfile</Name></Step>
    <Step><Name>EV-ExtractProfile</Name></Step>
  </Request>
</Flow>
```
See [policies_integration.md](./references/policies_integration.md).

### Build Consistent Error Responses
Add FaultRules + DefaultFaultRule to ProxyEndpoint:
```xml
<FaultRules>
  <FaultRule name="auth-error">
    <Condition>fault.name = "FailedToResolveAPIKey"</Condition>
    <Step><Name>AM-AuthError</Name></Step>
  </FaultRule>
</FaultRules>
<DefaultFaultRule>
  <AlwaysEnforce>true</AlwaysEnforce>
  <Step><Name>AM-GenericError</Name></Step>
</DefaultFaultRule>
```
See [fault_handling.md](./references/fault_handling.md).

### Create and Use a Shared Flow
Extract reusable logic into a shared flow, invoke via FlowCallout:
```xml
<!-- In consuming proxy -->
<PreFlow name="PreFlow">
  <Request>
    <Step><Name>FC-AuthSharedFlow</Name></Step>
  </Request>
</PreFlow>
```
See [shared_flows.md](./references/shared_flows.md).

## Best Practices Summary

- **Policy ordering**: Security (PreFlow) → Mediation → Traffic management → Caching (PostFlow) → Logging (PostClientFlow)
- **Naming**: Always use `[Abbreviation]-[Purpose].xml` for policy files
- **Policies over code**: Use built-in policies first; only use JavaScript for logic that policies cannot express
- **Fault handling**: Every proxy should have a DefaultFaultRule with a consistent error response format
- **Shared flows**: Extract any policy sequence used in 2+ proxies into a shared flow
- **Base paths**: Use versioned paths (`/v1/resource`) and ensure uniqueness per environment
- **Conditions**: Place the most specific conditional flows first (first match wins)
- **PostClientFlow**: Always use for MessageLogging to guarantee execution regardless of errors
- **Caching**: Set `ExcludeErrorResponse` to true on ResponseCache to avoid caching error responses
- **Large payloads**: Minimize policies that parse large payloads; enable streaming for passthrough scenarios
- **Anti-patterns**: See [anti_patterns_and_best_practices.md](./references/anti_patterns_and_best_practices.md) for the complete catalog
