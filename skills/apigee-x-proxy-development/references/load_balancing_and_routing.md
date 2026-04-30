# Load Balancing, Target Servers, and Health Monitors

This reference covers Apigee X load balancing, target server management,
health monitoring, and advanced routing patterns.

---

## Target Servers

Environment-level named backend definitions that decouple proxy config from concrete URLs:

- Defined per environment (dev, staging, prod can each point to different hosts)
- Can be updated without redeploying the proxy
- Enable load balancing across multiple backends

### Creating via REST API

```bash
curl -X POST "https://apigee.googleapis.com/v1/organizations/{org}/environments/{env}/targetservers" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"backend-1","host":"api.example.com","port":443,"protocol":"HTTP","isEnabled":true}'
```

### Supported Protocol Values

| Protocol | Use Case |
|---|---|
| `HTTP` | Standard HTTP/HTTPS backends (default) |
| `HTTP2` | HTTP/2 backends for multiplexed connections |
| `GRPC` | gRPC backends (used with gRPC proxy type) |
| `GRPC_TARGET` | gRPC target for non-gRPC proxies |
| `EXTERNAL_CALLOUT` | External callout servers for custom processing |

---

## Referencing Target Servers in TargetEndpoint

Reference named target servers through `<LoadBalancer>` inside `<HTTPTargetConnection>`:

```xml
<TargetEndpoint name="default">
  <HTTPTargetConnection>
    <LoadBalancer>
      <Server name="backend-1"/>
      <Server name="backend-2"/>
    </LoadBalancer>
    <Path>/api/v1</Path>
  </HTTPTargetConnection>
</TargetEndpoint>
```

**Important**: `<LoadBalancer>` and `<URL>` are mutually exclusive in `<HTTPTargetConnection>`.

---

## Load Balancing Algorithms

### RoundRobin (Default)

Sequential distribution, one request per server in order:

```xml
<LoadBalancer>
  <Algorithm>RoundRobin</Algorithm>
  <Server name="server-1"/>
  <Server name="server-2"/>
  <Server name="server-3"/>
</LoadBalancer>
```

Best for homogeneous backends with similar capacity.

### Weighted (WeightedRoundRobin)

Proportional distribution based on weight values:

```xml
<LoadBalancer>
  <Algorithm>Weighted</Algorithm>
  <Server name="powerful-server"><Weight>3</Weight></Server>
  <Server name="standard-server"><Weight>1</Weight></Server>
</LoadBalancer>
```

Result: powerful-server gets 75% traffic, standard-server 25%. Weight values are
relative -- only the ratio matters.

### LeastConnections

Routes each request to the server with the fewest active connections:

```xml
<LoadBalancer>
  <Algorithm>LeastConnections</Algorithm>
  <Server name="server-1"/>
  <Server name="server-2"/>
</LoadBalancer>
```

Best for long-lived connections or variable response times.

---

## MaxFailures and Failover

### MaxFailures Behavior

```xml
<LoadBalancer>
  <Server name="primary-1"/>
  <Server name="primary-2"/>
  <MaxFailures>5</MaxFailures>
  <RetryEnabled>true</RetryEnabled>
</LoadBalancer>
```

- Tracks consecutive I/O failures per server
- When a server reaches MaxFailures consecutive failures, it is removed from rotation
- **Without HealthMonitor**: server never auto-recovers (needs proxy redeploy)
- **With HealthMonitor**: server auto-recovers when health check passes
- **Default MaxFailures=0**: never remove server from rotation

### RetryEnabled

- When `true`: on I/O failure, automatically retry on next server
- Only retries on I/O exceptions and timeouts, NOT HTTP error codes (4xx/5xx)
- Requires minimum 2 servers in LoadBalancer

### IsFallback Servers

```xml
<LoadBalancer>
  <Algorithm>RoundRobin</Algorithm>
  <Server name="primary-1"/>
  <Server name="primary-2"/>
  <Server name="dr-fallback">
    <IsFallback>true</IsFallback>
  </Server>
  <MaxFailures>3</MaxFailures>
</LoadBalancer>
```

- Only **one** server can have IsFallback=true
- Fallback only receives traffic when **all** primary servers are down
- If fallback is also down, Apigee returns 503
- Use for disaster recovery or degraded-mode backends

---

## Health Monitors

Periodic checks against target servers that enable automatic recovery of servers
removed from rotation by MaxFailures.

### HTTPMonitor -- Complete Configuration

```xml
<HTTPTargetConnection>
  <LoadBalancer>
    <Algorithm>RoundRobin</Algorithm>
    <Server name="backend-1"/>
    <Server name="backend-2"/>
    <MaxFailures>3</MaxFailures>
  </LoadBalancer>
  <HealthMonitor>
    <IsEnabled>true</IsEnabled>
    <IntervalInSec>10</IntervalInSec>
    <HTTPMonitor>
      <ConnectTimeoutInSec>5</ConnectTimeoutInSec>
      <SocketReadTimeoutInSec>10</SocketReadTimeoutInSec>
      <UseTargetServerSSLInfo>true</UseTargetServerSSLInfo>
      <Request>
        <Verb>GET</Verb>
        <Path>/health</Path>
        <Header name="User-Agent">Apigee-HealthCheck</Header>
        <IncludeHealthCheckIdHeader>true</IncludeHealthCheckIdHeader>
      </Request>
      <SuccessResponse>
        <ResponseCode>200</ResponseCode>
        <Header name="X-Health">OK</Header>
      </SuccessResponse>
    </HTTPMonitor>
  </HealthMonitor>
</HTTPTargetConnection>
```

### HTTPMonitor Element Reference

| Element | Description |
|---|---|
| `IsEnabled` | Enable/disable health checks |
| `IntervalInSec` | Check frequency in seconds; each server checked independently |
| `ConnectTimeoutInSec` | TCP connection timeout for the health check |
| `SocketReadTimeoutInSec` | Response read timeout after connecting |
| `UseTargetServerSSLInfo` | Use target's SSL config for health check; set `true` for HTTPS |
| `Request > Verb` | HTTP method (GET, POST, etc.) |
| `Request > Path` | URL path for the health check endpoint |
| `Request > Header` | Custom headers; multiple supported |
| `IncludeHealthCheckIdHeader` | Adds `X-Apigee-Healthcheck-Id` unique header for backend logging |
| `SuccessResponse > ResponseCode` | HTTP status code that indicates healthy; must match exactly |
| `SuccessResponse > Header` | Optional header check; both name and value must match |

### Health Check Lifecycle

```
server UP --> health check runs every IntervalInSec
  --> check fails --> failure count++
  --> failure count >= MaxFailures --> server marked DOWN, removed from rotation
  --> health check continues running against DOWN server
  --> check passes --> failure count reset to 0 --> server marked UP, returned to rotation
```

### TCPMonitor

```xml
<HealthMonitor>
  <IsEnabled>true</IsEnabled>
  <IntervalInSec>5</IntervalInSec>
  <TCPMonitor>
    <ConnectTimeoutInSec>5</ConnectTimeoutInSec>
    <Port>443</Port>
  </TCPMonitor>
</HealthMonitor>
```

- Simpler than HTTPMonitor: only checks TCP connectivity
- Port is optional (uses TargetServer port if omitted)
- Best for simple liveness checks or non-HTTP backends

---

## Advanced Routing Patterns

### Conditional RouteRules to Multiple TargetEndpoints

```xml
<RouteRule name="v2-api">
  <Condition>request.header.X-API-Version = "2"</Condition>
  <TargetEndpoint>BackendV2</TargetEndpoint>
</RouteRule>
<RouteRule name="default">
  <TargetEndpoint>BackendV1</TargetEndpoint>
</RouteRule>
```

- Evaluated top-to-bottom, first match wins
- Default (no condition) MUST be last
- Each TargetEndpoint can have its own LoadBalancer and HealthMonitor

### Geo-Routing with Load Balancing per Region

```xml
<RouteRule name="us-region">
  <Condition>request.header.X-Region = "us"</Condition>
  <TargetEndpoint>UsBackend</TargetEndpoint>
</RouteRule>
<RouteRule name="eu-region">
  <Condition>request.header.X-Region = "eu"</Condition>
  <TargetEndpoint>EuBackend</TargetEndpoint>
</RouteRule>
<RouteRule name="default-region">
  <TargetEndpoint>UsBackend</TargetEndpoint>
</RouteRule>
```

Each TargetEndpoint maintains its own LoadBalancer + HealthMonitor for independent
failover per region.

### Blue-Green / Canary Deployments

Route percentage of traffic to new backend version using Weighted algorithm:

```xml
<LoadBalancer>
  <Algorithm>Weighted</Algorithm>
  <Server name="backend-blue"><Weight>9</Weight></Server>
  <Server name="backend-green"><Weight>1</Weight></Server>
</LoadBalancer>
```

Start with 90/10 split, gradually shift weight. Update via API without redeploying.

### Dynamic target.url Routing

Set `target.url` dynamically in JavaScript or AssignMessage:

```xml
<AssignMessage name="AM-SetDynamicTarget">
  <AssignVariable>
    <Name>target.url</Name>
    <Value>https://dynamic-backend.example.com/api</Value>
  </AssignVariable>
</AssignMessage>
```

**Important**: Must be set in the **TargetEndpoint request flow**, not ProxyEndpoint.

---

## Endpoint Properties Reference

```xml
<HTTPTargetConnection>
  <Properties>
    <Property name="connect.timeout.millis">5000</Property>
    <Property name="io.timeout.millis">30000</Property>
    <Property name="keepalive.timeout.millis">60000</Property>
    <Property name="request.streaming.enabled">true</Property>
    <Property name="response.streaming.enabled">true</Property>
  </Properties>
  <LoadBalancer>
    <Server name="backend-1"/>
  </LoadBalancer>
</HTTPTargetConnection>
```

| Property | Default | Description |
|---|---|---|
| `connect.timeout.millis` | 3000 | TCP connection timeout |
| `io.timeout.millis` | 55000 | I/O read timeout after connection |
| `keepalive.timeout.millis` | 60000 | Idle connection keepalive |
| `request.streaming.enabled` | false | Stream requests without buffering |
| `response.streaming.enabled` | false | Stream responses without buffering |
| `request.retain.headers` | all | Headers to forward to backend |
| `retain.queryparams` | all | Query params to forward |

**Note**: Property values must be literals (no variable substitution).

---

## Complete Production Example

A comprehensive TargetEndpoint combining all features:

```xml
<TargetEndpoint name="ProductionBackend">
  <PreFlow name="PreFlow">
    <Request/>
    <Response/>
  </PreFlow>
  <PostFlow name="PostFlow">
    <Request/>
    <Response/>
  </PostFlow>
  <HTTPTargetConnection>
    <Properties>
      <Property name="connect.timeout.millis">5000</Property>
      <Property name="io.timeout.millis">30000</Property>
      <Property name="keepalive.timeout.millis">60000</Property>
    </Properties>
    <SSLInfo>
      <Enabled>true</Enabled>
      <ClientAuthEnabled>false</ClientAuthEnabled>
      <TrustStore>ref://myTrustStoreRef</TrustStore>
      <IgnoreValidationErrors>false</IgnoreValidationErrors>
    </SSLInfo>
    <LoadBalancer>
      <Algorithm>Weighted</Algorithm>
      <Server name="prod-backend-1"><Weight>3</Weight></Server>
      <Server name="prod-backend-2"><Weight>3</Weight></Server>
      <Server name="prod-backend-3"><Weight>2</Weight></Server>
      <Server name="prod-dr-fallback">
        <IsFallback>true</IsFallback>
      </Server>
      <MaxFailures>5</MaxFailures>
      <RetryEnabled>true</RetryEnabled>
    </LoadBalancer>
    <HealthMonitor>
      <IsEnabled>true</IsEnabled>
      <IntervalInSec>10</IntervalInSec>
      <HTTPMonitor>
        <ConnectTimeoutInSec>5</ConnectTimeoutInSec>
        <SocketReadTimeoutInSec>10</SocketReadTimeoutInSec>
        <UseTargetServerSSLInfo>true</UseTargetServerSSLInfo>
        <Request>
          <Verb>GET</Verb>
          <Path>/health</Path>
          <Header name="User-Agent">Apigee-HealthCheck</Header>
          <IncludeHealthCheckIdHeader>true</IncludeHealthCheckIdHeader>
        </Request>
        <SuccessResponse>
          <ResponseCode>200</ResponseCode>
        </SuccessResponse>
      </HTTPMonitor>
    </HealthMonitor>
    <Path>/api/v1</Path>
  </HTTPTargetConnection>
</TargetEndpoint>
```

This configuration provides:

- **Weighted load balancing** across three primary servers (3:3:2 ratio)
- **Disaster recovery fallback** to `prod-dr-fallback` when all primaries are down
- **Automatic failover** with MaxFailures=5 and RetryEnabled
- **Health monitoring** every 10 seconds via HTTP GET to `/health`
- **Auto-recovery** of failed servers when health checks pass
- **SSL/TLS** with trust store validation
- **Connection tuning** via endpoint properties

---

## Related References

- [Endpoints and Routing](endpoints_and_routing.md) -- ProxyEndpoint and TargetEndpoint configuration fundamentals
- [Advanced Patterns](advanced_patterns.md) -- Chained proxies, shared flows, and complex integration patterns
