# End-to-End Proxy Examples

Four progressively complex, complete API proxy bundles. Each example includes ALL XML files needed for the proxy bundle.

## Example 1: Simple Passthrough Proxy

Minimal proxy that forwards requests to a backend with no policies.

### File Structure

```
apiproxy/
├── SimplePassthrough.xml
├── proxies/
│   └── default.xml
└── targets/
    └── default.xml
```

### apiproxy/SimplePassthrough.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<APIProxy name="SimplePassthrough" revision="1">
  <DisplayName>Simple Passthrough</DisplayName>
  <Description>Minimal proxy that forwards all requests to the backend</Description>
</APIProxy>
```

### apiproxy/proxies/default.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProxyEndpoint name="default">
  <HTTPProxyConnection>
    <BasePath>/v1/simple</BasePath>
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

---

## Example 2: API Key Protected with Rate Limiting

API with key verification, rate limiting, CORS, conditional flows by operation, and fault handling.

### File Structure

```
apiproxy/
├── ItemsAPI.xml
├── proxies/
│   └── default.xml
├── targets/
│   └── default.xml
└── policies/
    ├── VAK-VerifyKey.xml
    ├── SA-ProtectBackend.xml
    ├── Q-DailyLimit.xml
    ├── CORS-AllowOrigins.xml
    ├── AM-AuthError.xml
    ├── AM-QuotaError.xml
    └── AM-GenericError.xml
```

### apiproxy/ItemsAPI.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<APIProxy name="ItemsAPI" revision="1">
  <DisplayName>Items API</DisplayName>
  <Description>API key protected items service with rate limiting</Description>
</APIProxy>
```

### apiproxy/proxies/default.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProxyEndpoint name="default">
  <HTTPProxyConnection>
    <BasePath>/v1/items</BasePath>
  </HTTPProxyConnection>

  <PreFlow name="PreFlow">
    <Request>
      <Step>
        <Name>CORS-AllowOrigins</Name>
      </Step>
      <Step>
        <Name>VAK-VerifyKey</Name>
      </Step>
      <Step>
        <Name>SA-ProtectBackend</Name>
      </Step>
      <Step>
        <Name>Q-DailyLimit</Name>
      </Step>
    </Request>
    <Response/>
  </PreFlow>

  <Flows>
    <Flow name="get-items">
      <Condition>(proxy.pathsuffix MatchesPath "/") and (request.verb = "GET")</Condition>
      <Request/>
      <Response/>
    </Flow>
    <Flow name="create-item">
      <Condition>(proxy.pathsuffix MatchesPath "/") and (request.verb = "POST")</Condition>
      <Request/>
      <Response/>
    </Flow>
    <Flow name="get-item">
      <Condition>(proxy.pathsuffix MatchesPath "/{itemId}") and (request.verb = "GET")</Condition>
      <Request/>
      <Response/>
    </Flow>
    <Flow name="delete-item">
      <Condition>(proxy.pathsuffix MatchesPath "/{itemId}") and (request.verb = "DELETE")</Condition>
      <Request/>
      <Response/>
    </Flow>
  </Flows>

  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>

  <FaultRules>
    <FaultRule name="auth-errors">
      <Condition>(fault.name = "FailedToResolveAPIKey") or (fault.name = "InvalidApiKey") or (fault.name = "InvalidApiKeyForGivenResource")</Condition>
      <Step>
        <Name>AM-AuthError</Name>
      </Step>
    </FaultRule>
    <FaultRule name="quota-errors">
      <Condition>fault.name = "QuotaViolation" or fault.name = "SpikeArrestViolation"</Condition>
      <Step>
        <Name>AM-QuotaError</Name>
      </Step>
    </FaultRule>
  </FaultRules>

  <DefaultFaultRule>
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step>
      <Name>AM-GenericError</Name>
    </Step>
  </DefaultFaultRule>

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

### apiproxy/policies/VAK-VerifyKey.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<VerifyAPIKey name="VAK-VerifyKey">
  <DisplayName>Verify API Key</DisplayName>
  <APIKey ref="request.header.x-api-key"/>
</VerifyAPIKey>
```

### apiproxy/policies/SA-ProtectBackend.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SpikeArrest name="SA-ProtectBackend">
  <DisplayName>Protect Backend</DisplayName>
  <Rate>100pm</Rate>
  <Identifier ref="request.header.x-api-key"/>
  <UseEffectiveCount>true</UseEffectiveCount>
</SpikeArrest>
```

### apiproxy/policies/Q-DailyLimit.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Quota name="Q-DailyLimit">
  <DisplayName>Daily Quota</DisplayName>
  <Allow count="1000"/>
  <Interval>1</Interval>
  <TimeUnit>day</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <Identifier ref="request.header.x-api-key"/>
</Quota>
```

### apiproxy/policies/CORS-AllowOrigins.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CORS name="CORS-AllowOrigins">
  <DisplayName>CORS Allow Origins</DisplayName>
  <AllowOrigins>{request.header.origin}</AllowOrigins>
  <AllowMethods>GET, POST, DELETE, OPTIONS</AllowMethods>
  <AllowHeaders>origin, x-requested-with, accept, content-type, x-api-key</AllowHeaders>
  <ExposeHeaders>*</ExposeHeaders>
  <MaxAge>3600</MaxAge>
  <AllowCredentials>false</AllowCredentials>
  <GeneratePreflightResponse>true</GeneratePreflightResponse>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</CORS>
```

### apiproxy/policies/AM-AuthError.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-AuthError">
  <DisplayName>Auth Error Response</DisplayName>
  <AssignTo>response</AssignTo>
  <Set>
    <StatusCode>401</StatusCode>
    <ReasonPhrase>Unauthorized</ReasonPhrase>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "AUTHENTICATION_ERROR",
          "message": "Invalid or missing API key",
          "requestId": "{system.uuid}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

### apiproxy/policies/AM-QuotaError.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-QuotaError">
  <DisplayName>Quota Error Response</DisplayName>
  <AssignTo>response</AssignTo>
  <Set>
    <StatusCode>429</StatusCode>
    <ReasonPhrase>Too Many Requests</ReasonPhrase>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "RATE_LIMIT_EXCEEDED",
          "message": "API rate limit exceeded. Please retry later.",
          "requestId": "{system.uuid}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

### apiproxy/policies/AM-GenericError.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-GenericError">
  <DisplayName>Generic Error Response</DisplayName>
  <AssignTo>response</AssignTo>
  <Set>
    <StatusCode>500</StatusCode>
    <ReasonPhrase>Internal Server Error</ReasonPhrase>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "INTERNAL_ERROR",
          "message": "An unexpected error occurred",
          "requestId": "{system.uuid}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

---

## Example 3: OAuth-Secured API with Mediation

OAuth2 client_credentials flow with request/response transformation and full fault handling.

### File Structure

```
apiproxy/
├── UserServiceAPI.xml
├── proxies/
│   └── default.xml
├── targets/
│   └── default.xml
└── policies/
    ├── OAuth-GenerateToken.xml
    ├── OAuth-VerifyToken.xml
    ├── EV-ExtractUserId.xml
    ├── AM-EnrichRequest.xml
    ├── JS-FilterResponse.xml
    ├── AM-AuthError.xml
    ├── AM-GenericError.xml
    └── ML-LogToCloud.xml
```

### apiproxy/UserServiceAPI.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<APIProxy name="UserServiceAPI" revision="1">
  <DisplayName>User Service API</DisplayName>
  <Description>OAuth2-secured user service with mediation and logging</Description>
</APIProxy>
```

### apiproxy/proxies/default.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProxyEndpoint name="default">
  <HTTPProxyConnection>
    <BasePath>/v1/users</BasePath>
  </HTTPProxyConnection>

  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>

  <Flows>
    <Flow name="generate-token">
      <Condition>(proxy.pathsuffix MatchesPath "/token") and (request.verb = "POST")</Condition>
      <Request>
        <Step>
          <Name>OAuth-GenerateToken</Name>
        </Step>
      </Request>
      <Response/>
    </Flow>

    <Flow name="list-users">
      <Condition>(proxy.pathsuffix MatchesPath "/") and (request.verb = "GET")</Condition>
      <Request>
        <Step>
          <Name>OAuth-VerifyToken</Name>
        </Step>
      </Request>
      <Response>
        <Step>
          <Name>JS-FilterResponse</Name>
        </Step>
      </Response>
    </Flow>

    <Flow name="create-user">
      <Condition>(proxy.pathsuffix MatchesPath "/") and (request.verb = "POST")</Condition>
      <Request>
        <Step>
          <Name>OAuth-VerifyToken</Name>
        </Step>
      </Request>
      <Response/>
    </Flow>

    <Flow name="get-user">
      <Condition>(proxy.pathsuffix MatchesPath "/{userId}") and (request.verb = "GET")</Condition>
      <Request>
        <Step>
          <Name>OAuth-VerifyToken</Name>
        </Step>
        <Step>
          <Name>EV-ExtractUserId</Name>
        </Step>
        <Step>
          <Name>AM-EnrichRequest</Name>
        </Step>
      </Request>
      <Response>
        <Step>
          <Name>JS-FilterResponse</Name>
        </Step>
      </Response>
    </Flow>

    <Flow name="update-user">
      <Condition>(proxy.pathsuffix MatchesPath "/{userId}") and (request.verb = "PUT")</Condition>
      <Request>
        <Step>
          <Name>OAuth-VerifyToken</Name>
        </Step>
        <Step>
          <Name>EV-ExtractUserId</Name>
        </Step>
        <Step>
          <Name>AM-EnrichRequest</Name>
        </Step>
      </Request>
      <Response/>
    </Flow>

    <Flow name="delete-user">
      <Condition>(proxy.pathsuffix MatchesPath "/{userId}") and (request.verb = "DELETE")</Condition>
      <Request>
        <Step>
          <Name>OAuth-VerifyToken</Name>
        </Step>
        <Step>
          <Name>EV-ExtractUserId</Name>
        </Step>
      </Request>
      <Response/>
    </Flow>
  </Flows>

  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>

  <PostClientFlow name="PostClientFlow">
    <Response>
      <Step>
        <Name>ML-LogToCloud</Name>
      </Step>
    </Response>
  </PostClientFlow>

  <FaultRules>
    <FaultRule name="auth-errors">
      <Condition>(fault.name = "InvalidAccessToken") or (fault.name = "access_token_expired") or (fault.name = "InsufficientScope")</Condition>
      <Step>
        <Name>AM-AuthError</Name>
      </Step>
    </FaultRule>
  </FaultRules>

  <DefaultFaultRule>
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step>
      <Name>AM-GenericError</Name>
    </Step>
  </DefaultFaultRule>

  <RouteRule name="token-route">
    <Condition>proxy.pathsuffix MatchesPath "/token"</Condition>
  </RouteRule>
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
    <URL>https://user-service.example.com</URL>
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

### apiproxy/policies/OAuth-GenerateToken.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OAuthV2 name="OAuth-GenerateToken">
  <DisplayName>Generate OAuth Token</DisplayName>
  <Operation>GenerateAccessToken</Operation>
  <ExpiresIn>1800000</ExpiresIn>
  <SupportedGrantTypes>
    <GrantType>client_credentials</GrantType>
  </SupportedGrantTypes>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
</OAuthV2>
```

### apiproxy/policies/OAuth-VerifyToken.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OAuthV2 name="OAuth-VerifyToken">
  <DisplayName>Verify OAuth Token</DisplayName>
  <Operation>VerifyAccessToken</Operation>
</OAuthV2>
```

### apiproxy/policies/EV-ExtractUserId.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtractVariables name="EV-ExtractUserId">
  <DisplayName>Extract User ID from Path</DisplayName>
  <Source>request</Source>
  <URIPath>
    <Pattern ignoreCase="true">/{userId}</Pattern>
  </URIPath>
  <VariablePrefix>path</VariablePrefix>
</ExtractVariables>
```

### apiproxy/policies/AM-EnrichRequest.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-EnrichRequest">
  <DisplayName>Enrich Backend Request</DisplayName>
  <AssignTo>request</AssignTo>
  <Set>
    <Headers>
      <Header name="X-User-ID">{path.userId}</Header>
      <Header name="X-Request-ID">{system.uuid}</Header>
      <Header name="X-Client-App">{developer.app.name}</Header>
    </Headers>
  </Set>
  <Remove>
    <Headers>
      <Header name="Authorization"/>
    </Headers>
  </Remove>
</AssignMessage>
```

### apiproxy/policies/JS-FilterResponse.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Javascript name="JS-FilterResponse">
  <DisplayName>Filter Sensitive Response Fields</DisplayName>
  <ResourceURL>jsc://filter-response.js</ResourceURL>
</Javascript>
```

### apiproxy/resources/jsc/filter-response.js

```javascript
var content = context.getVariable("response.content");
if (content) {
  try {
    var body = JSON.parse(content);

    // Remove sensitive fields from response
    var sensitiveFields = ["passwordHash", "ssn", "internalId", "dbKey"];

    function filterObject(obj) {
      if (Array.isArray(obj)) {
        obj.forEach(function(item) {
          filterObject(item);
        });
      } else if (obj !== null && typeof obj === "object") {
        sensitiveFields.forEach(function(field) {
          delete obj[field];
        });
        Object.keys(obj).forEach(function(key) {
          filterObject(obj[key]);
        });
      }
    }

    filterObject(body);
    context.setVariable("response.content", JSON.stringify(body));
  } catch (e) {
    // Non-JSON response, pass through unchanged
  }
}
```

### apiproxy/policies/AM-AuthError.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-AuthError">
  <DisplayName>Auth Error Response</DisplayName>
  <AssignTo>response</AssignTo>
  <Set>
    <StatusCode>401</StatusCode>
    <ReasonPhrase>Unauthorized</ReasonPhrase>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "AUTHENTICATION_ERROR",
          "message": "Invalid or expired access token",
          "requestId": "{system.uuid}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

### apiproxy/policies/AM-GenericError.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-GenericError">
  <DisplayName>Generic Error Response</DisplayName>
  <AssignTo>response</AssignTo>
  <Set>
    <StatusCode>500</StatusCode>
    <ReasonPhrase>Internal Server Error</ReasonPhrase>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "INTERNAL_ERROR",
          "message": "An unexpected error occurred",
          "requestId": "{system.uuid}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

### apiproxy/policies/ML-LogToCloud.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MessageLogging name="ML-LogToCloud">
  <DisplayName>Log to Cloud Logging</DisplayName>
  <CloudLogging>
    <LogName>projects/{organization.name}/logs/apigee-user-service</LogName>
    <Message contentType="application/json">
      {
        "requestId": "{system.uuid}",
        "verb": "{request.verb}",
        "path": "{request.path}",
        "statusCode": "{response.status.code}",
        "clientIp": "{client.ip}",
        "clientApp": "{developer.app.name}",
        "latency": "{target.received.end.timestamp - target.received.start.timestamp}",
        "proxyName": "{apiproxy.name}",
        "environment": "{environment.name}"
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
    </Labels>
    <ResourceType>api</ResourceType>
  </CloudLogging>
</MessageLogging>
```

---

## Example 4: Composite API with Caching and Circuit Breaker

Advanced proxy that calls multiple backends, aggregates responses, implements caching and failover.

### File Structure

```
apiproxy/
├── CompositeProfileAPI.xml
├── proxies/
│   └── default.xml
├── targets/
│   ├── primary.xml
│   └── secondary.xml
├── policies/
│   ├── FC-AuthSharedFlow.xml
│   ├── RC-CacheProfile.xml
│   ├── SC-GetUserDetails.xml
│   ├── SC-GetUserOrders.xml
│   ├── EV-ExtractUser.xml
│   ├── JS-AggregateProfile.xml
│   ├── Q-CircuitBreaker.xml
│   ├── Q-CircuitBreaker-Increment.xml
│   ├── AM-GenericError.xml
│   └── ML-LogToCloud.xml
└── resources/
    └── jsc/
        └── aggregate-profile.js
```

### apiproxy/CompositeProfileAPI.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<APIProxy name="CompositeProfileAPI" revision="1">
  <DisplayName>Composite Profile API</DisplayName>
  <Description>Aggregates user details and orders from multiple backends with caching and circuit breaker</Description>
</APIProxy>
```

### apiproxy/proxies/default.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ProxyEndpoint name="default">
  <HTTPProxyConnection>
    <BasePath>/v1/profile</BasePath>
  </HTTPProxyConnection>

  <PreFlow name="PreFlow">
    <Request>
      <Step>
        <Name>FC-AuthSharedFlow</Name>
      </Step>
      <Step>
        <Name>Q-CircuitBreaker</Name>
      </Step>
    </Request>
    <Response/>
  </PreFlow>

  <Flows>
    <Flow name="get-profile">
      <Condition>(proxy.pathsuffix MatchesPath "/{userId}") and (request.verb = "GET")</Condition>
      <Request>
        <Step>
          <Name>EV-ExtractUser</Name>
        </Step>
        <Step>
          <Name>RC-CacheProfile</Name>
        </Step>
        <Step>
          <Condition>responsecache.RC-CacheProfile.cachehit = false</Condition>
          <Name>SC-GetUserDetails</Name>
        </Step>
        <Step>
          <Condition>responsecache.RC-CacheProfile.cachehit = false</Condition>
          <Name>SC-GetUserOrders</Name>
        </Step>
      </Request>
      <Response>
        <Step>
          <Condition>responsecache.RC-CacheProfile.cachehit = false</Condition>
          <Name>JS-AggregateProfile</Name>
        </Step>
        <Step>
          <Name>RC-CacheProfile</Name>
        </Step>
      </Response>
    </Flow>
  </Flows>

  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>

  <PostClientFlow name="PostClientFlow">
    <Response>
      <Step>
        <Name>ML-LogToCloud</Name>
      </Step>
    </Response>
  </PostClientFlow>

  <FaultRules>
    <FaultRule name="service-callout-errors">
      <Condition>fault.name = "ExecutionFailed"</Condition>
      <Step>
        <Name>AM-GenericError</Name>
      </Step>
    </FaultRule>
  </FaultRules>

  <DefaultFaultRule>
    <AlwaysEnforce>true</AlwaysEnforce>
    <Step>
      <Name>AM-GenericError</Name>
    </Step>
  </DefaultFaultRule>

  <RouteRule name="primary">
    <Condition>ratelimit.Q-CircuitBreaker.failed = false</Condition>
    <TargetEndpoint>primary</TargetEndpoint>
  </RouteRule>
  <RouteRule name="fallback">
    <TargetEndpoint>secondary</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

### apiproxy/targets/primary.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TargetEndpoint name="primary">
  <HTTPTargetConnection>
    <URL>https://primary-backend.example.com/api</URL>
    <SSLInfo>
      <Enabled>true</Enabled>
    </SSLInfo>
  </HTTPTargetConnection>

  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>

  <Flows/>

  <PostFlow name="PostFlow">
    <Request/>
    <Response>
      <Step>
        <Condition>response.status.code >= 500</Condition>
        <Name>Q-CircuitBreaker-Increment</Name>
      </Step>
    </Response>
  </PostFlow>
</TargetEndpoint>
```

### apiproxy/targets/secondary.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TargetEndpoint name="secondary">
  <HTTPTargetConnection>
    <URL>https://fallback-backend.example.com/api</URL>
    <SSLInfo>
      <Enabled>true</Enabled>
    </SSLInfo>
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

### apiproxy/policies/FC-AuthSharedFlow.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowCallout name="FC-AuthSharedFlow">
  <DisplayName>Auth Shared Flow</DisplayName>
  <SharedFlowBundle>auth-shared-flow</SharedFlowBundle>
</FlowCallout>
```

### apiproxy/policies/RC-CacheProfile.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ResponseCache name="RC-CacheProfile">
  <DisplayName>Cache Profile Response</DisplayName>
  <CacheKey>
    <Prefix>profile</Prefix>
    <KeyFragment ref="path.userId"/>
  </CacheKey>
  <Scope>Exclusive</Scope>
  <ExpirySettings>
    <TimeoutInSec>600</TimeoutInSec>
  </ExpirySettings>
  <ExcludeErrorResponse>true</ExcludeErrorResponse>
  <SkipCacheLookup>
    <Condition>request.header.x-bypass-cache = "true"</Condition>
  </SkipCacheLookup>
  <SkipCachePopulation>
    <Condition>request.verb != "GET"</Condition>
  </SkipCachePopulation>
</ResponseCache>
```

### apiproxy/policies/SC-GetUserDetails.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceCallout name="SC-GetUserDetails">
  <DisplayName>Get User Details</DisplayName>
  <Request clearPayload="true" variable="userRequest">
    <Set>
      <URL>https://user-service.example.com/users/{path.userId}</URL>
      <Verb>GET</Verb>
      <Headers>
        <Header name="Accept">application/json</Header>
        <Header name="X-Request-ID">{system.uuid}</Header>
      </Headers>
    </Set>
  </Request>
  <Response>userResponse</Response>
  <Timeout>10000</Timeout>
</ServiceCallout>
```

### apiproxy/policies/SC-GetUserOrders.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ServiceCallout name="SC-GetUserOrders">
  <DisplayName>Get User Orders</DisplayName>
  <Request clearPayload="true" variable="ordersRequest">
    <Set>
      <URL>https://order-service.example.com/orders?userId={path.userId}</URL>
      <Verb>GET</Verb>
      <Headers>
        <Header name="Accept">application/json</Header>
        <Header name="X-Request-ID">{system.uuid}</Header>
      </Headers>
    </Set>
  </Request>
  <Response>ordersResponse</Response>
  <Timeout>10000</Timeout>
</ServiceCallout>
```

### apiproxy/policies/EV-ExtractUser.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtractVariables name="EV-ExtractUser">
  <DisplayName>Extract User ID from Path</DisplayName>
  <Source>request</Source>
  <URIPath>
    <Pattern ignoreCase="true">/{userId}</Pattern>
  </URIPath>
  <VariablePrefix>path</VariablePrefix>
</ExtractVariables>
```

### apiproxy/policies/JS-AggregateProfile.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Javascript name="JS-AggregateProfile">
  <DisplayName>Aggregate Profile Data</DisplayName>
  <ResourceURL>jsc://aggregate-profile.js</ResourceURL>
</Javascript>
```

### apiproxy/resources/jsc/aggregate-profile.js

```javascript
var userContent = context.getVariable("userResponse.content");
var ordersContent = context.getVariable("ordersResponse.content");
var userStatus = context.getVariable("userResponse.status.code");
var ordersStatus = context.getVariable("ordersResponse.status.code");

var profile = {
  generatedAt: new Date().toISOString(),
  requestId: context.getVariable("system.uuid")
};

// Parse user details if the service returned 200
if (userStatus == 200 && userContent) {
  try {
    profile.user = JSON.parse(userContent);
  } catch (e) {
    profile.user = null;
    profile.userError = "Failed to parse user details";
  }
} else {
  profile.user = null;
  profile.userError = "User service returned status " + userStatus;
}

// Parse orders if the service returned 200
if (ordersStatus == 200 && ordersContent) {
  try {
    var ordersData = JSON.parse(ordersContent);
    // Include only the 5 most recent orders
    profile.recentOrders = ordersData.items ? ordersData.items.slice(0, 5) : [];
    profile.totalOrders = ordersData.totalCount || 0;
  } catch (e) {
    profile.recentOrders = [];
    profile.ordersError = "Failed to parse orders";
  }
} else {
  profile.recentOrders = [];
  profile.ordersError = "Order service returned status " + ordersStatus;
}

context.setVariable("response.content", JSON.stringify(profile));
context.setVariable("response.header.Content-Type", "application/json");
context.setVariable("response.status.code", 200);
```

### apiproxy/policies/Q-CircuitBreaker.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Quota name="Q-CircuitBreaker" continueOnError="true">
  <DisplayName>Circuit Breaker Check</DisplayName>
  <Allow count="5"/>
  <Interval>2</Interval>
  <TimeUnit>minute</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <EnforceOnly>true</EnforceOnly>
  <Identifier>circuit-breaker</Identifier>
</Quota>
```

### apiproxy/policies/Q-CircuitBreaker-Increment.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Quota name="Q-CircuitBreaker-Increment">
  <DisplayName>Circuit Breaker Increment on Failure</DisplayName>
  <Allow count="5"/>
  <Interval>2</Interval>
  <TimeUnit>minute</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <Identifier>circuit-breaker</Identifier>
</Quota>
```

### apiproxy/policies/AM-GenericError.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AssignMessage name="AM-GenericError">
  <DisplayName>Generic Error Response</DisplayName>
  <AssignTo>response</AssignTo>
  <Set>
    <StatusCode>500</StatusCode>
    <ReasonPhrase>Internal Server Error</ReasonPhrase>
    <Headers>
      <Header name="Content-Type">application/json</Header>
    </Headers>
    <Payload contentType="application/json">
      {
        "error": {
          "code": "INTERNAL_ERROR",
          "message": "An unexpected error occurred",
          "requestId": "{system.uuid}"
        }
      }
    </Payload>
  </Set>
</AssignMessage>
```

### apiproxy/policies/ML-LogToCloud.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<MessageLogging name="ML-LogToCloud">
  <DisplayName>Log to Cloud Logging</DisplayName>
  <CloudLogging>
    <LogName>projects/{organization.name}/logs/apigee-composite-profile</LogName>
    <Message contentType="application/json">
      {
        "requestId": "{system.uuid}",
        "verb": "{request.verb}",
        "path": "{request.path}",
        "statusCode": "{response.status.code}",
        "clientIp": "{client.ip}",
        "cacheHit": "{responsecache.RC-CacheProfile.cachehit}",
        "circuitBreakerTripped": "{ratelimit.Q-CircuitBreaker.failed}",
        "latency": "{target.received.end.timestamp - target.received.start.timestamp}",
        "proxyName": "{apiproxy.name}",
        "environment": "{environment.name}"
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
    </Labels>
    <ResourceType>api</ResourceType>
  </CloudLogging>
</MessageLogging>
```

---

See also:
- [Proxy Bundle Anatomy](./proxy_bundle_anatomy.md)
- [Endpoints and Routing](./endpoints_and_routing.md)
- [Fault Handling](./fault_handling.md)
- [Anti-patterns and Best Practices](./anti_patterns_and_best_practices.md)
- [Advanced Patterns](./advanced_patterns.md)
- [Policies: Security](./policies_security.md)
- [Policies: Caching](./policies_caching.md)
