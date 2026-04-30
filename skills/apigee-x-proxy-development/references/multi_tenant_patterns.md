# Multi-Tenant Isolation Patterns

## Overview

Multi-tenant API proxies serve multiple customers or organizations through a single proxy deployment, with tenant-specific routing, rate limiting, configuration, and data isolation. This pattern reduces operational overhead while maintaining strict separation between tenants.

## Tenant Identification

### From HTTP Header

```xml
<ExtractVariables name="EV-ExtractTenant">
  <Source>request</Source>
  <Header name="X-Tenant-ID">
    <Pattern>{tenant.id}</Pattern>
  </Header>
  <VariablePrefix>extracted</VariablePrefix>
</ExtractVariables>
```

### From JWT Claim

After VerifyJWT, the tenant is available as a decoded claim:

```xml
<VerifyJWT name="JWT-VerifyToken">
  <Algorithm>RS256</Algorithm>
  <Source>request.header.Authorization</Source>
  <PublicKey>
    <JWKS uri="https://auth.example.com/.well-known/jwks.json"/>
  </PublicKey>
  <AdditionalClaims>
    <Claim name="tenant_id" type="string"/>
  </AdditionalClaims>
</VerifyJWT>
```

Access tenant via: `jwt.JWT-VerifyToken.decoded.claim.tenant_id`

### From API Key / API Product

After VerifyAPIKey, use custom attributes on the API product or developer app:

```xml
<VerifyAPIKey name="VAK-VerifyKey">
  <APIKey ref="request.header.x-api-key"/>
</VerifyAPIKey>
```

Access tenant via product custom attribute: `verifyapikey.VAK-VerifyKey.apiproduct.tenant_id`

This requires setting `tenant_id` as a custom attribute on the API product in Apigee.

### From Path Segment

```xml
<ExtractVariables name="EV-TenantFromPath">
  <Source>request</Source>
  <URIPath>
    <Pattern>/tenants/{tenant.id}/**</Pattern>
  </URIPath>
  <VariablePrefix>path</VariablePrefix>
</ExtractVariables>
```

## Tenant-Specific Routing

Route to different backends per tenant using conditional RouteRules:

```xml
<RouteRule name="tenant-acme">
  <Condition>extracted.tenant.id = "acme"</Condition>
  <TargetEndpoint>AcmeBackend</TargetEndpoint>
</RouteRule>
<RouteRule name="tenant-globex">
  <Condition>extracted.tenant.id = "globex"</Condition>
  <TargetEndpoint>GlobexBackend</TargetEndpoint>
</RouteRule>
<RouteRule name="default">
  <TargetEndpoint>SharedBackend</TargetEndpoint>
</RouteRule>
```

### Dynamic Routing via KVM

For many tenants, use KVM lookup instead of hardcoded RouteRules:

```xml
<!-- Step 1: Look up tenant's backend URL from KVM -->
<KeyValueMapOperations name="KVM-GetTenantBackend" mapIdentifier="tenant-backends">
  <Scope>environment</Scope>
  <Get assignTo="private.kvm.tenantBackendUrl">
    <Key>
      <Parameter ref="extracted.tenant.id"/>
    </Key>
  </Get>
</KeyValueMapOperations>

<!-- Step 2: Set target URL dynamically -->
<AssignMessage name="AM-SetTenantTarget">
  <AssignVariable>
    <Name>target.url</Name>
    <Ref>private.kvm.tenantBackendUrl</Ref>
    <Value>https://default-backend.example.com</Value>
  </AssignVariable>
</AssignMessage>
```

This scales to hundreds of tenants without proxy redeployment. Add new tenants by adding KVM entries.

## Tenant-Specific Rate Limiting

Use tenant ID as the Quota Identifier for per-tenant counters:

```xml
<Quota name="Q-TenantQuota">
  <Allow countRef="kvm.tenant.quota.limit" count="1000"/>
  <Interval>1</Interval>
  <TimeUnit>day</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <Identifier ref="extracted.tenant.id"/>
</Quota>
```

Each tenant gets its own independent quota counter. Use `countRef` to load limits from KVM per tenant so different tenants can have different quotas.

### Tiered Rate Limiting

Apply different limits per tier using conditional flows:

```xml
<Flow name="premium-quota">
  <Condition>verifyapikey.VAK-VerifyKey.apiproduct.tier = "premium"</Condition>
  <Request>
    <Step><Name>Q-PremiumQuota</Name></Step>
  </Request>
</Flow>
<Flow name="standard-quota">
  <Request>
    <Step><Name>Q-StandardQuota</Name></Step>
  </Request>
</Flow>
```

## Tenant-Specific Configuration

### KVM Per-Tenant Pattern

Store tenant-specific settings in an environment KVM with compound keys:

```xml
<KeyValueMapOperations name="KVM-GetTenantConfig" mapIdentifier="tenant-config">
  <Scope>environment</Scope>
  <Get assignTo="kvm.tenant.timeout">
    <Key>
      <Parameter ref="extracted.tenant.id"/>
      <Parameter>timeout</Parameter>
    </Key>
  </Get>
  <Get assignTo="kvm.tenant.maxPayloadSize">
    <Key>
      <Parameter ref="extracted.tenant.id"/>
      <Parameter>maxPayloadSize</Parameter>
    </Key>
  </Get>
</KeyValueMapOperations>
```

### Property Set for Tenant Defaults

Use property sets for default values and KVM for tenant-specific overrides:

```xml
<AssignMessage name="AM-LoadDefaults">
  <AssignVariable>
    <Name>config.timeout</Name>
    <Value>{propertyset.defaults.timeout}</Value>
  </AssignVariable>
</AssignMessage>

<!-- KVM overrides defaults when a tenant-specific value exists -->
<AssignMessage name="AM-ApplyTenantOverrides">
  <AssignVariable>
    <Name>config.timeout</Name>
    <Ref>kvm.tenant.timeout</Ref>
    <Value>{config.timeout}</Value>
  </AssignVariable>
</AssignMessage>
```

The `<Value>` element acts as a fallback -- if `kvm.tenant.timeout` is not set, the existing default is preserved.

## Tenant Data Isolation

### Cross-Tenant Access Prevention

Validate that the authenticated tenant matches the requested resource:

```javascript
// JS-ValidateTenantAccess.js
var authTenant = context.getVariable("jwt.JWT-VerifyToken.decoded.claim.tenant_id");
var resourceTenant = context.getVariable("path.tenant.id");

if (authTenant !== resourceTenant) {
  context.setVariable("custom.error.code", "FORBIDDEN");
  context.setVariable("custom.error.message",
    "Tenant " + authTenant + " cannot access resources of tenant " + resourceTenant);
  context.setVariable("custom.raiseError", "true");
}
```

Follow with a conditional RaiseFault in the flow:

```xml
<Step><Name>JS-ValidateTenantAccess</Name></Step>
<Step>
  <Condition>custom.raiseError = "true"</Condition>
  <Name>RF-Forbidden</Name>
</Step>
```

Where `RF-Forbidden` is defined as:

```xml
<RaiseFault name="RF-Forbidden">
  <FaultResponse>
    <Set>
      <StatusCode>403</StatusCode>
      <ReasonPhrase>Forbidden</ReasonPhrase>
      <Payload contentType="application/json">
        {"error":{"code":403,"message":"{custom.error.message}","status":"FORBIDDEN"}}
      </Payload>
    </Set>
  </FaultResponse>
</RaiseFault>
```

### Shared Flow for Tenant Validation

Extract tenant validation into a shared flow for reuse across proxies:

```xml
<FlowCallout name="FC-ValidateTenant">
  <SharedFlowBundle>tenant-validation-sf</SharedFlowBundle>
  <Parameters>
    <Parameter name="expected_tenant">{path.tenant.id}</Parameter>
  </Parameters>
</FlowCallout>
```

## Tenant-Aware Logging and Analytics

### MessageLogging with Tenant Context

```xml
<MessageLogging name="ML-TenantLog">
  <CloudLogging>
    <LogName>projects/{organization.name}/logs/api-tenant-audit</LogName>
    <Message contentType="application/json">
      {"tenantId":"{extracted.tenant.id}","verb":"{request.verb}","path":"{request.path}","status":"{response.status.code}","requestId":"{system.uuid}"}
    </Message>
    <Labels>
      <Label><Key>tenant</Key><Value>{extracted.tenant.id}</Value></Label>
      <Label><Key>proxy</Key><Value>{apiproxy.name}</Value></Label>
    </Labels>
    <ResourceType>api</ResourceType>
  </CloudLogging>
</MessageLogging>
```

### DataCapture for Per-Tenant Analytics

```xml
<DataCapture name="DC-TenantMetrics">
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <Capture>
    <DataCollector>dc_tenant_id</DataCollector>
    <Collect ref="extracted.tenant.id" default="unknown"/>
  </Capture>
  <Capture>
    <DataCollector>dc_tenant_tier</DataCollector>
    <Collect ref="verifyapikey.VAK-VerifyKey.apiproduct.tier" default="standard"/>
  </Capture>
</DataCapture>
```

Create custom reports in Apigee Analytics grouped by `dc_tenant_id` to view per-tenant traffic, latency, and error rates.

## Complete Multi-Tenant ProxyEndpoint Example

The following ProxyEndpoint combines tenant extraction, authentication, KVM-based configuration and routing, per-tenant quota, cross-tenant access prevention, and tenant-aware logging:

```xml
<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request>
      <!-- 1. Extract tenant from header -->
      <Step><Name>EV-ExtractTenant</Name></Step>
      <!-- 2. Authenticate via API key -->
      <Step><Name>VAK-VerifyKey</Name></Step>
      <!-- 3. Load tenant config from KVM -->
      <Step><Name>KVM-GetTenantConfig</Name></Step>
      <!-- 4. Load tenant backend URL from KVM -->
      <Step><Name>KVM-GetTenantBackend</Name></Step>
      <!-- 5. Apply per-tenant quota -->
      <Step><Name>Q-TenantQuota</Name></Step>
      <!-- 6. Validate cross-tenant access -->
      <Step><Name>JS-ValidateTenantAccess</Name></Step>
      <Step>
        <Condition>custom.raiseError = "true"</Condition>
        <Name>RF-Forbidden</Name>
      </Step>
      <!-- 7. Set dynamic target URL -->
      <Step><Name>AM-SetTenantTarget</Name></Step>
    </Request>
  </PreFlow>

  <Flows>
    <Flow name="get-resources">
      <Condition>(proxy.pathsuffix MatchesPath "/resources") and (request.verb = "GET")</Condition>
      <Request/>
      <Response>
        <Step><Name>DC-TenantMetrics</Name></Step>
      </Response>
    </Flow>
  </Flows>

  <PostFlow name="PostFlow">
    <Response>
      <Step><Name>AM-AddTenantResponseHeaders</Name></Step>
    </Response>
  </PostFlow>

  <PostClientFlow name="PostClientFlow">
    <Response>
      <Step><Name>ML-TenantLog</Name></Step>
    </Response>
  </PostClientFlow>

  <FaultRules>
    <FaultRule name="quota-exceeded">
      <Condition>(fault.name = "QuotaViolation")</Condition>
      <Step><Name>AM-QuotaExceededResponse</Name></Step>
      <Step><Name>ML-TenantLog</Name></Step>
    </FaultRule>
    <FaultRule name="auth-failure">
      <Condition>(fault.name = "InvalidApiKey") or (fault.name = "FailedToResolveAPIKey")</Condition>
      <Step><Name>AM-AuthFailureResponse</Name></Step>
      <Step><Name>ML-TenantLog</Name></Step>
    </FaultRule>
  </FaultRules>

  <DefaultFaultRule name="DefaultFault">
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step><Name>AM-DefaultFaultResponse</Name></Step>
    <Step><Name>ML-TenantLog</Name></Step>
  </DefaultFaultRule>

  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>

  <HTTPProxyConnection>
    <BasePath>/v1/tenants</BasePath>
  </HTTPProxyConnection>
</ProxyEndpoint>
```

In this example, routing is handled dynamically by setting `target.url` in the AM-SetTenantTarget policy rather than using multiple RouteRules. The single RouteRule points to a default TargetEndpoint whose URL gets overridden at runtime.

---

See also:
- [Shared Flows](shared_flows.md) -- reusable tenant validation shared flows
- [Policies: Traffic Management](policies_traffic_management.md) -- Quota and SpikeArrest details
- [Policies: Security](policies_security.md) -- VerifyAPIKey and VerifyJWT configuration
- [Fault Handling](fault_handling.md) -- FaultRules and DefaultFaultRule patterns
- [Flow Variables and Conditions](flow_variables_and_conditions.md) -- variable references used in conditions
- [Advanced Patterns](advanced_patterns.md) -- KVM-based dynamic routing and other advanced techniques
