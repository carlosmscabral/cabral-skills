# Caching Policies

Caching policies reduce backend load and improve response latency by storing data for reuse across requests. Apigee X provides two caching approaches: **ResponseCache** for complete HTTP responses and **general-purpose caching** (PopulateCache, LookupCache, InvalidateCache) for arbitrary data. The general-purpose policies enable the **cache-aside pattern**, which gives full control over cache lookup, population, and invalidation as separate steps.

---

## ResponseCache Policy

ResponseCache handles both cache lookup and cache population in a single policy. Attach it to **both** the request flow (where it performs the lookup) and the response flow (where it stores the backend response). When a cache hit occurs on the request flow, Apigee returns the cached response immediately without calling the backend.

### Complete XML Example

```xml
<ResponseCache name="RC-CacheResponse">
    <DisplayName>Cache GET Responses</DisplayName>
    <CacheKey>
        <Prefix>v1</Prefix>
        <KeyFragment ref="request.uri"/>
    </CacheKey>
    <Scope>Exclusive</Scope>
    <ExpirySettings>
        <TimeoutInSec>300</TimeoutInSec>
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

### Key Elements

| Element | Description |
|---|---|
| `<CacheKey>` | Defines the unique key used to store and retrieve cached entries |
| `<Prefix>` | Static string prepended to the cache key |
| `<KeyFragment>` | Static value or variable reference that forms part of the key |
| `<Scope>` | Controls key uniqueness: `Global`, `Application`, `Proxy`, `Target`, `Exclusive` |
| `<ExpirySettings>` | Controls how long entries remain in cache |
| `<TimeoutInSec>` | TTL in seconds |
| `<UseResponseCacheHeaders>` | When `true`, honors `Cache-Control` and `Expires` headers from the backend |
| `<ExcludeErrorResponse>` | When `true`, prevents caching of error responses (4xx/5xx) |
| `<SkipCacheLookup>` | Condition to bypass cache lookup on request |
| `<SkipCachePopulation>` | Condition to bypass cache storage on response |

### Honoring Backend Cache-Control Headers

```xml
<ResponseCache name="RC-HonorBackendHeaders">
    <DisplayName>Honor Backend Cache Headers</DisplayName>
    <CacheKey>
        <Prefix>api</Prefix>
        <KeyFragment ref="request.uri"/>
        <KeyFragment ref="request.header.Accept"/>
    </CacheKey>
    <Scope>Exclusive</Scope>
    <ExpirySettings>
        <TimeoutInSec>600</TimeoutInSec>
        <UseResponseCacheHeaders>true</UseResponseCacheHeaders>
    </ExpirySettings>
    <ExcludeErrorResponse>true</ExcludeErrorResponse>
</ResponseCache>
```

When `UseResponseCacheHeaders` is `true`, the policy respects `Cache-Control: max-age`, `Cache-Control: s-maxage`, and `Expires` headers. The `TimeoutInSec` value acts as an upper bound -- the entry will never be cached longer than this value regardless of backend headers.

### Important Constraints

- Maximum cached object size is **256 KB**. Responses exceeding this limit are not cached.
- The policy must be attached to both the request and response flows to function correctly.
- Always set `<ExcludeErrorResponse>true</ExcludeErrorResponse>` to avoid caching transient backend errors.

---

## Cache-Aside Pattern

The cache-aside pattern separates cache lookup, data fetching, and cache population into distinct steps, giving full control over caching behavior. The flow is: **check cache -> if miss, fetch data -> store in cache -> serve. If hit, serve from cache directly**, bypassing the backend entirely.

This pattern is essential when you need to cache data from ServiceCallout responses, transform data before caching, apply conditional caching logic, or serve cached data without hitting a target endpoint at all.

### Complete Cache-Aside Proxy Configuration

The following shows the full ProxyEndpoint configuration implementing cache-aside with conditional routing. On a cache hit, the proxy returns the cached data directly via a null route (no TargetEndpoint). On a cache miss, the request proceeds to the backend, and the response is cached for future requests.

```xml
<ProxyEndpoint name="default">
  <PreFlow name="PreFlow">
    <Request>
      <Step><Name>LC-LookupData</Name></Step>
    </Request>
    <Response/>
  </PreFlow>
  <Flows>
    <Flow name="cache-miss">
      <Condition>lookupcache.LC-LookupData.cachehit = false</Condition>
      <Request>
        <Step><Name>SC-FetchFromBackend</Name></Step>
        <Step><Name>PC-StoreInCache</Name></Step>
      </Request>
      <Response/>
    </Flow>
    <Flow name="cache-hit">
      <Condition>lookupcache.LC-LookupData.cachehit = true</Condition>
      <Request/>
      <Response>
        <Step><Name>AM-ReturnCachedData</Name></Step>
      </Response>
    </Flow>
  </Flows>
  <!-- null route for cache-hit, real target for miss -->
  <RouteRule name="cache-hit-no-backend">
    <Condition>lookupcache.LC-LookupData.cachehit = true</Condition>
  </RouteRule>
  <RouteRule name="default">
    <TargetEndpoint>default</TargetEndpoint>
  </RouteRule>
</ProxyEndpoint>
```

Key points about the routing:
- The `cache-hit-no-backend` RouteRule has no `<TargetEndpoint>`, creating a **null route** that prevents any backend call.
- RouteRules are evaluated top-to-bottom; the first matching condition wins. Place the cache-hit rule before the default rule.
- The cache-miss flow uses a ServiceCallout (`SC-FetchFromBackend`) followed by PopulateCache in the request flow, but you can also populate cache in the response flow after a normal backend call depending on your design.

### LookupCache Policy (Complete)

```xml
<LookupCache name="LC-LookupData">
  <CacheKey>
    <Prefix>userdata</Prefix>
    <KeyFragment ref="request.queryparam.user_id"/>
  </CacheKey>
  <CacheResource>default</CacheResource>
  <Scope>Exclusive</Scope>
  <AssignTo>cached.data</AssignTo>
  <CacheLookupTimeoutInSeconds>5</CacheLookupTimeoutInSeconds>
</LookupCache>
```

| Element | Description |
|---|---|
| `<CacheResource>` | Named cache resource to use. Use `default` for the built-in environment cache. |
| `<AssignTo>` | Flow variable where the cached value is stored on a hit. Not set on a miss. |
| `<CacheLookupTimeoutInSeconds>` | Maximum time to wait for the cache lookup before treating it as a miss. Prevents slow cache lookups from blocking the request. |

After execution, check `lookupcache.LC-LookupData.cachehit` to determine if a value was found.

### PopulateCache Policy (Complete with ExpirySettings)

```xml
<PopulateCache name="PC-StoreInCache">
  <CacheKey>
    <Prefix>userdata</Prefix>
    <KeyFragment ref="request.queryparam.user_id"/>
  </CacheKey>
  <CacheResource>default</CacheResource>
  <Scope>Exclusive</Scope>
  <Source>response.content</Source>
  <ExpirySettings>
    <TimeoutInSec>3600</TimeoutInSec>
  </ExpirySettings>
</PopulateCache>
```

The `<Source>` element names the flow variable whose value will be cached. If omitted, the entire response message is cached. The CacheKey must match exactly between LookupCache and PopulateCache for the pattern to work.

### AssignMessage Policy for Returning Cached Data

When a cache hit occurs and no backend call is needed, use AssignMessage to construct the response from the cached variable:

```xml
<AssignMessage name="AM-ReturnCachedData">
  <Set>
    <Payload contentType="application/json">{cached.data}</Payload>
    <StatusCode>200</StatusCode>
    <Headers>
      <Header name="Content-Type">application/json</Header>
      <Header name="X-Cache-Hit">true</Header>
    </Headers>
  </Set>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</AssignMessage>
```

The `X-Cache-Hit: true` header is optional but useful for debugging and for downstream consumers to know the response was served from cache.

---

## General-Purpose Caching Policies

For caching arbitrary data -- ServiceCallout responses, computed values, tokens, session data -- use the three general-purpose cache policies together. They provide full control over what is cached, when it is retrieved, and when it is invalidated.

### PopulateCache

Stores a value in the cache under a specified key.

```xml
<PopulateCache name="PC-StoreToken">
    <DisplayName>Store OAuth Token</DisplayName>
    <CacheKey>
        <Prefix>tokens</Prefix>
        <KeyFragment ref="request.header.x-client-id"/>
    </CacheKey>
    <Source>oauth.access_token</Source>
    <Scope>Environment</Scope>
    <ExpirySettings>
        <TimeoutInSec>3600</TimeoutInSec>
    </ExpirySettings>
</PopulateCache>
```

### LookupCache

Retrieves a value from the cache and assigns it to a flow variable.

```xml
<LookupCache name="LC-GetToken">
    <DisplayName>Lookup Cached Token</DisplayName>
    <CacheKey>
        <Prefix>tokens</Prefix>
        <KeyFragment ref="request.header.x-client-id"/>
    </CacheKey>
    <Scope>Environment</Scope>
    <AssignTo>cached.token</AssignTo>
</LookupCache>
```

After execution, check `lookupcache.{policy-name}.cachehit` to determine if a value was found. If the lookup misses, the `<AssignTo>` variable is not set.

### InvalidateCache

Removes a cached entry by key.

```xml
<InvalidateCache name="IC-ClearToken">
    <DisplayName>Clear Cached Token</DisplayName>
    <CacheKey>
        <Prefix>tokens</Prefix>
        <KeyFragment ref="request.header.x-client-id"/>
    </CacheKey>
    <Scope>Environment</Scope>
</InvalidateCache>
```

Use InvalidateCache when the underlying data changes -- for example, after a password reset or token revocation.

### Complete Flow Example: Caching a ServiceCallout Response

```xml
<ProxyEndpoint name="default">
    <PreFlow name="PreFlow">
        <Request>
            <!-- Step 1: Try to retrieve cached config -->
            <Step>
                <Name>LC-GetConfig</Name>
            </Step>
            <!-- Step 2: If cache miss, call backend for config -->
            <Step>
                <Name>SC-FetchConfig</Name>
                <Condition>lookupcache.LC-GetConfig.cachehit = false</Condition>
            </Step>
            <!-- Step 3: If cache miss, store the fetched config -->
            <Step>
                <Name>PC-StoreConfig</Name>
                <Condition>lookupcache.LC-GetConfig.cachehit = false</Condition>
            </Step>
        </Request>
    </PreFlow>

    <RouteRule name="default">
        <TargetEndpoint>default</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>
```

This pattern avoids unnecessary backend calls by serving cached data when available and only fetching and caching on a miss. Unlike the full cache-aside pattern above, this variant still routes to a TargetEndpoint -- use it when the cached data supplements the main request rather than replacing the backend response entirely.

---

## InvalidateCache Deep Dive

InvalidateCache supports selective and bulk invalidation. The `<PurgeChildEntries>` element controls whether child entries under a prefix are also purged, and `<CacheContext>` allows invalidating entries from a different proxy or scope.

### Complete InvalidateCache with All Options

```xml
<InvalidateCache name="IC-PurgeUserData">
    <DisplayName>Purge All User Data</DisplayName>
    <CacheKey>
        <Prefix>userdata</Prefix>
        <KeyFragment ref="request.queryparam.user_id"/>
    </CacheKey>
    <CacheResource>default</CacheResource>
    <Scope>Exclusive</Scope>
    <PurgeChildEntries>true</PurgeChildEntries>
</InvalidateCache>
```

### Invalidating Entries from a Different Cache Context

Use `<CacheContext>` to invalidate cache entries that were created in a different proxy or with a different scope:

```xml
<InvalidateCache name="IC-CrossProxyInvalidate">
    <DisplayName>Invalidate Shared Cache Entry</DisplayName>
    <CacheKey>
        <Prefix>shared-config</Prefix>
        <KeyFragment>global-settings</KeyFragment>
    </CacheKey>
    <CacheContext>
        <APIProxyName>shared-data-proxy</APIProxyName>
        <TargetName>default</TargetName>
    </CacheContext>
    <Scope>Exclusive</Scope>
</InvalidateCache>
```

This is useful in architectures where one proxy manages data mutations while other proxies cache and serve that data. The mutating proxy can invalidate cached entries across the other proxies.

---

## ExpirySettings Deep Dive

ExpirySettings controls how long cached entries remain valid. There are three mutually exclusive options, plus the ability to set dynamic TTLs via variable references.

### TimeoutInSec (Relative TTL)

The most common option. Specifies a TTL in seconds from the moment the entry is cached.

```xml
<ExpirySettings>
    <TimeoutInSec>3600</TimeoutInSec>
</ExpirySettings>
```

### Dynamic TTL with ref Attribute

Use the `ref` attribute to read the TTL from a flow variable at runtime. The element text serves as the default if the variable is not set.

```xml
<ExpirySettings>
    <TimeoutInSec ref="request.header.X-Cache-TTL">3600</TimeoutInSec>
</ExpirySettings>
```

This allows API consumers or upstream logic to control cache duration per request.

### ExpiryDate (Absolute Date)

Specifies an absolute expiration date in `mm-dd-yyyy` format. The entry expires at midnight UTC on the specified date.

```xml
<ExpirySettings>
    <ExpiryDate>12-31-2026</ExpiryDate>
</ExpirySettings>
```

### TimeOfDay (Daily Reset)

Specifies a time of day in `hh:mm:ss` (UTC) at which the cache entry expires. The entry is purged at this time every day.

```xml
<ExpirySettings>
    <TimeOfDay>06:00:00</TimeOfDay>
</ExpirySettings>
```

Useful for data that refreshes on a daily schedule, such as exchange rates or daily reports.

### Precedence Rules

When multiple expiry elements are present (though only one should be used), the precedence is:

1. **TimeoutInSec** -- highest priority, always wins if present
2. **ExpiryDate** -- second priority
3. **TimeOfDay** -- lowest priority

Best practice: use only one expiry element per policy to avoid confusion.

---

## Cache Scope Deep Dive

The `<Scope>` element controls the namespace of cache keys, determining which proxies and revisions share cached entries. The scope is prepended to the cache key to form the full key used internally.

| Scope | Key Format | Use Case |
|---|---|---|
| **Global** | `orgName__envName__[keyFragment]` | Shared across all proxies in the environment. Use for environment-wide configuration or shared reference data. |
| **Application** | `orgName__envName__appName__[keyFragment]` | Scoped to a specific application. Rarely used. |
| **Proxy** | `orgName__envName__proxyName__[keyFragment]` | Shared across all revisions of a proxy. Most common scope for production use. |
| **Target** | `orgName__envName__proxyName__targetName__[keyFragment]` | Scoped to a specific TargetEndpoint within a proxy. |
| **Exclusive** | `orgName__envName__proxyName__revisionNumber__proxyName\|targetName__[keyFragment]` | Fully isolated per proxy revision and endpoint. Safest option -- deploying a new revision gets a fresh cache. |

**Choosing the right scope:**

- Use **Proxy** when cached data should survive proxy re-deployments (same revision or new revision).
- Use **Exclusive** (the default) when a new deployment should start with a clean cache, such as when the response format may have changed between revisions.
- Use **Global** sparingly and only for truly shared data, as any proxy can overwrite entries.

---

## Flow Variables Set by Caching Policies

### LookupCache Variables

| Variable | Description |
|---|---|
| `lookupcache.{policy-name}.cachehit` | `true` if the lookup found an entry, `false` otherwise. **This is the critical variable for implementing the cache-aside pattern.** |
| `lookupcache.{policy-name}.cachekey` | The fully qualified cache key that was used for the lookup. |
| `lookupcache.{policy-name}.assignto` | The name of the variable specified in `<AssignTo>`. |

### ResponseCache Variables

| Variable | Description |
|---|---|
| `responsecache.{policy-name}.cachehit` | `true` if the response was served from cache. |
| `responsecache.{policy-name}.cachekey` | The computed cache key string. |
| `responsecache.{policy-name}.invalidentry` | `true` if the cached entry is invalid. |

### Using Cache Variables in Conditions

```xml
<!-- Skip processing if data was served from cache -->
<Step>
    <Name>JS-TransformResponse</Name>
    <Condition>lookupcache.LC-LookupData.cachehit = false</Condition>
</Step>

<!-- Add cache diagnostic headers -->
<Step>
    <Name>AM-AddCacheHeaders</Name>
    <Condition>responsecache.RC-CacheResponse.cachehit = true</Condition>
</Step>
```

---

## ResponseCache vs Cache-Aside Comparison

| Criteria | ResponseCache | Cache-Aside (Populate/Lookup/Invalidate) |
|---|---|---|
| **What is cached** | Complete HTTP response (headers + body) | Any flow variable value |
| **Number of policies** | One (handles both lookup and populate) | Three separate policies, plus AssignMessage for response construction |
| **Ease of use** | Simpler setup for standard response caching | More configuration, but more flexible |
| **Cache invalidation** | Time-based only (TTL or response headers) | Explicit invalidation via InvalidateCache, plus time-based |
| **Backend bypass** | Automatic -- cache hit skips backend | Manual -- requires null RouteRule or conditional ServiceCallout |
| **Data transformation** | Caches raw backend response as-is | Can transform data before caching |
| **Partial data caching** | No -- caches entire response | Yes -- cache any variable or subset of response |
| **Cross-proxy sharing** | Limited to scope settings | Full control via CacheContext and scope |
| **Best for** | Simple GET response caching | Tokens, config, computed values, ServiceCallout data, complex caching logic |

**When to use ResponseCache:**
- Caching standard GET responses where the backend response is served as-is.
- The API is read-heavy with predictable cache keys based on URI and headers.
- You want minimal configuration and automatic cache hit/miss handling.

**When to use Cache-Aside:**
- You need to cache data from ServiceCallout responses, not the main backend.
- You want to transform or enrich data before caching.
- You need explicit invalidation triggered by mutation operations (POST/PUT/DELETE).
- You want to short-circuit the proxy entirely on cache hits (null route pattern).
- You need to cache partial data or combine cached data with live data.

---

## Cache Limits

| Limit | Value |
|---|---|
| Maximum cache key size | 2 KB |
| Maximum cached value size | 256 KB |
| Maximum items per cache | 10 million |
| Maximum caches per environment | 100 |
| Minimum expiration | 1 second |
| Maximum expiration | 30 days (2,592,000 seconds) |

Entries exceeding the 256 KB value limit are silently not cached -- no error is raised. Monitor cache hit rates to detect this. For large payloads, consider caching a compressed version or only the fields you need.

---

## Cache Key Design Best Practices

Effective cache key design ensures that distinct responses are cached separately while identical requests share a cached entry.

```xml
<CacheKey>
    <Prefix>v2</Prefix>
    <KeyFragment ref="request.uri"/>
    <KeyFragment ref="request.header.Accept"/>
    <KeyFragment ref="request.queryparam.lang"/>
</CacheKey>
```

### Multiple KeyFragment Types

KeyFragment supports both variable references and static values. Combine them as needed:

```xml
<CacheKey>
    <Prefix>catalog</Prefix>
    <!-- Static fragment for logical grouping -->
    <KeyFragment>product-list</KeyFragment>
    <!-- Dynamic fragments from request context -->
    <KeyFragment ref="request.queryparam.category"/>
    <KeyFragment ref="request.queryparam.page"/>
    <KeyFragment ref="request.queryparam.page_size"/>
</CacheKey>
```

### Guidelines

- **Include all attributes that produce different responses.** If the backend returns different data for different query parameters, those parameters must be in the cache key.
- **Include an API version prefix.** When deploying a new API version, changing the prefix (e.g., `v1` to `v2`) invalidates all stale entries without manual cache clearing.
- **Include the Accept header** when the backend supports content negotiation (JSON vs XML). Without it, a client requesting XML could receive a cached JSON response.
- **Keep keys deterministic.** The same logical request must always produce the same cache key. Avoid including timestamps, random values, or non-deterministic variables.
- **Avoid overly broad keys.** Using only `request.uri` may cache too aggressively if query parameters affect the response. Using too many fragments may reduce cache hit rates.
- **Keep keys under the 2 KB limit.** Long URIs or large header values can push the key over the limit. If needed, use a JavaScript callout to hash the key components into a shorter value and reference that hash as the KeyFragment.
- **Match CacheKey exactly** across LookupCache and PopulateCache policies. A mismatch in Prefix, Scope, or KeyFragment elements means lookups will never find populated entries.

---

**See also:** [Traffic Management Policies](policies_traffic_management.md) | [Flows and Execution](flows_and_execution.md) | [Flow Variables and Conditions](flow_variables_and_conditions.md)
