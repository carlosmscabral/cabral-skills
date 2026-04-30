# Endpoints and Routing

This reference covers ProxyEndpoint and TargetEndpoint configuration, route rules, load balancing, TLS, and proxy chaining in Apigee X.

## ProxyEndpoint

The ProxyEndpoint defines how clients connect to the API proxy. It lives in `apiproxy/proxies/`.

### Complete ProxyEndpoint Example

```xml
<ProxyEndpoint name="default">
    <HTTPProxyConnection>
        <BasePath>/v1/orders</BasePath>
        <Properties>
            <Property name="request.streaming.enabled">true</Property>
            <Property name="response.streaming.enabled">true</Property>
            <Property name="request.retain.headers">User-Agent,Accept</Property>
        </Properties>
    </HTTPProxyConnection>

    <PreFlow name="PreFlow">
        <Request>
            <Step><Name>VAK-VerifyKey</Name></Step>
            <Step><Name>SA-RateLimit</Name></Step>
        </Request>
        <Response/>
    </PreFlow>

    <Flows>
        <Flow name="GetOrders">
            <Condition>(proxy.pathsuffix MatchesPath "/") and (request.verb = "GET")</Condition>
            <Request><Step><Name>Q-DeveloperQuota</Name></Step></Request>
            <Response><Step><Name>AM-SetCORSHeaders</Name></Step></Response>
        </Flow>
    </Flows>

    <PostFlow name="PostFlow">
        <Request/>
        <Response><Step><Name>ML-LogToCloudLogging</Name></Step></Response>
    </PostFlow>

    <DefaultFaultRule name="DefaultFault">
        <AlwaysEnforce>true</AlwaysEnforce>
        <Step><Name>AM-BuildErrorResponse</Name></Step>
    </DefaultFaultRule>

    <RouteRule name="default">
        <TargetEndpoint>default</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>
```

**BasePath rules:**
- Must be unique per environment — two proxies in the same environment cannot share a base path
- Limit: 3,000 base paths per environment or environment group
- By default, all data in the request is passed unchanged from ProxyEndpoint to TargetEndpoint

### ProxyEndpoint Properties

| Property | Description | Default |
|----------|-------------|---------|
| `request.streaming.enabled` | Stream request body without buffering. Required for payloads over 10 MB. | `false` |
| `response.streaming.enabled` | Stream response body without buffering. Required for payloads over 10 MB. | `false` |
| `request.retain.headers` | Comma-separated headers to preserve (not removed by Apigee). | All standard headers |

When streaming is enabled, policies that access `request.content` or `response.content` cannot read the payload.

## TargetEndpoint

The TargetEndpoint defines how the proxy connects to the backend. It lives in `apiproxy/targets/`.

### Direct URL Target

```xml
<TargetEndpoint name="default">
    <HTTPTargetConnection>
        <URL>https://backend.example.com/api/orders</URL>
        <Properties>
            <Property name="connect.timeout.millis">5000</Property>
            <Property name="io.timeout.millis">30000</Property>
        </Properties>
    </HTTPTargetConnection>

    <PreFlow name="PreFlow">
        <Request><Step><Name>AM-SetBackendAuth</Name></Step></Request>
        <Response/>
    </PreFlow>
</TargetEndpoint>
```

| Property | Description | Default |
|----------|-------------|---------|
| `connect.timeout.millis` | TCP connection timeout in milliseconds. | `3000` |
| `io.timeout.millis` | Read/write timeout on the socket. | `55000` |
| `request.retain.headers` | Headers to preserve when forwarding to backend. | All standard headers |
| `keepalive.timeout.millis` | Idle timeout for connection pooling. | `60000` |

### Load Balancer Target

Use `<LoadBalancer>` instead of `<URL>` to distribute traffic. `<Algorithm>` accepts `RoundRobin`, `LeastConnections`, or `Weighted`. Servers exceeding `<MaxFailures>` are removed from rotation.

```xml
<TargetEndpoint name="default">
    <HTTPTargetConnection>
        <LoadBalancer>
            <Algorithm>RoundRobin</Algorithm>
            <Server name="server1">
                <Host>backend1.example.com</Host>
                <Port>443</Port>
                <IsEnabled>true</IsEnabled>
                <MaxFailures>3</MaxFailures>
            </Server>
            <Server name="server2">
                <Host>backend2.example.com</Host>
                <Port>443</Port>
                <IsEnabled>true</IsEnabled>
                <MaxFailures>3</MaxFailures>
            </Server>
            <Path>/api/orders</Path>
            <RetryEnabled>true</RetryEnabled>
        </LoadBalancer>
        <SSLInfo><Enabled>true</Enabled></SSLInfo>
    </HTTPTargetConnection>
</TargetEndpoint>
```

### TLS/mTLS Configuration

```xml
<TargetEndpoint name="mtls-backend">
    <HTTPTargetConnection>
        <URL>https://secure-backend.example.com/api</URL>
        <SSLInfo>
            <Enabled>true</Enabled>
            <ClientAuthEnabled>true</ClientAuthEnabled>
            <KeyStore>ref://myKeyStoreRef</KeyStore>
            <KeyAlias>my-client-cert</KeyAlias>
            <TrustStore>ref://myTrustStoreRef</TrustStore>
        </SSLInfo>
    </HTTPTargetConnection>
</TargetEndpoint>
```

| Element | Description |
|---------|-------------|
| `<Enabled>` | Enable TLS. Must be `true` for HTTPS targets. |
| `<ClientAuthEnabled>` | Enable mTLS. The proxy presents a client certificate to the backend. |
| `<KeyStore>` | Reference to keystore with client cert. Use `ref://` prefix. |
| `<KeyAlias>` | Alias of the key entry within the keystore. |
| `<TrustStore>` | Reference to truststore with backend CA cert. Use `ref://` prefix. |
| `<Enforce>` | When `true`, enforces strict hostname validation against CN in the backend certificate. Default: Apigee does NOT validate hostnames. |
| `<CommonName>` | Expected Common Name in the backend cert. Supports wildcards (e.g., `*.example.com`). |
| `<IgnoreValidationErrors>` | When `true`, ignores ALL certificate validation errors (self-signed, expired, wrong CN). **NOT recommended for production.** |

Always use `ref://` references rather than hardcoded keystore names so certificates can be rotated without redeploying the proxy.

### Handling Self-Signed or No-Certificate Backends

**Development/testing with self-signed certificates:**
```xml
<SSLInfo>
  <Enabled>true</Enabled>
  <IgnoreValidationErrors>true</IgnoreValidationErrors>
</SSLInfo>
```
This bypasses ALL certificate validation — self-signed, expired, wrong hostname, untrusted CA. Use ONLY in dev/test environments.

**Production with internal CA:**
```xml
<SSLInfo>
  <Enabled>true</Enabled>
  <TrustStore>ref://internalCATrustStore</TrustStore>
  <Enforce>true</Enforce>
  <CommonName>api.internal.example.com</CommonName>
</SSLInfo>
```
Upload your internal CA certificate to a truststore, then reference it. `Enforce` + `CommonName` ensures hostname validation.

**Production best practices:**
- Never use `<IgnoreValidationErrors>true</IgnoreValidationErrors>` in production
- Always set `<Enforce>true</Enforce>` for hostname validation
- Use `<TrustStore>` with your CA cert rather than disabling validation
- TLS 1.2+ required (Apigee X does not support TLS 1.0 or 1.1)

## RouteRules

RouteRules appear at the bottom of the ProxyEndpoint and determine which TargetEndpoint handles each request. They are evaluated **top-to-bottom; the first match wins**. RouteRules are evaluated **after** all policies in the ProxyEndpoint request pipeline (PreFlow, conditional flows, and PostFlow) have executed.

### Conditional Routing Examples

```xml
<!-- Route by custom header -->
<RouteRule name="route-v2">
    <Condition>request.header.X-Backend-Version = "v2"</Condition>
    <TargetEndpoint>v2-backend</TargetEndpoint>
</RouteRule>

<!-- Route by query parameter -->
<RouteRule name="route-sandbox">
    <Condition>request.queryparam.env = "sandbox"</Condition>
    <TargetEndpoint>sandbox-backend</TargetEndpoint>
</RouteRule>

<!-- Route by API product custom attribute -->
<RouteRule name="route-premium">
    <Condition>verifyapikey.VAK-VerifyKey.apiproduct.tier = "premium"</Condition>
    <TargetEndpoint>premium-backend</TargetEndpoint>
</RouteRule>

<!-- Route by path suffix -->
<RouteRule name="route-admin">
    <Condition>proxy.pathsuffix MatchesPath "/admin/**"</Condition>
    <TargetEndpoint>admin-backend</TargetEndpoint>
</RouteRule>

<!-- Default route (no condition - MUST be last) -->
<RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
</RouteRule>
```

### Direct URL Routing and Null Routes

```xml
<!-- Direct URL: skips TargetEndpoint entirely (no target PreFlow/PostFlow) -->
<RouteRule name="direct-route">
    <Condition>request.header.X-Direct = "true"</Condition>
    <URL>https://direct-backend.example.com/api</URL>
</RouteRule>

<!-- Null route: no backend call, response built in ProxyEndpoint flows -->
<!-- Used for mock APIs, health checks, CORS preflight -->
<RouteRule name="no-target"/>
```

### Evaluation Order

Rules are evaluated in document order -- the first match wins. Place specific rules first; an unconditional default placed first would swallow all traffic.

## LocalTargetConnection (Proxy Chaining)

LocalTargetConnection routes requests to another proxy deployed in the same environment, bypassing the network stack.

```xml
<TargetEndpoint name="chained">
    <LocalTargetConnection>
        <APIProxy>internal-auth-proxy</APIProxy>
        <ProxyEndpoint>default</ProxyEndpoint>
    </LocalTargetConnection>
</TargetEndpoint>
```

| Element | Description |
|---------|-------------|
| `<APIProxy>` | Name of the target proxy (must be deployed in the same environment). |
| `<ProxyEndpoint>` | ProxyEndpoint within the target proxy (typically `default`). |

**Benefits**: No network overhead (no DNS, TLS handshake, or TCP setup), no external URL required, keeps internal calls within the Apigee runtime.

**Billing**: Each proxy in the chain counts as a separate API call. A chain of A -> B -> C counts as three calls.

**Infinite loop prevention**: Apigee X does not automatically prevent chaining loops. If proxy A chains to B and B chains back to A, the request loops until the runtime timeout. Always validate chaining topology to avoid circular references.

---

## Related References

- [Proxy Bundle Anatomy](./proxy_bundle_anatomy.md) -- directory structure, naming conventions, and resource resolution
