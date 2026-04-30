# Integration & Extension Policies

## ServiceCallout Policy

Call external REST services or internal API proxies during flow execution. Response stored in a named variable. Set `Timeout` in milliseconds; use `continueOnError="true"` for optional callouts.

### Basic HTTP Callout
```xml
<ServiceCallout name="SC-GetUserProfile">
  <Request clearPayload="false" variable="profileRequest">
    <Set>
      <Verb>GET</Verb>
      <Headers>
        <Header name="Authorization">Bearer {custom.serviceToken}</Header>
        <Header name="Accept">application/json</Header>
      </Headers>
    </Set>
  </Request>
  <Response>profileResponse</Response>
  <Timeout>30000</Timeout>
  <HTTPTargetConnection>
    <URL>https://user-service.example.com/profiles/{custom.userId}</URL>
  </HTTPTargetConnection>
</ServiceCallout>
```

### POST with Payload
```xml
<ServiceCallout name="SC-CreateAuditLog">
  <Request clearPayload="true" variable="auditRequest">
    <Set>
      <Verb>POST</Verb>
      <Headers>
        <Header name="Content-Type">application/json</Header>
      </Headers>
      <Payload contentType="application/json">
        {"action": "{request.verb}", "path": "{proxy.pathsuffix}", "user": "{custom.userId}", "timestamp": "{system.timestamp}"}
      </Payload>
    </Set>
  </Request>
  <Response>auditResponse</Response>
  <Timeout>5000</Timeout>
  <HTTPTargetConnection>
    <URL>https://audit.example.com/log</URL>
  </HTTPTargetConnection>
</ServiceCallout>
```

### Accessing the Response
Access via the variable name in `<Response>`: `{profileResponse.status.code}` (HTTP status), `{profileResponse.content}` (body), `{profileResponse.header.Content-Type}` (headers). Use ExtractVariables or JavaScript to parse the body.

### Multiple Callouts with Aggregation
```xml
<!-- Sequential callouts followed by aggregation -->
<Step><Name>SC-UserService</Name></Step>
<Step><Name>SC-OrderService</Name></Step>
<Step><Name>JS-AggregateResponses</Name></Step>
```
```javascript
var users = JSON.parse(context.getVariable("userResponse.content"));
var orders = JSON.parse(context.getVariable("orderResponse.content"));
var aggregate = { users: users, orders: orders, timestamp: Date.now() };
context.setVariable("response.content", JSON.stringify(aggregate));
context.setVariable("response.header.Content-Type", "application/json");
```

## FlowCallout Policy

Invoke a shared flow from within a proxy. The shared flow must be deployed before the consuming proxy. See `shared_flows.md` for creating shared flows.
```xml
<FlowCallout name="FC-AuthSharedFlow">
  <SharedFlowBundle>auth-shared-flow</SharedFlowBundle>
  <Parameters>
    <Parameter name="expected_scope">{custom.requiredScope}</Parameter>
  </Parameters>
</FlowCallout>
```

## ExternalCallout Policy

Send gRPC requests to external servers for custom processing. The server reads and modifies flow variables.
```xml
<ExternalCallout name="EC-ProcessRequest">
  <GrpcConnection>
    <Server name="my-grpc-server"/>
  </GrpcConnection>
  <TimeoutMs>5000</TimeoutMs>
</ExternalCallout>
```

## KeyValueMapOperations Policy

Read, write, and delete persistent key-value data. KVMs provide runtime-mutable storage for configuration, credentials, and tokens.

### Core Concepts
- `mapIdentifier` attribute: references the KVM by name
- `Scope` element: `organization`, `environment`, or `apiproxy`
- All KVMs in Apigee X are encrypted -- there is no unencrypted option
- Use the `private.` prefix on `assignTo` variables to hide values from debug/trace sessions

### GET Operation
```xml
<KeyValueMapOperations name="KVM-GetConfig" mapIdentifier="api-config">
  <Scope>environment</Scope>
  <ExpiryTimeInSecs>300</ExpiryTimeInSecs>
  <Get assignTo="private.kvm.backendUrl" index="1">
    <Key>
      <Parameter>backendUrl</Parameter>
    </Key>
  </Get>
</KeyValueMapOperations>
```
- `assignTo`: flow variable to store the retrieved value. Use `private.` prefix for sensitive data so values are masked in trace sessions
- `index`: 1-based index for multi-valued keys (default: 1)
- `ExpiryTimeInSecs`: how long to cache KVM values in memory. This is NOT an entry TTL -- KVM entries never expire. It controls how often the runtime re-reads from the backing store

### PUT Operation
```xml
<KeyValueMapOperations name="KVM-StoreToken" mapIdentifier="tokens">
  <Scope>environment</Scope>
  <Put override="true">
    <Key>
      <Parameter ref="custom.tokenKey"/>
    </Key>
    <Value ref="custom.tokenValue"/>
  </Put>
</KeyValueMapOperations>
```
- `override="true"`: overwrite existing value. Default is `false`, which only creates new entries and leaves existing entries unchanged

### DELETE Operation
```xml
<KeyValueMapOperations name="KVM-DeleteEntry" mapIdentifier="tokens">
  <Scope>environment</Scope>
  <Delete>
    <Key>
      <Parameter ref="request.header.x-token-id"/>
    </Key>
  </Delete>
</KeyValueMapOperations>
```

### InitialEntries -- Seed Data on Deployment
```xml
<KeyValueMapOperations name="KVM-Init" mapIdentifier="defaults">
  <Scope>apiproxy</Scope>
  <InitialEntries>
    <Entry>
      <Key><Parameter>timeout</Parameter></Key>
      <Value>30000</Value>
    </Entry>
    <Entry>
      <Key><Parameter>retries</Parameter></Key>
      <Value>3</Value>
    </Entry>
  </InitialEntries>
  <Get assignTo="kvm.timeout">
    <Key><Parameter>timeout</Parameter></Key>
  </Get>
</KeyValueMapOperations>
```
- Entries are created when the proxy is first deployed
- Existing entries are NOT overwritten on redeployment
- Combine `InitialEntries` with `Get` in the same policy to seed defaults and read them in one step

### Dynamic Keys from Flow Variables
Use the `ref` attribute on `<Parameter>` and `<Value>` elements to resolve keys and values from flow variables at runtime:
```xml
<KeyValueMapOperations name="KVM-DynamicGet" mapIdentifier="tenant-config">
  <Scope>environment</Scope>
  <Get assignTo="private.kvm.tenantSecret">
    <Key>
      <Parameter ref="request.header.X-Tenant-ID"/>
    </Key>
  </Get>
</KeyValueMapOperations>
```
```xml
<KeyValueMapOperations name="KVM-DynamicPut" mapIdentifier="session-store">
  <Scope>environment</Scope>
  <Put override="true">
    <Key>
      <Parameter ref="custom.sessionId"/>
    </Key>
    <Value ref="custom.sessionPayload"/>
  </Put>
</KeyValueMapOperations>
```

### KVM Limits
| Resource | Limit |
|---|---|
| Key size | 2 KB |
| Value size | 10 KB |
| Total items per org | 5 million |
| KVMs per org (org-scoped) | 100 |
| KVMs per env (env-scoped) | 900 |

### KVM Scopes -- When to Use Each
- **Organization**: global settings shared across ALL environments. Use for org-wide constants that rarely change
- **Environment**: env-specific configuration such as dev/staging/prod credentials, backend URLs, and feature toggles. This is the most commonly used scope
- **API Proxy**: proxy-specific data isolated to a single proxy. Use for proxy-local state like session tokens or per-proxy defaults

### KVM from JavaScript
KVM data cannot be accessed directly from JavaScript callouts. The pattern is to use a KVM policy first to load values into flow variables, then read those variables from JavaScript:
```xml
<!-- Step 1: KVM policy loads value into a flow variable -->
<Step><Name>KVM-GetSecret</Name></Step>
<!-- Step 2: JavaScript reads the flow variable -->
<Step><Name>JS-UseSecret</Name></Step>
```
```javascript
// In JS-UseSecret.js
var secret = context.getVariable("private.kvm.secret");
// Use the secret for HMAC signing, header construction, etc.
```

## Property Sets

Static configuration deployed with the proxy bundle. Lighter weight than KVM for read-only values that change only at deployment time.

### Property Set File Format
Property set files live in the proxy bundle and use standard Java `.properties` format:
```
apiproxy/resources/properties/
  app-config.properties      # Proxy-scoped property set
```
File content:
```properties
backend.url=https://api.example.com
cache.ttl=3600
feature.analytics=true
max.retries=3
```

### Accessing Property Sets -- Two Ways

**1. Direct flow variable access (no policy needed):**
```xml
<AssignMessage name="AM-SetTarget">
  <Set>
    <Headers>
      <Header name="X-Backend">{propertyset.app-config.backend.url}</Header>
    </Headers>
  </Set>
</AssignMessage>
```
Syntax: `propertyset.{filename-without-extension}.{key}`

This works anywhere flow variables are supported -- conditions, policy attributes, message templates.

**2. ReadPropertySet policy (for defaults and dynamic keys):**
```xml
<ReadPropertySet name="RPS-GetConfig">
  <Read>
    <Name>app-config</Name>
    <Key>backend.url</Key>
    <AssignTo>target.backend.url</AssignTo>
    <DefaultValue>https://fallback.example.com</DefaultValue>
  </Read>
  <Read>
    <Name ref="request.header.X-Config-Set">app-config</Name>
    <Key ref="request.queryparam.setting">cache.ttl</Key>
    <AssignTo>custom.cacheTTL</AssignTo>
    <DefaultValue>1800</DefaultValue>
  </Read>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</ReadPropertySet>
```
Use the ReadPropertySet policy when you need default values for missing keys or when the property set name or key is determined dynamically from flow variables via the `ref` attribute.

### Environment-Scoped vs Proxy-Scoped
- **Proxy-scoped**: files in `apiproxy/resources/properties/` bundled with the proxy. Max 50 per proxy. Only accessible by that proxy
- **Environment-scoped**: created via API or UI. Max 10 per environment. Accessible by all proxies deployed to that environment. Useful for shared configuration like environment-specific backend URLs

### Property Set Limits
| Resource | Limit |
|---|---|
| Max per proxy | 50 |
| Max per environment | 10 |
| Max file size | 110 KB per property set |

### KVMs vs Property Sets -- Decision Guide
| Criterion | KVMs | Property Sets |
|---|---|---|
| Mutability | Mutable at runtime | Read-only (redeploy to change) |
| Storage | Platform database | Proxy bundle files |
| Encryption | Always encrypted | Bundle-level access control |
| Max value size | 10 KB | 110 KB per file |
| Use for | Credentials, runtime lookup, tokens | Static config, feature flags, URLs |
| Access method | KeyValueMapOperations policy | Flow variables or ReadPropertySet |
| Performance | Cached with ExpiryTimeInSecs | Always in memory, no cache delay |

## AccessEntity Policy

Retrieve entity profiles from Apigee datastore. Result stored as XML in `AccessEntity.{policy-name}`.
```xml
<AccessEntity name="AE-GetDeveloper">
  <EntityType value="developer"/>
  <EntityIdentifier ref="developer.email" type="email"/>
</AccessEntity>
```
Entity types: `developer`, `app`, `apiproduct`, `consumerkey`, `companydeveloper`.

## RaiseFault Policy

Immediately halt normal flow and transfer control to the error flow.
```xml
<RaiseFault name="RF-InvalidInput">
  <FaultResponse>
    <Set>
      <StatusCode>400</StatusCode>
      <ReasonPhrase>Bad Request</ReasonPhrase>
      <Headers>
        <Header name="Content-Type">application/json</Header>
      </Headers>
      <Payload contentType="application/json">
        {"error": {"code": "INVALID_INPUT", "message": "Required field missing: {custom.missingField}"}}
      </Payload>
    </Set>
  </FaultResponse>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</RaiseFault>
```
Processing jumps to FaultRules. See `fault_handling.md` for the error handling model.

## AssertCondition Policy

Evaluate a condition and store the result without raising a fault.
```xml
<AssertCondition name="AC-CheckAge">
  <Condition>custom.userAge >= 18</Condition>
</AssertCondition>
```
Result in `assertcondition.AC-CheckAge.truthValue` (true/false). Does not raise a fault -- stores the result for downstream decisions.

## MessageLogging Policy

Log structured data to Google Cloud Logging (preferred for Apigee X). Place in PostClientFlow for guaranteed execution.
```xml
<MessageLogging name="ML-LogToCloud">
  <CloudLogging>
    <LogName>projects/{organization.name}/logs/apigee-proxy</LogName>
    <Message contentType="application/json">
      {"requestId": "{system.uuid}", "verb": "{request.verb}", "path": "{request.path}", "status": "{response.status.code}", "latency": "{target.received.end.timestamp - target.received.start.timestamp}"}
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
    </Labels>
    <ResourceType>api</ResourceType>
  </CloudLogging>
</MessageLogging>
```

## PublishMessage Policy

Publish messages to Google Cloud Pub/Sub for event-driven architectures and async processing.
```xml
<PublishMessage name="PM-PublishEvent">
  <Source>{response.content}</Source>
  <CloudPubSub>
    <Topic>projects/my-project/topics/api-events</Topic>
  </CloudPubSub>
</PublishMessage>
```

## DataCapture Policy and Data Collectors

Capture custom analytics data from API traffic. DataCapture collects values into pre-defined **Data Collectors** (schema entities), which feed Apigee Analytics, custom reports, and BigQuery export.

### Prerequisites: Create Data Collectors

Data Collectors define the schema. They must exist BEFORE the DataCapture policy executes. Create via REST API or `apigeecli`:

```bash
# REST API
curl -X POST \
  "https://apigee.googleapis.com/v1/organizations/{org}/datacollectors" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"dc_payment_amount","description":"Transaction amount","type":"FLOAT"}'

# apigeecli
apigeecli datacollectors create -n dc_payment_amount -d "Transaction amount" -p FLOAT -o $ORG -t $TOKEN
```

**Supported types:** STRING, INTEGER, FLOAT, LONG, DOUBLE, BOOLEAN, DATE, DATETIME. Type is immutable after creation.

**Naming:** Must start with `dc_` prefix. Use lowercase with underscores. Do NOT create names differing only by case (causes BigQuery export errors).

### Basic DataCapture — Flow Variable Reference

Capture flow variables directly using `ref`:
```xml
<DataCapture name="DC-CaptureMetrics" continueOnError="false" enabled="true">
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <Capture>
    <DataCollector>dc_response_status</DataCollector>
    <Collect ref="response.status.code" default="0"/>
  </Capture>
  <Capture>
    <DataCollector>dc_client_ip</DataCollector>
    <Collect ref="client.ip" default="unknown"/>
  </Capture>
</DataCapture>
```

- `ref`: flow variable to capture
- `default`: fallback when variable is unresolved
- `IgnoreUnresolvedVariables`: set `true` to prevent policy failure on missing variables
- Multiple `<Capture>` elements allowed, but each must reference a DIFFERENT DataCollector

### DataCapture — JSON Payload Extraction

Extract values from JSON using JSONPath:
```xml
<DataCapture name="DC-CaptureFromJSON">
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <Capture>
    <DataCollector>dc_user_country</DataCollector>
    <Collect>
      <Source>response</Source>
      <JSONPayload>
        <JSONPath>$.user.address.country</JSONPath>
      </JSONPayload>
    </Collect>
  </Capture>
  <Capture>
    <DataCollector>dc_order_total</DataCollector>
    <Collect>
      <Source>response</Source>
      <JSONPayload>
        <JSONPath>$.order.total</JSONPath>
      </JSONPayload>
    </Collect>
  </Capture>
</DataCapture>
```

`<Source>` defaults to `message` (context-aware). Set explicitly to `request` or `response` to be unambiguous.

### DataCapture — Headers, Query Params, URI Path, Form Params

```xml
<DataCapture name="DC-CaptureRequestData">
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <!-- From header -->
  <Capture>
    <DataCollector>dc_api_version</DataCollector>
    <Collect>
      <Header name="X-API-Version">
        <Pattern>{version}</Pattern>
      </Header>
    </Collect>
  </Capture>
  <!-- From query parameter -->
  <Capture>
    <DataCollector>dc_search_term</DataCollector>
    <Collect>
      <QueryParam name="q">
        <Pattern>{term}</Pattern>
      </QueryParam>
    </Collect>
  </Capture>
  <!-- From URI path -->
  <Capture>
    <DataCollector>dc_resource_id</DataCollector>
    <Collect>
      <URIPath>
        <Pattern ignoreCase="true">/resources/{resourceId}</Pattern>
      </URIPath>
    </Collect>
  </Capture>
  <!-- From form parameter -->
  <Capture>
    <DataCollector>dc_payment_currency</DataCollector>
    <Collect>
      <FormParam name="currency">
        <Pattern>{curr}</Pattern>
      </FormParam>
    </Collect>
  </Capture>
</DataCapture>
```

### DataCapture — XML Payload Extraction

```xml
<Capture>
  <DataCollector>dc_transaction_amount</DataCollector>
  <Collect>
    <Source>response</Source>
    <XMLPayload>
      <XPath>/ns:response/ns:transaction/ns:amount</XPath>
      <Namespaces>
        <Namespace prefix="ns">http://api.example.com/v1</Namespace>
      </Namespaces>
    </XMLPayload>
  </Collect>
</Capture>
```

### Flow Placement

Place DataCapture in **response PostFlow** to capture both request and response data:
```xml
<PostFlow name="PostFlow">
  <Response>
    <Step><Name>EV-ExtractMetrics</Name></Step>
    <Step><Name>DC-CaptureMetrics</Name></Step>
  </Response>
</PostFlow>
```

Also works in FaultRules to capture error analytics:
```xml
<FaultRule name="capture-on-error">
  <Condition>error.status.code >= 400</Condition>
  <Step><Name>DC-CaptureErrorMetrics</Name></Step>
</FaultRule>
```

DataCapture is NOT allowed in PostClientFlow (only MessageLogging and FlowCallout there).

### Pattern: ExtractVariables → DataCapture

When you need values in both the proxy flow AND analytics, extract first, then capture:
```xml
<!-- Step 1: Extract into flow variables -->
<Step><Name>EV-ExtractTokenCounts</Name></Step>
<!-- Step 2: Use variables in proxy logic (e.g., quota) -->
<Step><Name>Q-TokenQuota</Name></Step>
<!-- Step 3: Capture same variables for analytics -->
<Step><Name>DC-CollectTokenCounts</Name></Step>
```

The DataCapture policy then captures via `ref`:
```xml
<DataCapture name="DC-CollectTokenCounts">
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <Capture>
    <DataCollector>dc_prompt_token_count</DataCollector>
    <Collect ref="prompt_token_count" default="0"/>
  </Capture>
  <Capture>
    <DataCollector>dc_total_token_count</DataCollector>
    <Collect ref="total_token_count" default="0"/>
  </Capture>
</DataCapture>
```

### Creating Custom Reports from Captured Data

After data is captured (10-minute analytics delay), create reports via API:
```bash
curl -X POST \
  "https://apigee.googleapis.com/v1/organizations/$ORG/reports" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "token-usage-report",
    "displayName": "Token Usage Report",
    "metrics": [
      {"name": "dc_prompt_token_count", "function": "sum"},
      {"name": "dc_total_token_count", "function": "sum"}
    ],
    "dimensions": ["api_product", "developer_app"],
    "chartType": "line"
  }'
```

Metric functions: `sum`, `avg`, `min`, `max`, `count`.

### Data Collector Limits

| Resource | Limit |
|---|---|
| Name prefix | Must start with `dc_` |
| Max variables per capture | 100 |
| Max variable size | 400 bytes |
| Data types | STRING, INTEGER, FLOAT, LONG, DOUBLE, BOOLEAN, DATE, DATETIME |
| Analytics delay | ~10 minutes |
| BigQuery export | Each collector becomes a column |

### Data Flow: Collector → Capture → Analytics → Reports

```
DataCollector (schema: name + type)
    ↓
DataCapture policy (collects matching data at runtime)
    ↓
Apigee Analytics engine (~10 min delay)
    ↓
Custom Reports (dimensions from STRING, metrics from numeric types)
    ↓
BigQuery Export (each collector = one column)
```

---

**Related references:** `fault_handling.md` | `shared_flows.md` | `flows_and_execution.md`
