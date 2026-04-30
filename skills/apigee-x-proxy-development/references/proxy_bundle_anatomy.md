# API Proxy Bundle Anatomy

This reference documents the complete structure of Apigee X API proxy bundles and SharedFlow bundles, including directory layout, naming conventions, and resource resolution.

## Directory Tree

```
apiproxy/
  APIProxy.xml                    # Root descriptor: name, revision, basepaths
  policies/                       # All policy XML files
    AM-SetHeaders.xml
    EV-ExtractToken.xml
    RF-InvalidKey.xml
  proxies/                        # ProxyEndpoint definitions
    default.xml
  targets/                        # TargetEndpoint definitions
    default.xml
  resources/                      # Embedded code and config files
    jsc/                          #   JavaScript files (.js)
    java/                         #   Compiled JAR files (.jar)
    xsl/                          #   XSLT stylesheets (.xsl)
    properties/                   #   Java properties files (.properties)
    wsdl/                         #   WSDL files (.wsdl)
    openapi/                      #   OpenAPI spec files (.json, .yaml)
```

Every proxy bundle must contain `APIProxy.xml` at the root and at least one ProxyEndpoint in `proxies/`. The `targets/`, `policies/`, and `resources/` directories are optional.

## Root APIProxy XML

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<APIProxy revision="1" name="my-api-v1">
    <DisplayName>My API v1</DisplayName>
    <Description>Customer-facing API</Description>
    <CreatedAt>1609459200000</CreatedAt>
    <LastModifiedAt>1609459200000</LastModifiedAt>
    <BasePaths>/v1/my-api</BasePaths>
    <Policies>
        <Policy>AM-SetHeaders</Policy>
        <Policy>EV-ExtractToken</Policy>
    </Policies>
    <ProxyEndpoints>
        <ProxyEndpoint>default</ProxyEndpoint>
    </ProxyEndpoints>
    <TargetEndpoints>
        <TargetEndpoint>default</TargetEndpoint>
    </TargetEndpoints>
    <Resources>
        <Resource>jsc://utils.js</Resource>
    </Resources>
</APIProxy>
```

The `name` attribute must match the bundle directory name. The `<BasePaths>` element declares the URL prefix this proxy handles.

## File Naming Conventions

Policy files follow the pattern `[Abbreviation]-[Purpose].xml`, consistent with the GoogleCloudPlatform/apigee-samples repository. The abbreviation prefix identifies the policy type at a glance.

### Abbreviation Table

| Abbreviation | Policy Type              | Example Filename              |
|-------------|--------------------------|-------------------------------|
| AM          | AssignMessage            | AM-SetCORSHeaders.xml         |
| EV          | ExtractVariables         | EV-ExtractAuthToken.xml       |
| SC          | ServiceCallout           | SC-CallAuthService.xml        |
| RF          | RaiseFault               | RF-InvalidAPIKey.xml          |
| FC          | FlowCallout              | FC-ApplySecurity.xml          |
| SA          | SpikeArrest              | SA-RateLimit.xml              |
| Q           | Quota                    | Q-DeveloperQuota.xml          |
| RC          | ResponseCache            | RC-CacheGETResponses.xml      |
| LC          | LookupCache              | LC-ReadSessionData.xml        |
| PC          | PopulateCache            | PC-StoreSessionData.xml       |
| IC          | InvalidateCache          | IC-ClearSessionData.xml       |
| KVM         | KeyValueMapOperations    | KVM-GetConfig.xml             |
| JS          | JavaScript               | JS-TransformPayload.xml       |
| JWT         | JWT policies             | JWT-VerifyAccessToken.xml     |
| OAuth       | OAuthV2                  | OAuth-GenerateToken.xml       |
| VAK         | VerifyAPIKey             | VAK-VerifyKey.xml             |
| ML          | MessageLogging           | ML-LogToCloudLogging.xml      |
| DC          | DataCapture              | DC-CaptureRevenue.xml         |
| CORS        | CORS                     | CORS-AllowOrigins.xml         |
| JTP         | JSONThreatProtection     | JTP-ValidateInput.xml         |
| XTP         | XMLThreatProtection      | XTP-ValidateSOAP.xml          |
| OAS         | OASValidation            | OAS-ValidateRequest.xml       |

These naming conventions are recommended practice, not enforced by Apigee. Any valid filename works, but consistent naming improves team collaboration and proxy readability.

## Resources Directory

The `resources/` directory holds code and configuration files referenced by policies.

| Subdirectory   | Contents                         | Referenced By           |
|---------------|----------------------------------|------------------------|
| `jsc/`        | JavaScript files (.js)           | JavaScript policy      |
| `java/`       | Compiled JAR files (.jar)        | JavaCallout policy     |
| `xsl/`        | XSLT stylesheets (.xsl)         | XSLTransform policy    |
| `properties/` | Java properties files            | JavaCallout policy     |
| `wsdl/`       | WSDL definitions                 | SOAPMessageValidation  |
| `openapi/`    | OpenAPI specs (.json, .yaml)     | OASValidation policy   |

### Resource Resolution Order

When a policy references a resource file, Apigee X resolves it in this order:

1. **Proxy-scoped** -- `apiproxy/resources/` within the current bundle
2. **Environment-scoped** -- resources uploaded to the environment via the API
3. **Organization-scoped** -- resources uploaded to the organization via the API

The first match wins. Proxy-scoped resources always take precedence, allowing bundles to be self-contained while still sharing common resources at higher scopes.

## SharedFlow Bundle Structure

SharedFlow bundles mirror the proxy bundle layout but use `sharedflowbundle/` as the root and `sharedflows/` instead of `proxies/`:

```
sharedflowbundle/
  SharedFlowBundle.xml            # Root descriptor (replaces APIProxy.xml)
  policies/                       # Policy XML files (same as proxy)
  sharedflows/                    # SharedFlow definition (replaces proxies/)
    default.xml
  resources/                      # Embedded resources (same as proxy)
    jsc/
```

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<SharedFlowBundle revision="1" name="sf-security-v1">
    <DisplayName>Security SharedFlow v1</DisplayName>
    <Policies>
        <Policy>VAK-VerifyKey</Policy>
        <Policy>SA-RateLimit</Policy>
    </Policies>
    <SharedFlows>
        <SharedFlow>default</SharedFlow>
    </SharedFlows>
</SharedFlowBundle>
```

SharedFlows have no `targets/` directory and no `<BasePaths>` element. They are invoked from proxy bundles using the FlowCallout policy (FC prefix).

## Base Path Rules

- Each base path must be **unique within an environment group**. Two deployed proxies cannot share the same base path in overlapping environment groups.
- Apigee X supports a maximum of **3000 proxy deployments per environment**.
- Base paths support a single trailing wildcard: `/v1/orders/**` matches all sub-paths.
- The base path `/` is valid and acts as a catch-all for the environment group's hostnames.

---

## Related References

- [Endpoints and Routing](./endpoints_and_routing.md) -- ProxyEndpoint, TargetEndpoint, RouteRules, and proxy chaining
