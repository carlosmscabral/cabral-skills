# Traffic Management Policies

Traffic management policies protect backend services from excessive load and enforce consumption limits per API consumer. Apigee X provides two complementary mechanisms: **SpikeArrest** for rate smoothing and **Quota** for counter-based SLA enforcement.

---

## SpikeArrest Policy

SpikeArrest throttles the rate of requests flowing to a backend, protecting it from sudden traffic surges. It uses a token bucket algorithm that smooths traffic rather than allowing bursts. A rate of `100pm` does not mean 100 requests can arrive in the first second -- it means roughly 1 request every 0.6 seconds (60 / 100 = 0.6s interval).

Rate syntax uses `Xpm` (per minute) or `Xps` (per second).

### Complete XML Example

```xml
<SpikeArrest name="SA-ProtectBackend">
    <DisplayName>Protect Backend</DisplayName>
    <Rate>100pm</Rate>
    <Identifier ref="request.header.x-api-key"/>
    <UseEffectiveCount>true</UseEffectiveCount>
</SpikeArrest>
```

### Key Elements

| Element | Description |
|---|---|
| `<Rate>` | Static rate value. Examples: `30ps`, `200pm` |
| `<Rate ref="..."/>` | Dynamic rate from a flow variable |
| `<Identifier>` | Applies the rate limit per unique value (e.g., per client IP, per API key) |
| `<UseEffectiveCount>` | When `true`, distributes rate counting across all Apigee instances. Required for accurate enforcement in multi-instance environments |

**Critical:** When `UseEffectiveCount` is `false` (default), each Apigee runtime instance enforces the rate independently. With 3 instances, the effective rate is 3x the configured value. Always set `UseEffectiveCount` to `true` in production for accurate distributed rate limiting.

### Dynamic Rate from a Variable

You can drive the rate from a KVM entry, API product attribute, or any flow variable:

```xml
<SpikeArrest name="SA-DynamicRate">
    <DisplayName>Dynamic SpikeArrest</DisplayName>
    <Rate ref="kvm.spikeRate"/>
    <Identifier ref="developer.app.name"/>
    <UseEffectiveCount>true</UseEffectiveCount>
</SpikeArrest>
```

### Flow Variables Set by SpikeArrest

| Variable | Description |
|---|---|
| `ratelimit.{policy-name}.allowed.count` | The configured rate limit |
| `ratelimit.{policy-name}.used.count` | Current count in the time window |
| `ratelimit.{policy-name}.exceed.count` | Number of requests exceeding the limit |
| `ratelimit.{policy-name}.failed` | `true` if the policy raised a fault |

---

## Quota Policy

Quota enforces consumption limits over extended time periods -- for example, 1000 calls per day or 50 calls per minute per developer. Unlike SpikeArrest, Quota is a **counter**: it increments with each request and rejects traffic once the limit is reached.

### Complete XML Example

```xml
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

### Key Elements

| Element | Description |
|---|---|
| `<Allow count="N"/>` | Static quota limit |
| `<Allow countRef="..."/>` | Dynamic quota from a flow variable |
| `<Interval>` | Number of TimeUnits per quota period |
| `<TimeUnit>` | `minute`, `hour`, `day`, `week`, or `month` |
| `<Distributed>` | Share quota counter across all Apigee instances |
| `<Synchronous>` | Synchronize counter updates in real time (use with `Distributed`) |

**Gotcha:** `Distributed=true` with `Synchronous=false` uses eventual consistency — quota reads may be stale across nodes. Set `Synchronous=true` for accurate enforcement (at slight latency cost). Quota counters reset at the start of each period (e.g., daily quota resets at midnight UTC), not 24 hours from first request.
| `<Identifier>` | Apply separate counters per unique value |

### Weighted Quota (MessageWeight)

Charge different costs per request using `<MessageWeight>`:
```xml
<Quota name="Q-WeightedQuota">
  <Allow count="1000"/>
  <Interval>1</Interval>
  <TimeUnit>day</TimeUnit>
  <Distributed>true</Distributed>
  <Synchronous>true</Synchronous>
  <Identifier ref="request.header.x-api-key"/>
  <MessageWeight ref="custom.request.cost"/>
</Quota>
```
Each request consumes `custom.request.cost` units from the quota (default weight: 1). Use for tiered pricing where premium operations cost more quota units than simple reads.

### Dynamic Quota from API Product

When VerifyAPIKey or OAuthV2 runs first, Apigee populates quota variables from the API product configuration:

```xml
<Quota name="Q-ProductQuota">
    <DisplayName>Product-Driven Quota</DisplayName>
    <Allow countRef="apiproduct.developer.quota.limit"/>
    <Interval ref="apiproduct.developer.quota.interval"/>
    <TimeUnit ref="apiproduct.developer.quota.timeunit"/>
    <Distributed>true</Distributed>
    <Synchronous>true</Synchronous>
    <Identifier ref="client_id"/>
</Quota>
```

### Flow Variables Set by Quota

| Variable | Description |
|---|---|
| `ratelimit.{policy-name}.allowed.count` | The configured quota limit |
| `ratelimit.{policy-name}.used.count` | Current count consumed |
| `ratelimit.{policy-name}.exceed.count` | Number of requests over the limit |
| `ratelimit.{policy-name}.expiry.time` | UTC time when the quota counter resets |
| `ratelimit.{policy-name}.failed` | `true` if the policy raised a fault |

---

## ResetQuota Policy

ResetQuota dynamically decreases the quota counter to grant additional allowance mid-cycle. It does not reset the counter to zero -- it subtracts a specified amount from the used count.

```xml
<ResetQuota name="RQ-GrantExtra">
    <DisplayName>Grant Extra Quota</DisplayName>
    <Quota name="Q-DailyLimit">
        <Identifier ref="request.header.x-api-key"/>
        <Allow>
            <Count>100</Count>
        </Allow>
    </Quota>
</ResetQuota>
```

The `<Quota name="...">` must reference an existing Quota policy. The `<Count>` value is subtracted from the used count, effectively granting that many additional requests.

---

## SpikeArrest vs Quota Decision Guide

| Criteria | SpikeArrest | Quota |
|---|---|---|
| **Purpose** | Backend protection from surges | SLA and consumption enforcement |
| **Mechanism** | Rate smoothing (token bucket) | Counter with time window |
| **Granularity** | Per-second or per-minute | Minute, hour, day, week, month |
| **State** | Minimal state, fast evaluation | Counter state, requires Distributed+Synchronous for accuracy |
| **Typical use** | Prevent backend overload | Enforce "1000 calls/day per developer" |
| **Failure mode** | Returns `429` immediately when rate exceeded | Returns `429` when counter exhausted |

Use SpikeArrest when you need to **protect the backend** from instantaneous traffic spikes. Use Quota when you need to **enforce contractual limits** per API consumer.

---

## Combined Usage Pattern

The recommended pattern is to place both policies in the PreFlow, after credential verification. SpikeArrest provides immediate backend protection while Quota enforces per-consumer SLA limits.

```xml
<ProxyEndpoint name="default">
    <PreFlow name="PreFlow">
        <Request>
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
    </PreFlow>

    <RouteRule name="default">
        <TargetEndpoint>default</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>
```

SpikeArrest executes first to reject traffic that would overwhelm the backend. Quota executes second to decrement the consumer's counter. VerifyAPIKey must run before both so that `request.header.x-api-key` and `client_id` variables are available for Identifier elements.

---

**See also:** [Caching Policies](policies_caching.md) | [Flows and Execution](flows_and_execution.md) | [Flow Variables and Conditions](flow_variables_and_conditions.md)
