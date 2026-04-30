# Mediation Policies

Mediation policies transform, enrich, and reshape messages as they flow through the proxy. They handle header manipulation, payload transformation, variable extraction, and format conversion.

## AssignMessage Policy

The Swiss Army knife of Apigee policies. AssignMessage can modify, create, or transform messages using four operations: Set, Add, Remove, and Copy. It can target the current request, current response, or a custom message variable.

### Set Operation (Replace Values)

Replaces existing values or creates them if they do not exist.

```xml
<AssignMessage name="AM-SetBackendHeaders">
  <AssignTo>request</AssignTo>
  <Set>
    <Headers>
      <Header name="X-Forwarded-For">{client.ip}</Header>
      <Header name="X-Request-ID">{system.uuid}</Header>
    </Headers>
    <QueryParams>
      <QueryParam name="format">json</QueryParam>
    </QueryParams>
    <Payload contentType="application/json">
      {"userId": "{custom.userId}", "action": "{request.verb}"}
    </Payload>
    <StatusCode>200</StatusCode>
    <ReasonPhrase>OK</ReasonPhrase>
    <Verb>POST</Verb>
    <Path>/api/v2/process</Path>
  </Set>
</AssignMessage>
```

### Add Operation (Append Values)

Appends values without replacing existing ones. Useful for multi-value headers.

```xml
<AssignMessage name="AM-AddHeaders">
  <AssignTo>response</AssignTo>
  <Add>
    <Headers>
      <Header name="X-Response-Time">{system.timestamp}</Header>
    </Headers>
  </Add>
</AssignMessage>
```

### Remove Operation

Removes headers, query parameters, or form parameters from the message.

```xml
<AssignMessage name="AM-RemoveSensitive">
  <AssignTo>request</AssignTo>
  <Remove>
    <Headers>
      <Header name="X-Internal-Token"/>
    </Headers>
    <QueryParams>
      <QueryParam name="debug"/>
    </QueryParams>
  </Remove>
</AssignMessage>
```

### Copy Operation

Copies elements from one message to another. Commonly used to build a new request for ServiceCallout.

```xml
<AssignMessage name="AM-CopyHeaders">
  <Copy source="request">
    <Headers>
      <Header name="Authorization"/>
    </Headers>
  </Copy>
  <AssignTo createNew="true" transport="http" type="request">backendRequest</AssignTo>
</AssignMessage>
```

### Creating Custom Variables

Use `<AssignVariable>` to set flow variables for use by downstream policies.

```xml
<AssignMessage name="AM-SetVariables">
  <AssignTo createNew="false" transport="http" type="request"/>
  <AssignVariable>
    <Name>custom.startTime</Name>
    <Value>{system.timestamp}</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>custom.clientTier</Name>
    <Ref>apiproduct.name</Ref>
    <Value>standard</Value>
  </AssignVariable>
</AssignMessage>
```

`<Ref>` attempts to read the referenced variable first. If the variable is null or unresolved, the policy falls back to the literal `<Value>`. This pattern is useful for setting defaults.

### AssignTo Explained

The `<AssignTo>` element controls which message the policy modifies:

- `<AssignTo>request</AssignTo>` -- modify the current request message.
- `<AssignTo>response</AssignTo>` -- modify the current response message.
- `<AssignTo createNew="true" type="request">myMessage</AssignTo>` -- create a new named message variable (useful as input to ServiceCallout).
- Omitting `<AssignTo>` or setting `createNew="false"`: modifies the current message in scope (request in request flow, response in response flow).

## ExtractVariables Policy

Extracts data from messages and stores it in flow variables. Supports JSONPath, XPath, URI path patterns, headers, and query parameters.

### JSONPath Extraction

```xml
<ExtractVariables name="EV-ExtractFromJSON">
  <Source>request</Source>
  <JSONPayload>
    <Variable name="userId" type="string">
      <JSONPath>$.user.id</JSONPath>
    </Variable>
    <Variable name="email" type="string">
      <JSONPath>$.user.email</JSONPath>
    </Variable>
    <Variable name="orderCount" type="integer">
      <JSONPath>$.orders.length()</JSONPath>
    </Variable>
  </JSONPayload>
  <VariablePrefix>extracted</VariablePrefix>
</ExtractVariables>
```

Creates variables: `extracted.userId`, `extracted.email`, `extracted.orderCount`. The prefix is prepended to each variable name.

### XPath Extraction

```xml
<ExtractVariables name="EV-ExtractFromXML">
  <Source>response</Source>
  <XMLPayload>
    <Namespaces>
      <Namespace prefix="ns">http://example.com/schema</Namespace>
    </Namespaces>
    <Variable name="status" type="string">
      <XPath>/ns:response/ns:status/text()</XPath>
    </Variable>
    <Variable name="txnId" type="string">
      <XPath>/ns:response/ns:transaction/@id</XPath>
    </Variable>
  </XMLPayload>
  <VariablePrefix>xml</VariablePrefix>
</ExtractVariables>
```

Creates variables: `xml.status`, `xml.txnId`. Declare namespaces in the `<Namespaces>` block when the source XML uses them.

### URI Path Pattern Extraction

```xml
<ExtractVariables name="EV-ExtractPath">
  <Source>request</Source>
  <URIPath>
    <Pattern ignoreCase="true">/users/{userId}/orders/{orderId}</Pattern>
  </URIPath>
  <VariablePrefix>path</VariablePrefix>
</ExtractVariables>
```

Creates variables: `path.userId`, `path.orderId`. The pattern matches against `proxy.pathsuffix`.

### Header and Query Param Extraction

```xml
<ExtractVariables name="EV-ExtractHeaders">
  <Source>request</Source>
  <Header name="Authorization">
    <Pattern>Bearer {token}</Pattern>
  </Header>
  <QueryParam name="filter">
    <Pattern>{filterValue}</Pattern>
  </QueryParam>
  <VariablePrefix>ev</VariablePrefix>
</ExtractVariables>
```

Creates variables: `ev.token`, `ev.filterValue`. Patterns use curly braces to define capture groups.

Set `<IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>` to avoid faults when extraction patterns do not match the source content.

## HTTPModifier Policy

A simpler alternative to AssignMessage when you only need to manipulate headers and query parameters without modifying payloads.

```xml
<HTTPModifier name="HM-ModifyRequest">
  <Add>
    <Headers>
      <Header name="X-Custom">{custom.value}</Header>
    </Headers>
  </Add>
  <Remove>
    <Headers>
      <Header name="X-Debug"/>
    </Headers>
  </Remove>
  <Set>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <QueryParams>
      <QueryParam name="v">2</QueryParam>
    </QueryParams>
  </Set>
</HTTPModifier>
```

HTTPModifier supports the same Add, Remove, and Set operations as AssignMessage but is limited to headers and query parameters. Use it when you do not need payload manipulation, variable assignment, or Copy operations.

## XMLtoJSON Policy

Converts XML payloads to JSON format.

```xml
<XMLtoJSON name="XJ-ConvertResponse">
  <Source>response</Source>
  <OutputVariable>response</OutputVariable>
  <Options>
    <RecognizeNumber>true</RecognizeNumber>
    <RecognizeBoolean>true</RecognizeBoolean>
    <NullValue>NULL</NullValue>
  </Options>
</XMLtoJSON>
```

The source Content-Type must be `application/xml` or `text/xml`. The policy automatically sets the output Content-Type to `application/json`. `RecognizeNumber` and `RecognizeBoolean` control whether string values that look like numbers or booleans are converted to their native JSON types.

## JSONtoXML Policy

Converts JSON payloads to XML format.

```xml
<JSONtoXML name="JX-ConvertRequest">
  <Source>request</Source>
  <OutputVariable>request</OutputVariable>
  <Options>
    <RecognizeNumber>true</RecognizeNumber>
    <RecognizeBoolean>true</RecognizeBoolean>
    <NullValue>I_AM_NULL</NullValue>
  </Options>
</JSONtoXML>
```

The source Content-Type must be `application/json`. The output Content-Type is set to `application/xml`. The `NullValue` option defines the string representation used for null JSON values in the XML output.

## Common Mediation Patterns

These patterns combine mediation policies to solve recurring integration challenges:

1. **Request enrichment**: Use ExtractVariables to pull data from the request payload, then AssignMessage to add the extracted values as headers forwarded to the backend.

```xml
<!-- Step 1: Extract -->
<Step><Name>EV-ExtractUserId</Name></Step>
<!-- Step 2: Enrich -->
<Step><Name>AM-AddUserIdHeader</Name></Step>
```

2. **Response filtering**: Use AssignMessage Remove or a JavaScript policy to strip sensitive fields (internal IDs, debug info) from responses before returning them to the client.

3. **Format translation**: Place JSONtoXML on the request flow and XMLtoJSON on the response flow to expose a JSON API over an XML backend. The client sends and receives JSON while the backend works with XML.

4. **Variable initialization**: Place an AssignMessage with `<AssignVariable>` elements early in the PreFlow to set default values for variables used by downstream policies (quota keys, routing flags, feature toggles).

---

[Security Policies](policies_security.md) | [Proxy Bundle Anatomy](proxy_bundle_anatomy.md) | [Flows and Execution](flows_and_execution.md) | [Flow Variables and Conditions](flow_variables_and_conditions.md) | [Endpoints and Routing](endpoints_and_routing.md)
