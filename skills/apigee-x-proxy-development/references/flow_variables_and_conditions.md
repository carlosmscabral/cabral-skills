# Flow Variables, Conditions, and Message Templates

This reference provides a comprehensive guide to built-in flow variables in Apigee X, condition syntax with all operators, custom variables, and message template functions. It is organized as a lookup reference for proxy development.

---

## Flow Variables

Flow variables carry contextual data through the proxy pipeline. They are set automatically by Apigee at various stages of request processing, by policies after execution, and manually by developers using AssignMessage or JavaScript.

### request.* Variables

Available during the **request phase** (ProxyEndpoint request flow and TargetEndpoint request flow). Not available in the response phase unless captured into a custom variable.

| Variable | Type | R/W | Description |
|---|---|---|---|
| `request.verb` | String | Read | HTTP method: GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD |
| `request.uri` | String | Read | Request URI including query string, e.g. `/v1/users?status=active` |
| `request.url` | String | Read | Full URL including scheme and host, e.g. `https://api.example.com/v1/users?status=active` |
| `request.path` | String | Read | Request path without query string, e.g. `/v1/users` |
| `request.querystring` | String | Read | Full query string without the leading `?`, e.g. `status=active&limit=10` |
| `request.queryparam.{name}` | String | Read/Write | Value of a named query parameter. Returns null if not present |
| `request.queryparam.{name}.values.count` | Integer | Read | Number of values for a multi-valued query parameter |
| `request.header.{name}` | String | Read/Write | Value of a named request header. Case-insensitive name lookup |
| `request.header.{name}.values.count` | Integer | Read | Number of values for a multi-valued header |
| `request.formparam.{name}` | String | Read/Write | Value of a form parameter (application/x-www-form-urlencoded body) |
| `request.headers.count` | Integer | Read | Total number of request headers |
| `request.headers.names` | Collection | Read | List of all request header names |
| `request.formparams.count` | Integer | Read | Total number of form parameters |
| `request.formparams.names` | Collection | Read | List of all form parameter names |
| `request.content` | String | Read | Full request body as a string. **Empty when streaming is enabled** |
| `request.content.length` | Integer | Read | Length of the request body in bytes |
| `request.version` | String | Read | HTTP version, e.g. `1.1` |
| `request.scheme` | String | Read | Protocol scheme: `http` or `https` |
| `request.transport.message.type` | String | Read | Message type, typically `request` |

### response.* Variables

Available during the **response phase** (TargetEndpoint response flow and ProxyEndpoint response flow). Not available in the request phase.

| Variable | Type | R/W | Description |
|---|---|---|---|
| `response.content` | String | Read/Write | Response body as a string |
| `response.status.code` | Integer | Read/Write | HTTP status code, e.g. `200`, `404`, `500` |
| `response.reason.phrase` | String | Read/Write | HTTP reason phrase, e.g. `OK`, `Not Found` |
| `response.header.{name}` | String | Read/Write | Value of a named response header |
| `response.header.{name}.values.count` | Integer | Read | Number of values for a multi-valued response header |
| `response.content.length` | Integer | Read | Length of the response body in bytes |
| `response.version` | String | Read | HTTP version of the response |

### message.* Variables -- Context-Aware Behavior

The `message.*` variables are aliases that point to different underlying messages depending on the current flow phase:

| Flow Phase | `message.*` Refers To |
|---|---|
| Proxy request flow | `request.*` |
| Target request flow | `request.*` |
| Target response flow | `response.*` |
| Proxy response flow | `response.*` |
| Error flow | `error.*` |

**Key use cases for `message.*`:**
- **Error flow:** In FaultRules, `request.*` and `response.*` are out of scope. Use `message.*` to access the error message object. `AssignMessage` auto-switches context to the error message in fault flows.
- **PostClientFlow logging:** Use `message.*` in MessageLogging to seamlessly log response data in both success and error scenarios.
- **Shared policies:** A single AssignMessage or JavaScript policy can work in both request and response flows by referencing `message.*` instead of hard-coding `request.*` or `response.*`.

| Variable | Description |
|---|---|
| `message.content` | Body of the current message (request, response, or error) |
| `message.header.{name}` | Header of the current message |
| `message.status.code` | Status code (meaningful only in response/error phase) |
| `message.reason.phrase` | Reason phrase (meaningful only in response/error phase) |
| `message.version` | HTTP version of the current message |

### proxy.* Variables

| Variable | Type | Description | Example |
|---|---|---|---|
| `proxy.name` | String | Name of the ProxyEndpoint | `default` |
| `proxy.revision` | String | Revision number of the deployed proxy | `12` |
| `proxy.basepath` | String | The base path configured in the ProxyEndpoint | `/v1` |
| `proxy.pathsuffix` | String | Path after the base path | `/users/123` |
| `proxy.url` | String | Full proxy URL as received | `https://api.example.com/v1/users/123` |
| `proxy.client.ip` | String | Client IP address (may differ from `client.ip` when behind a load balancer; this gives the IP from X-Forwarded-For) | `203.0.113.42` |

### target.* Variables

| Variable | Type | R/W | Description |
|---|---|---|---|
| `target.url` | String | **Read/Write** | Full URL of the target backend. **Writable** -- critical for dynamic routing. Setting this in the target request flow overrides the HTTPTargetConnection URL |
| `target.name` | String | Read | Name of the TargetEndpoint being invoked |
| `target.host` | String | Read | Hostname of the target server |
| `target.port` | Integer | Read | Port of the target server |
| `target.ip` | String | Read | IP address of the resolved target server |
| `target.basepath` | String | Read | Base path on the target server |
| `target.pathsuffix` | String | Read | Path suffix forwarded to the target |
| `target.cn` | String | Read | Common Name from the target's TLS certificate |
| `target.copy.pathsuffix` | Boolean | Read | Whether the proxy path suffix is copied to the target URL (default true) |
| `target.copy.queryparams` | Boolean | Read | Whether query parameters are copied to the target URL (default true) |
| `target.ssl.enabled` | Boolean | Read | Whether the target connection uses TLS |
| `target.sent.start.timestamp` | Long | Read | Timestamp (ms) when the request began being sent to the target |
| `target.received.start.timestamp` | Long | Read | Timestamp (ms) when the response from the target began arriving |
| `target.received.end.timestamp` | Long | Read | Timestamp (ms) when the full response from the target was received |

**Dynamic routing example** -- overriding `target.url` based on a header:

```xml
<AssignMessage name="Route-To-Region">
  <AssignVariable>
    <Name>target.url</Name>
    <Value>https://us-backend.example.com/api</Value>
  </AssignVariable>
  <Condition>request.header.X-Region = "us"</Condition>
</AssignMessage>
```

### client.* Variables

| Variable | Type | Description |
|---|---|---|
| `client.ip` | String | IP address of the immediate client connection |
| `client.host` | String | Host header value from the client request |
| `client.port` | Integer | Port number of the client connection |
| `client.scheme` | String | Protocol scheme used by the client: `http` or `https` |
| `client.ssl.enabled` | Boolean | Whether the client connection uses TLS |
| `client.received.start.timestamp` | Long | Timestamp (ms) when the proxy began receiving the request from the client |
| `client.sent.end.timestamp` | Long | Timestamp (ms) when the proxy finished sending the response to the client. **Available only in PostClientFlow** |

### error.* and fault.* Variables

Available during **fault handling** (FaultRules, DefaultFaultRule, and the error flow).

| Variable | Type | Description | Example |
|---|---|---|---|
| `error.content` | String | Body of the error response | `{"fault":{"faultstring":"..."}}` |
| `error.message` | String | Error message string | `Invalid API Key` |
| `error.status.code` | Integer | HTTP status code of the error | `401` |
| `error.reason.phrase` | String | HTTP reason phrase of the error | `Unauthorized` |
| `error.header.{name}` | String | Header value on the error response | `application/json` |
| `error.transport.message.type` | String | Message type | `error` |
| `is.error` | Boolean | True when the flow is in error state. Use in conditions to detect error state | `true` |
| `fault.name` | String | Name of the fault as defined by the policy that raised it | `InvalidAccessToken` |
| `fault.type` | String | Type of fault | `ErrorResponseCode` |
| `fault.category` | String | Category of fault: `Step`, `Transport`, `Messaging` | `Step` |

### system.* Variables

Available in all flow phases.

| Variable | Type | Description | Example |
|---|---|---|---|
| `system.timestamp` | Long | Current timestamp in milliseconds since epoch | `1698765432100` |
| `system.time` | String | Formatted time string | `Thu, 31 Oct 2024 14:30:32 UTC` |
| `system.time.year` | String | Four-digit year | `2026` |
| `system.time.month` | String | Two-digit month | `04` |
| `system.time.day` | String | Two-digit day of month | `30` |
| `system.time.hour` | String | Two-digit hour (24-hour format) | `14` |
| `system.time.minute` | String | Two-digit minute | `30` |
| `system.time.second` | String | Two-digit second | `32` |
| `system.uuid` | String | Unique identifier for the transaction | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `system.pod.name` | String | Name of the pod processing the request | `apigee-runtime-abc123` |
| `system.region.name` | String | Region where the proxy is executing | `us-central1` |

### apiproduct.* Variables

**Important:** These variables are populated ONLY after a successful `VerifyAPIKey` or `OAuthV2` `VerifyAccessToken` policy execution. They will be null if no key/token verification has run.

| Variable | Description |
|---|---|
| `apiproduct.name` | Name of the matched API product |
| `apiproduct.developer.quota.limit` | Quota limit configured on the API product |
| `apiproduct.developer.quota.interval` | Quota interval value (e.g. `1`) |
| `apiproduct.developer.quota.timeunit` | Quota time unit: `minute`, `hour`, `day`, `week`, `month` |
| `apiproduct.{custom_attribute_name}` | Custom attributes defined on the API product are accessible by name |

### apiproxy.* and environment.* Variables

| Variable | Description | Example |
|---|---|---|
| `apiproxy.name` | Name of the API proxy bundle | `my-users-api` |
| `apiproxy.revision` | Deployed revision number | `12` |
| `environment.name` | Name of the Apigee environment | `prod` |
| `organization.name` | Name of the Apigee organization | `my-org` |

### verifyapikey.{policy_name}.* Variables

Set after a `VerifyAPIKey` policy executes. Replace `{policy_name}` with the name attribute of the policy.

| Variable | Description |
|---|---|
| `verifyapikey.{policy_name}.client_id` | The consumer key (API key) |
| `verifyapikey.{policy_name}.client_secret` | The consumer secret associated with the key |
| `verifyapikey.{policy_name}.failed` | Boolean indicating whether verification failed |
| `verifyapikey.{policy_name}.developer.id` | Developer ID associated with the app |
| `verifyapikey.{policy_name}.developer.app.name` | Name of the developer app |
| `verifyapikey.{policy_name}.developer.email` | Email of the developer |
| `verifyapikey.{policy_name}.app.name` | Name of the app |
| `verifyapikey.{policy_name}.app.status` | Status of the app: `approved` or `revoked` |
| `verifyapikey.{policy_name}.apiproduct.name` | Name of the matched API product |

### oauthv2accesstoken.{policy_name}.* Variables

Set after an `OAuthV2` policy with operation `VerifyAccessToken` executes.

| Variable | Description |
|---|---|
| `oauthv2accesstoken.{policy_name}.access_token` | The access token string |
| `oauthv2accesstoken.{policy_name}.token_type` | Token type, typically `Bearer` |
| `oauthv2accesstoken.{policy_name}.expires_in` | Seconds until the token expires |
| `oauthv2accesstoken.{policy_name}.refresh_token` | The refresh token, if issued |
| `oauthv2accesstoken.{policy_name}.scope` | Scopes associated with the token |
| `oauthv2accesstoken.{policy_name}.status` | Token status: `approved` or `revoked` |
| `oauthv2accesstoken.{policy_name}.developer.id` | Developer ID associated with the token |
| `oauthv2accesstoken.{policy_name}.developer.app.name` | Developer app name |

### ratelimit.{policy_name}.* Variables

Set after a `Quota` or `SpikeArrest` policy executes.

| Variable | Description |
|---|---|
| `ratelimit.{policy_name}.allowed.count` | Maximum number of requests allowed in the interval |
| `ratelimit.{policy_name}.used.count` | Number of requests consumed so far |
| `ratelimit.{policy_name}.available.count` | Number of remaining requests in the current interval |
| `ratelimit.{policy_name}.exceed.count` | Number of requests that exceeded the limit (1 if exceeded on this call) |
| `ratelimit.{policy_name}.expiry.time` | UTC time when the current quota window resets |
| `ratelimit.{policy_name}.failed` | Boolean: true if the policy failed (quota exceeded) |

### Other Useful Variables

| Variable | Description |
|---|---|
| `messageid` | Unique message ID for the API call |
| `current.flow.name` | Name of the currently executing flow |
| `current.flow.description` | Description of the currently executing flow |
| `route.name` | Name of the RouteRule that was matched |
| `route.target` | Name of the TargetEndpoint selected by routing |
| `virtualhost.name` | Name of the virtual host that received the request |
| `loadbalancing.selected.url` | URL selected by the load balancer (when using TargetServer with load balancing) |
| `loadbalancing.targetserver` | Name of the TargetServer selected |
| `is.error` | Boolean: true when the proxy is in an error state |

---

## Variable Availability by Flow Phase

Not all variables are populated in every phase. This table shows which variable groups are available and their read/write status in each phase.

| Variable Group | Proxy Request | Target Request | Target Response | Proxy Response | Error Flow | PostClientFlow |
|---|---|---|---|---|---|---|
| `request.*` | Read/Write | Read/Write | -- | -- | -- | -- |
| `response.*` | -- | -- | Read | Read/Write | -- | Read |
| `message.*` | = request | = request | = response | = response | = error | = response |
| `proxy.*` | Read | Read | Read | Read | Read | Read |
| `target.url` | -- | **Read/Write** | Read | Read | Read | Read |
| `target.*` (other) | -- | Read | Read | Read | Read | Read |
| `client.*` | Read | Read | Read | Read | Read | Read |
| `client.sent.end.timestamp` | -- | -- | -- | -- | -- | **Read** |
| `error.*`, `fault.*` | -- | -- | -- | -- | Read | -- |
| `is.error` | Read | Read | Read | Read | **true** | Read |
| `system.*` | Read | Read | Read | Read | Read | Read |
| `apiproxy.*`, `environment.*` | Read | Read | Read | Read | Read | Read |
| `apiproduct.*` | After verify | After verify | After verify | After verify | After verify | After verify |
| Custom variables | Read/Write | Read/Write | Read/Write | Read/Write | Read/Write | Read |

---

## Scope Rules and Custom Variables

`request.*` variables are **not available** in the response phase. `response.*` variables only exist in the response phase. To pass data across phases, store values in custom variables during the request phase:

```xml
<AssignMessage name="Store-Request-Verb">
  <AssignVariable>
    <Name>custom.original_verb</Name>
    <Ref>request.verb</Ref>
  </AssignVariable>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <AssignTo createNew="false" transport="http" type="request"/>
</AssignMessage>
```

The custom variable `custom.original_verb` is then available in the response phase.

Create with **AssignMessage** (when both `Ref` and `Value` are present, `Value` is the fallback if `Ref` is null):

```xml
<AssignMessage name="Set-Custom-Variables">
  <AssignVariable>
    <Name>custom.client_tier</Name>
    <Value>standard</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>custom.user_id</Name>
    <Ref>request.queryparam.user_id</Ref>
    <Value>anonymous</Value> <!-- fallback if Ref is null -->
  </AssignVariable>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <AssignTo createNew="false" transport="http" type="request"/>
</AssignMessage>
```

Create with **JavaScript** using `context.setVariable()` / `context.getVariable()`:

```javascript
context.setVariable("custom.client_tier", "premium");
context.setVariable("custom.request_id", context.getVariable("system.uuid"));
var segments = context.getVariable("proxy.pathsuffix").split("/");
if (segments.length > 1) context.setVariable("custom.resource_type", segments[1]);
```

---

## Condition Syntax

### Complete Operator Reference

#### Relational Operators

| Operator | Alternate Forms | Description | Example |
|---|---|---|---|
| `=` | `Equals`, `Is` | Equals (case sensitive) | `request.verb = "GET"` |
| `!=` | `NotEquals`, `IsNot` | Not equals (case sensitive) | `request.verb != "OPTIONS"` |
| `:=` | `EqualsCaseInsensitive` | Equals (case insensitive) | `request.header.Accept := "application/json"` |
| `>` | `GreaterThan` | Greater than | `response.status.code > 399` |
| `>=` | `GreaterThanOrEquals` | Greater than or equals | `response.status.code >= 400` |
| `<` | `LesserThan` | Less than (use `&lt;` in XML) | `response.status.code &lt; 300` |
| `<=` | `LesserThanOrEquals` | Less than or equals (use `&lt;=` in XML) | `request.content.length &lt;= 1048576` |

#### String and Pattern Operators

| Operator | Alternate Forms | Description | Example |
|---|---|---|---|
| `~` | `Matches`, `Like` | Glob-style pattern match with `*` wildcard (case sensitive) | `request.path ~ "/api/*/users"` |
| `~~` | `JavaRegex` | Java regex match (case sensitive) | `request.path ~~ "/api/v[0-9]+/.*"` |
| `~/` | `MatchesPath`, `LikePath` | Path expression match with `*` and `**` wildcards (case sensitive) | `proxy.pathsuffix MatchesPath "/users/*/orders"` |
| `=\|` | `StartsWith` | Matches the first characters of a string (case sensitive) | `request.path =\| "/api/v2"` |

#### Logical Operators

| Operator | Alternate Forms | Description |
|---|---|---|
| `and` | `AND`, `&&` | Logical AND |
| `or` | `OR`, `\|\|` | Logical OR |
| `!` | `Not`, `not` | Logical NOT (prefix) |

**Common confusion: `~` vs `~~` vs `~/`**
- `~` (`Matches`/`Like`): glob-style matching using `*` as wildcard. NOT regex. The `*` matches zero or more of ANY characters including `/` path separators. Example: `proxy.pathsuffix ~ "/cat*"` matches `/cat`, `/cat123`, and `/cat/bird/mouse`. Use `MatchesPath` instead if you need path-segment-aware matching.
- `~~` (`JavaRegex`): full Java regex. Example: `request.path ~~ "/api/v[0-9]+/users"` where `[0-9]+` is a regex character class.
- `~/` (`MatchesPath`/`LikePath`): path-segment-aware matching. `*` matches one segment, `**` matches one or more segments. Example: `proxy.pathsuffix MatchesPath "/users/*/orders/**"`.
- Escape `*` in `Matches` with `%`: `proxy.pathsuffix ~ "/c%*at"` matches literal `c*at`.

#### Null Checks

| Expression | Description |
|---|---|
| `variable = null` | True if the variable is not set or is null |
| `variable != null` | True if the variable is set and is not null |

#### Boolean Checks

| Expression | Description |
|---|---|
| `variable = true` | True if the variable is a Boolean true value |
| `variable = false` | True if the variable is a Boolean false value |

### MatchesPath Wildcards -- Deep Dive

The `MatchesPath` (or `~/`) operator supports two wildcard types for matching URI path segments:

**Single asterisk `*` -- matches exactly one path segment:**

| Pattern | Matches | Does NOT Match |
|---|---|---|
| `/users/*` | `/users/123` | `/users`, `/users/123/orders` |
| `/users/*/orders` | `/users/123/orders` | `/users/orders`, `/users/123/orders/456` |
| `/v1/*/items/*` | `/v1/catalog/items/789` | `/v1/a/b/items/789` |

**Double asterisk `**` -- matches one or more path segments:**

| Pattern | Matches | Does NOT Match |
|---|---|---|
| `/users/**` | `/users/123`, `/users/123/orders`, `/users/123/orders/456` | `/user/123`, `/users` (zero segments) |
| `/api/**/status` | `/api/v1/status`, `/api/v1/health/status` | `/api/v1/status/detail` |

Note: `**` requires at least one path segment after the prefix. `/users/**` does NOT match `/users` alone (zero trailing segments). Use a separate condition or `OR` to handle the base path: `(proxy.pathsuffix MatchesPath "/users/**") or (proxy.pathsuffix = "/users")`.

**Combining both wildcards:**

```xml
<!-- Match any single user's nested resources to any depth -->
<Condition>proxy.pathsuffix MatchesPath "/users/*/orders/**"</Condition>
<!-- Matches: /users/123/orders, /users/123/orders/456, /users/123/orders/456/items -->
<!-- Does NOT match: /users/orders, /users/123/456/orders -->
```

### XML Escaping in Conditions

Because conditions are written inside XML elements, angle bracket characters must be escaped:

| Character | XML Escape | Usage in Condition |
|---|---|---|
| `<` | `&lt;` | `<Condition>response.status.code &lt; 300</Condition>` |
| `>` | `&gt;` | `<Condition>response.status.code &gt;= 400</Condition>` |

**Correct usage:**

```xml
<Condition>response.status.code &gt;= 400</Condition>
```

**Incorrect (will cause XML parse error):**

```xml
<!-- WRONG: raw > and < will break XML parsing -->
<Condition>response.status.code >= 400</Condition>
```

The `=` and `!=` operators do not need escaping. The `~`, `MatchesPath`, `and`, and `or` operators do not need escaping.

### Type Coercion Rules

- **Default:** All comparisons are string comparisons
- **Numeric:** When both sides of a relational operator are numeric values, automatic numeric comparison is used. This is why `response.status.code >= 400` works correctly (comparing 400 as a number, not as the string "400")
- **Boolean:** Variables containing Boolean values can be compared with `= true` or `= false`
- **Null:** A variable that has not been set evaluates as null. Use `= null` or `!= null` to test

### Operator Precedence

**Warning: Apigee's precedence differs from most programming languages.** The `||` (OR) operator has HIGHER precedence than `&&` (AND):

1. `!` (NOT) — highest
2. `||` / `or` (OR)
3. `&&` / `and` (AND) — lowest

This means `A && B || C && D` is evaluated as `A && (B || C) && D`, NOT `(A && B) || (C && D)`.

**Best practice:** ALWAYS use parentheses to make precedence explicit. Never rely on default precedence with mixed `and`/`or`:

```xml
<!-- Ambiguous without parentheses -->
<Condition>request.verb = "GET" or request.verb = "HEAD" and proxy.pathsuffix MatchesPath "/users"</Condition>

<!-- Clear with parentheses -->
<Condition>(request.verb = "GET" or request.verb = "HEAD") and (proxy.pathsuffix MatchesPath "/users")</Condition>
```

### Comprehensive Condition Examples

```xml
<!-- 1. Path + verb matching for REST routing -->
<Condition>(proxy.pathsuffix MatchesPath "/users") and (request.verb = "GET")</Condition>

<!-- 2. Required header check -->
<Condition>request.header.Authorization = null</Condition>

<!-- 3. Query parameter value check -->
<Condition>request.queryparam.version = "2"</Condition>

<!-- 4. API product-based access control -->
<Condition>apiproduct.name = "Premium-Product"</Condition>

<!-- 5. Regex match on request path -->
<Condition>request.path ~ "/api/v[0-9]+/users/[a-f0-9-]+"</Condition>

<!-- 6. Response error code range (note XML escaping) -->
<Condition>(response.status.code &gt;= 500) and (response.status.code &lt;= 599)</Condition>

<!-- 7. Complex multi-condition with DELETE restriction -->
<Condition>(proxy.pathsuffix MatchesPath "/orders/*") and (request.verb = "DELETE") and (apiproduct.name = "admin")</Condition>

<!-- 8. Negated regex to exclude file extensions -->
<Condition>request.path !~ ".*\\.(css|js|png|jpg|gif)$"</Condition>

<!-- 9. Boolean variable check (is.error) -->
<Condition>is.error = true</Condition>

<!-- 10. Null check combined with value check -->
<Condition>(request.header.X-API-Version != null) and (request.header.X-API-Version != "1")</Condition>

<!-- 11. Multiple fault name matching in FaultRule -->
<Condition>(fault.name = "InvalidAccessToken") or (fault.name = "AccessTokenExpired") or (fault.name = "InvalidAPIKey")</Condition>

<!-- 12. Content-type check with regex -->
<Condition>request.header.Content-Type ~ "application/json.*"</Condition>

<!-- 13. Rate limit exceeded check -->
<Condition>ratelimit.Quota-Policy.failed = true</Condition>
```

### Condition Placement

Conditions are used in four locations, each controlling different behavior:

```xml
<!-- 1. Flows: determines which conditional flow executes -->
<Flow name="GetUsers">
  <Condition>(proxy.pathsuffix MatchesPath "/users") and (request.verb = "GET")</Condition>
  <Request><Step><Name>Get-Users-Policy</Name></Step></Request>
</Flow>

<!-- 2. Steps: determines if a policy executes within a flow -->
<Step>
  <Name>Cache-Lookup</Name>
  <Condition>request.verb = "GET"</Condition>
</Step>

<!-- 3. RouteRules: determines target endpoint routing -->
<RouteRule name="v2-backend">
  <Condition>request.header.X-API-Version = "2"</Condition>
  <TargetEndpoint>v2-target</TargetEndpoint>
</RouteRule>

<!-- 4. FaultRules: determines error handling -->
<FaultRule name="AuthFailure">
  <Condition>(fault.name = "InvalidAccessToken") or (fault.name = "InvalidAPIKey")</Condition>
  <Step><Name>Send-Auth-Error</Name></Step>
</FaultRule>
```

---

## Message Templates

Message templates provide dynamic string substitution using `{variable.name}` syntax. They allow you to embed flow variable values and call built-in functions within policy configuration elements.

### Syntax

Basic variable substitution:

```
{variable.name}
```

With a default value (used when the variable is null):

```
{variable.name:defaultValue}
```

Examples:

```
{request.header.X-Request-ID}
{request.queryparam.format:json}
{system.uuid}
```

### Where Templates Work

Message templates are supported in these policy elements:

| Policy | Supported Elements |
|---|---|
| **AssignMessage** | Payload, Headers (Name and Value), QueryParams (Name and Value), FormParams (Name and Value), StatusCode, ReasonPhrase, Path, Verb |
| **RaiseFault** | Same elements as AssignMessage (Payload, Headers, StatusCode, ReasonPhrase) |
| **ServiceCallout** | URL, Headers, Payload |
| **MessageLogging** | Message content (Syslog and CloudLogging) |
| **JWT** (GenerateJWT) | AdditionalClaims, AdditionalHeaders |
| **JWS** (GenerateJWS) | AdditionalHeaders, Payload |
| **OASValidation** | OASResource |

### Where Templates DO NOT Work

- **Condition elements** -- conditions reference variable names directly without braces
- **Property values** in `<HTTPTargetConnection>` / `<Properties>`
- **Policy name** attributes
- **Ref** attributes in AssignVariable (use the variable name directly)

```xml
<!-- WRONG: braces in a condition -->
<Condition>{request.verb} = "GET"</Condition>

<!-- RIGHT: variable name directly in a condition -->
<Condition>request.verb = "GET"</Condition>
```

### Template Functions -- Complete Reference

Message templates support a library of built-in functions. Functions are called inside the curly braces.

#### String Functions

| Function | Description | Example |
|---|---|---|
| `substring(str, start, end)` | Extract a substring by index | `{substring(request.path, 0, 5)}` |
| `replaceAll(str, regex, replacement)` | Replace all regex matches | `{replaceAll(request.path, "/v[0-9]+", "/v2")}` |
| `replaceFirst(str, regex, replacement)` | Replace first regex match | `{replaceFirst(request.content, "oldVal", "newVal")}` |
| `toUpperCase(str)` | Convert to uppercase | `{toUpperCase(request.verb)}` |
| `toLowerCase(str)` | Convert to lowercase | `{toLowerCase(request.header.Accept)}` |
| `split(str, separator)` | Split string, returns first element | `{split(request.header.Authorization, " ")}` |

#### Encoding Functions

| Function | Description | Example |
|---|---|---|
| `encodeBase64(str)` | Base64 encode | `{encodeBase64(request.content)}` |
| `decodeBase64(str)` | Base64 decode | `{decodeBase64(request.header.X-Data)}` |
| `encodeHTML(str)` | HTML-encode special characters | `{encodeHTML(error.message)}` |
| `escapeJSON(str)` | Escape a string for safe JSON embedding | `{escapeJSON(error.message)}` |
| `escapeXML(str)` | Escape for XML 1.0 | `{escapeXML(request.content)}` |
| `escapeXML11(str)` | Escape for XML 1.1 | `{escapeXML11(request.content)}` |

#### Hash Functions (Hex Output)

| Function | Description |
|---|---|
| `md5Hex(str)` | MD5 hash, hex-encoded |
| `sha1Hex(str)` | SHA-1 hash, hex-encoded |
| `sha256Hex(str)` | SHA-256 hash, hex-encoded |
| `sha384Hex(str)` | SHA-384 hash, hex-encoded |
| `sha512Hex(str)` | SHA-512 hash, hex-encoded |

Example: `{sha256Hex(request.content)}`

#### Hash Functions (Base64 Output)

| Function | Description |
|---|---|
| `md5Base64(str)` | MD5 hash, base64-encoded |
| `sha1Base64(str)` | SHA-1 hash, base64-encoded |
| `sha256Base64(str)` | SHA-256 hash, base64-encoded |
| `sha384Base64(str)` | SHA-384 hash, base64-encoded |
| `sha512Base64(str)` | SHA-512 hash, base64-encoded |

#### HMAC Functions

| Function | Description |
|---|---|
| `hmacSha256(key, valueToSign [, keyencoding [, outputencoding]])` | HMAC-SHA256 signature |
| `hmacSha1(key, valueToSign [, keyencoding [, outputencoding]])` | HMAC-SHA1 signature |
| `hmacSha384(key, valueToSign [, keyencoding [, outputencoding]])` | HMAC-SHA384 signature |
| `hmacSha512(key, valueToSign [, keyencoding [, outputencoding]])` | HMAC-SHA512 signature |
| `hmacMd5(key, valueToSign [, keyencoding [, outputencoding]])` | HMAC-MD5 signature |

The optional `keyencoding` parameter accepts `utf-8` (default), `base64`, or `hex`. The optional `outputencoding` parameter accepts `base64` (default) or `hex`.

Example: `{hmacSha256(private.secret_key, request.content, "utf-8", "hex")}`

#### Time Functions

| Function | Description |
|---|---|
| `timeFormat(format, str)` | Format epoch seconds using local timezone |
| `timeFormatMs(format, str)` | Format epoch milliseconds using local timezone |
| `timeFormatUTC(format, str)` | Format epoch seconds using UTC |
| `timeFormatUTCMs(format, str)` | Format epoch milliseconds using UTC |

The format string follows Java `SimpleDateFormat` patterns: `yyyy-MM-dd'T'HH:mm:ss.SSS'Z'`

Example: `{timeFormatUTCMs("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", system.timestamp)}`

#### JSON and XML Query Functions

| Function | Description |
|---|---|
| `jsonPath(json_path, json_var [, want_array])` | Extract a value from a JSON variable using JSONPath |
| `xpath(xpath_expr, xml_string [, datatype])` | Extract a value from XML using XPath |

Example: `{jsonPath("$.user.name", response.content)}`

#### Utility Functions

| Function | Description | Example |
|---|---|---|
| `createUuid()` | Generate a random UUID | `{createUuid()}` |
| `randomLong([min [, max]])` | Generate a random long integer | `{randomLong(1000, 9999)}` |
| `firstnonnull(var1, varN)` | Return the first non-null argument | `{firstnonnull(request.header.X-ID, system.uuid)}` |
| `xeger(regex)` | Generate a random string matching the regex | `{xeger("[A-Z]{3}-[0-9]{4}")}` |

### Function Syntax Rules

1. **No spaces** inside function parentheses:
   - Correct: `{toLowerCase(request.header.name)}`
   - Incorrect: `{toLowerCase( request.header.name )}`

2. **No nested functions** -- you cannot call a function inside another function:
   - Incorrect: `{toUpperCase(substring(request.path, 0, 5))}`
   - Workaround: Use AssignMessage to store intermediate values in variables

3. **Variables inside functions** are referenced by name without braces:
   - Correct: `{toUpperCase(request.header.name)}`
   - Incorrect: `{toUpperCase({request.header.name})}`

4. **String literals** inside functions are not quoted:
   - Correct: `{replaceAll(request.path, /v1, /v2)}`

### Practical Template Examples

**AssignMessage with createUuid, sha256Hex, and timeFormatUTCMs:**

```xml
<AssignMessage name="Add-Correlation-Headers">
  <Set>
    <Headers>
      <Header name="X-Correlation-ID">{createUuid()}</Header>
      <Header name="X-Request-Hash">{sha256Hex(request.content)}</Header>
      <Header name="X-Timestamp">{timeFormatUTCMs("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", system.timestamp)}</Header>
    </Headers>
  </Set>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
  <AssignTo createNew="false" transport="http" type="request"/>
</AssignMessage>
```

**RaiseFault with default values and escapeJSON:**

```xml
<RaiseFault name="Raise-Custom-Error">
  <FaultResponse>
    <Set>
      <Payload contentType="application/json">
{
  "error": {
    "code": "{error.status.code:500}",
    "message": "{escapeJSON(error.message:An unexpected error occurred)}",
    "request_id": "{system.uuid}",
    "timestamp": "{timeFormatUTCMs("yyyy-MM-dd'T'HH:mm:ss'Z'", system.timestamp)}"
  }
}
      </Payload>
      <StatusCode>{error.status.code:500}</StatusCode>
      <ReasonPhrase>{error.reason.phrase:Internal Server Error}</ReasonPhrase>
    </Set>
  </FaultResponse>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</RaiseFault>
```

**ServiceCallout with dynamic URL using variables:**

```xml
<ServiceCallout name="Call-User-Service">
  <Request>
    <Set>
      <Headers>
        <Header name="Authorization">Bearer {private.service_token}</Header>
        <Header name="X-Correlation-ID">{firstnonnull(request.header.X-Correlation-ID, system.uuid)}</Header>
        <Header name="Content-Type">application/json</Header>
      </Headers>
      <Payload contentType="application/json">
        {"user_id": "{request.queryparam.user_id:unknown}", "action": "{toLowerCase(request.verb)}"}
      </Payload>
    </Set>
  </Request>
  <Response>callout.user_service_response</Response>
  <HTTPTargetConnection>
    <URL>https://user-service.internal/api/v1/users/{request.queryparam.user_id}</URL>
  </HTTPTargetConnection>
</ServiceCallout>
```

**MessageLogging with jsonPath extraction:**

```xml
<MessageLogging name="Log-Request-Details">
  <CloudLogging>
    <LogName>projects/{organization.name}/logs/apigee-access</LogName>
    <Message contentType="application/json">
{
  "timestamp": "{timeFormatUTCMs("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", system.timestamp)}",
  "proxy": "{apiproxy.name}",
  "revision": "{apiproxy.revision}",
  "environment": "{environment.name}",
  "client_ip": "{proxy.client.ip}",
  "verb": "{request.verb}",
  "path": "{proxy.pathsuffix}",
  "status_code": "{response.status.code}",
  "user_agent": "{request.header.User-Agent:unknown}",
  "correlation_id": "{firstnonnull(request.header.X-Correlation-ID, system.uuid)}",
  "response_user": "{jsonPath("$.user.name", response.content)}"
}
    </Message>
  </CloudLogging>
</MessageLogging>
```

---

See also: [Flows and Execution](flows_and_execution.md) | [Mediation Policies](policies_mediation.md) | [Fault Handling](fault_handling.md) | [Endpoints and Routing](endpoints_and_routing.md)
