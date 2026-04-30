# Fault Handling

## How Faults Work in Apigee X

When a policy fails and `continueOnError` is set to `false` (the default), execution immediately enters the error flow. The remaining Steps in the current flow are skipped. Apigee then evaluates FaultRules in the endpoint where the fault occurred. If no FaultRule condition matches, the DefaultFaultRule executes. Without any fault handling configured, Apigee returns a generic error to the client.

## Fault Handling Architecture

```
Policy fails → Skip remaining steps → Evaluate FaultRules →
  If match:    execute FaultRule steps → Return error response
  If no match: Execute DefaultFaultRule → Return error response
  If no DefaultFaultRule: Return generic Apigee error
```

## FaultRules

FaultRules are defined in ProxyEndpoint and/or TargetEndpoint. Each FaultRule has a Condition that determines when it fires. Only the **first** matching FaultRule executes.

**Critical: Evaluation order differs by endpoint:**
- **ProxyEndpoint: Bottom to top** -- the last FaultRule in XML is evaluated first
- **TargetEndpoint: Top to bottom** -- the first FaultRule in XML is evaluated first

```xml
<ProxyEndpoint name="default">
  <!-- ... flows ... -->

  <FaultRules>
    <FaultRule name="auth-errors">
      <Condition>(fault.name = "FailedToResolveAPIKey") or (fault.name = "InvalidApiKey")</Condition>
      <Step>
        <Name>AM-AuthError</Name>
      </Step>
    </FaultRule>

    <FaultRule name="quota-errors">
      <Condition>fault.name = "QuotaViolation"</Condition>
      <Step>
        <Name>AM-QuotaError</Name>
      </Step>
    </FaultRule>

    <FaultRule name="threat-errors">
      <Condition>fault.name Matches "Body*" or fault.name Matches "Exceeded*"</Condition>
      <Step>
        <Name>AM-ThreatError</Name>
      </Step>
    </FaultRule>
  </FaultRules>

  <DefaultFaultRule>
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step>
      <Name>AM-GenericError</Name>
    </Step>
  </DefaultFaultRule>
</ProxyEndpoint>
```

## DefaultFaultRule

DefaultFaultRule catches all faults not handled by specific FaultRules. When `AlwaysEnforce` is set to `true`, it executes even if a FaultRule already matched (it runs after the matching FaultRule). Every proxy should have a DefaultFaultRule for consistent error responses.

```xml
<DefaultFaultRule>
  <AlwaysEnforce>true</AlwaysEnforce>
  <Step>
    <Name>AM-SetErrorHeaders</Name>
  </Step>
  <Step>
    <Name>AM-FormatError</Name>
  </Step>
</DefaultFaultRule>
```

## RaiseFault for Custom Errors

Use RaiseFault to explicitly trigger a fault from any flow and enter the error flow.

```xml
<RaiseFault name="RF-ValidationError">
  <FaultResponse>
    <Set>
      <StatusCode>400</StatusCode>
      <ReasonPhrase>Bad Request</ReasonPhrase>
      <Headers>
        <Header name="Content-Type">application/json</Header>
      </Headers>
      <Payload contentType="application/json">
        {
          "error": {
            "code": "VALIDATION_ERROR",
            "message": "Field '{custom.missingField}' is required",
            "requestId": "{system.uuid}"
          }
        }
      </Payload>
    </Set>
  </FaultResponse>
</RaiseFault>
```

Use RaiseFault in conditional Steps to validate input and raise a fault on failure.

### RaiseFault + FaultRule Interaction

When RaiseFault triggers an error AND a FaultRule also executes:
- **FaultRule response wins** for status code and payload (it runs after RaiseFault)
- If the FaultRule does NOT set status code or payload, the RaiseFault values are used
- **Custom headers from BOTH** are included in the response (duplicate names create multi-value headers)

This means RaiseFault sets initial error state, but FaultRules can override it.

## continueOnError Attribute

When set to `true` on a policy, flow execution continues even if the policy fails. The proxy does NOT enter the error state, so **FaultRules will NOT be triggered** even if their conditions match. The `{policy}.failed` variable is set to `true`, but no fault is raised. Use this for optional enrichment (e.g., ServiceCallout) or best-effort operations. Never use `continueOnError="true"` on security policies -- a failed auth check would silently pass.

To detect the failure when `continueOnError="true"`, check the `{policy}.failed` variable:
```xml
<Step><Name>SC-OptionalCallout</Name></Step>
<Step>
  <Condition>servicecallout.SC-OptionalCallout.failed = true</Condition>
  <Name>AM-LogCalloutFailure</Name>
</Step>
```

```xml
<!-- SAFE: optional enrichment -->
<ServiceCallout name="SC-GetRecommendations" continueOnError="true">
  <!-- callout configuration -->
</ServiceCallout>

<!-- UNSAFE: never do this -->
<VerifyAPIKey name="VAK-VerifyKey" continueOnError="true">  <!-- WRONG! -->
  <!-- key verification -->
</VerifyAPIKey>
```

## Error Variables Reference

| Variable | Description | Example |
|---|---|---|
| `fault.name` | Policy-specific fault name | `FailedToResolveAPIKey`, `QuotaViolation` |
| `fault.type` | Fault category | `ErrorPoint` |
| `fault.category` | Broad category | `Step` |
| `error.status.code` | HTTP status code of the error | `401`, `429`, `500` |
| `error.message` | Error message text | `API Key is invalid` |
| `error.content` | Error response body | Full error payload |
| `error.transport.message` | Transport-level error message | `Connection timeout` |

## ProxyEndpoint vs TargetEndpoint Fault Handling

**Where an error occurs determines which FaultRules are checked.** Apigee looks for FaultRules ONLY in the endpoint where the error happened:

- **Error in TargetEndpoint** (e.g., backend timeout, target policy failure): Only TargetEndpoint FaultRules are checked. ProxyEndpoint FaultRules are NOT executed.
- **Error in ProxyEndpoint** (e.g., auth failure, proxy policy error): Only ProxyEndpoint FaultRules are checked. TargetEndpoint FaultRules are NOT executed.

This means if you define FaultRules only in ProxyEndpoint, backend errors (503, timeouts) will NOT be caught by them. You must define FaultRules in both endpoints if you want to handle errors from both.

**Evaluation order reminder:**
- ProxyEndpoint FaultRules: bottom to top (last in XML first)
- TargetEndpoint FaultRules: top to bottom (first in XML first)

Best practice: define FaultRules in both ProxyEndpoint and TargetEndpoint with a shared error formatting pattern (via shared flow or consistent AssignMessage policies).

## Building Consistent Error Responses

Create a standard error format for all error responses using AssignMessage.

```xml
<AssignMessage name="AM-FormatError">
  <AssignTo>response</AssignTo>
  <Set>
    <Headers>
      <Header name="Content-Type">application/json</Header>
      <Header name="X-Request-ID">{system.uuid}</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "{custom.errorCode}",
          "message": "{custom.errorMessage}",
          "status": {error.status.code},
          "requestId": "{system.uuid}",
          "timestamp": "{system.timestamp}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

The recommended pattern: each specific FaultRule sets `custom.errorCode` and `custom.errorMessage`, then DefaultFaultRule with `AlwaysEnforce` formats the final response.

## Complete Fault Handling Example

A ProxyEndpoint with multiple FaultRules, DefaultFaultRule, error formatting, and correlation ID propagation.

```xml
<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request>
      <Step>
        <Name>VAK-VerifyKey</Name>
      </Step>
      <Step>
        <Name>QU-EnforceQuota</Name>
      </Step>
      <Step>
        <Name>JTP-ProtectInput</Name>
      </Step>
    </Request>
    <Response>
      <Step>
        <Name>AM-AddCorsHeaders</Name>
      </Step>
    </Response>
  </PreFlow>

  <Flows>
    <Flow name="CreateOrder">
      <Condition>(proxy.pathsuffix MatchesPath "/orders") and (request.verb = "POST")</Condition>
      <Request>
        <Step>
          <Name>JS-ValidateOrderPayload</Name>
        </Step>
        <Step>
          <Condition>custom.raiseError = "true"</Condition>
          <Name>RF-ValidationError</Name>
        </Step>
      </Request>
    </Flow>
  </Flows>

  <FaultRules>
    <FaultRule name="auth-errors">
      <Condition>(fault.name = "FailedToResolveAPIKey") or (fault.name = "InvalidApiKey") or (fault.name = "InvalidApiKeyForGivenResource")</Condition>
      <Step>
        <Name>AM-SetAuthErrorVars</Name>
      </Step>
    </FaultRule>

    <FaultRule name="quota-errors">
      <Condition>fault.name = "QuotaViolation"</Condition>
      <Step>
        <Name>AM-SetQuotaErrorVars</Name>
      </Step>
    </FaultRule>

    <FaultRule name="threat-errors">
      <Condition>fault.name Matches "Body*" or fault.name Matches "Exceeded*" or fault.name Matches "Source*"</Condition>
      <Step>
        <Name>AM-SetThreatErrorVars</Name>
      </Step>
    </FaultRule>

    <FaultRule name="backend-errors">
      <Condition>fault.name = "ExecutionFailed"</Condition>
      <Step>
        <Name>AM-SetBackendErrorVars</Name>
      </Step>
    </FaultRule>
  </FaultRules>

  <DefaultFaultRule>
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step>
      <Condition>custom.errorCode = null</Condition>
      <Name>AM-SetGenericErrorVars</Name>
    </Step>
    <Step>
      <Name>AM-FormatError</Name>
    </Step>
    <Step>
      <Name>AM-AddCorsHeaders</Name>
    </Step>
  </DefaultFaultRule>

  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

Supporting policies for the error variable setup:

```xml
<AssignMessage name="AM-SetAuthErrorVars">
  <AssignVariable>
    <Name>custom.errorCode</Name>
    <Value>AUTHENTICATION_ERROR</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>custom.errorMessage</Name>
    <Value>Invalid or missing API key</Value>
  </AssignVariable>
  <Set>
    <StatusCode>401</StatusCode>
  </Set>
</AssignMessage>
```

```xml
<AssignMessage name="AM-SetQuotaErrorVars">
  <AssignVariable>
    <Name>custom.errorCode</Name>
    <Value>RATE_LIMIT_EXCEEDED</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>custom.errorMessage</Name>
    <Value>API rate limit exceeded. Please retry later.</Value>
  </AssignVariable>
  <Set>
    <StatusCode>429</StatusCode>
  </Set>
</AssignMessage>
```

```xml
<AssignMessage name="AM-SetGenericErrorVars">
  <AssignVariable>
    <Name>custom.errorCode</Name>
    <Value>INTERNAL_ERROR</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>custom.errorMessage</Name>
    <Value>An unexpected error occurred</Value>
  </AssignVariable>
  <Set>
    <StatusCode>500</StatusCode>
  </Set>
</AssignMessage>
```

## Common Fault Names Reference

| Policy | Common `fault.name` Values |
|---|---|
| VerifyAPIKey | `FailedToResolveAPIKey`, `InvalidApiKey`, `InvalidApiKeyForGivenResource` |
| OAuthV2 | `InvalidAccessToken`, `access_token_expired`, `InsufficientScope` |
| Quota | `QuotaViolation` |
| SpikeArrest | `SpikeArrestViolation` |
| JSONThreatProtection | `ExceededContainerDepth`, `ExceededArrayElementCount`, `ExceededStringValueLength` |
| ServiceCallout | `ExecutionFailed` (timeout, connection error) |
| XMLThreatProtection | `NodeDepthExceeded`, `AttrCountExceeded` |
| RegularExpressionProtection | `ThreatDetected` |

---

See also:
- [Proxy Bundle Anatomy](proxy_bundle_anatomy.md)
- [Flows and Execution](flows_and_execution.md)
- [Flow Variables and Conditions](flow_variables_and_conditions.md)
- [Security Policies](policies_security.md)
- [Traffic Management Policies](policies_traffic_management.md)
- [JavaScript Development](javascript_development.md)
