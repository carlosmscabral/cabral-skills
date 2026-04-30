# Security Policies

Security policies protect APIs from unauthorized access, malicious payloads, and abuse. These policies handle authentication, authorization, threat detection, and input validation.

## VerifyAPIKey

Validates API keys passed in the request and associates the request with an API product, developer app, and developer. After successful verification, Apigee auto-populates flow variables with metadata from the associated API product and developer app.

Key location: header or query parameter.

Auto-populated variables after verification: `apiproduct.name`, `apiproduct.developer.quota.limit`, `developer.email`, `developer.app.name`, `verifyapikey.{policy-name}.client_id`, `verifyapikey.{policy-name}.client_secret`.

```xml
<VerifyAPIKey name="VAK-VerifyKey">
  <APIKey ref="request.header.x-api-key"/>
</VerifyAPIKey>
```

Alternative -- extract from query parameter:

```xml
<VerifyAPIKey name="VAK-VerifyKeyFromParam">
  <APIKey ref="request.queryparam.apikey"/>
</VerifyAPIKey>
```

Place this policy early in the PreFlow Request to reject unauthenticated requests before any processing occurs.

## OAuthV2

Supports standard OAuth 2.0 grant types: `client_credentials`, `authorization_code`, `password`, `implicit`. Each grant type requires a different configuration of the OAuthV2 policy.

### GenerateAccessToken (client_credentials)

```xml
<OAuthV2 name="OAuth-GenerateToken">
  <Operation>GenerateAccessToken</Operation>
  <ExpiresIn>3600000</ExpiresIn>
  <SupportedGrantTypes>
    <GrantType>client_credentials</GrantType>
  </SupportedGrantTypes>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
</OAuthV2>
```

### VerifyAccessToken

```xml
<OAuthV2 name="OAuth-VerifyToken">
  <Operation>VerifyAccessToken</Operation>
</OAuthV2>
```

### Token Endpoint Proxy Pattern

Create a dedicated conditional flow in your proxy to handle token generation requests. The condition isolates token operations from normal API traffic:

```xml
<Flow name="GenerateToken">
  <Condition>(proxy.pathsuffix MatchesPath "/token") and (request.verb = "POST")</Condition>
  <Request>
    <Step>
      <Name>OAuth-GenerateToken</Name>
    </Step>
  </Request>
</Flow>
```

### Auto-populated Variables

After `VerifyAccessToken` succeeds, the following variables become available: `oauthv2accesstoken.{policy-name}.access_token`, `oauthv2accesstoken.{policy-name}.scope`, `apiproduct.name`, `developer.email`, `developer.app.name`.

### Authorization Code Grant Flow

The authorization code grant is a multi-step process:

1. Client redirects user to the `/authorize` endpoint on the proxy.
2. Proxy authenticates the user (often via identity provider) and presents a consent screen.
3. Upon consent, proxy generates an authorization code using `<Operation>GenerateAuthorizationCode</Operation>` and redirects back to the client callback URL.
4. Client exchanges the authorization code for an access token by calling the `/token` endpoint with the code and `grant_type=authorization_code`.

### Scope Validation

Scopes are defined on API products. When verifying tokens, you can enforce required scopes:

```xml
<OAuthV2 name="OAuth-VerifyWithScope">
  <Operation>VerifyAccessToken</Operation>
  <Scope>read write</Scope>
</OAuthV2>
```

The token must contain all specified scopes for the request to proceed.

## BasicAuthentication Policy

Encode or decode Base64 credentials for HTTP Basic Authentication. This policy does NOT enforce authentication — it only transforms credentials. Use it to extract client credentials from incoming `Authorization: Basic` headers or to create Basic auth headers for backend requests.

### Decode (extract username and password from incoming request)
```xml
<BasicAuthentication name="BA-DecodeCredentials">
  <Operation>Decode</Operation>
  <Source>request.header.Authorization</Source>
  <User ref="decoded.username"/>
  <Password ref="decoded.password"/>
</BasicAuthentication>
```
Parses `Basic dXNlcjpwYXNz`, Base64-decodes, splits on `:`, stores username and password in separate variables.

### Encode (create Authorization header for backend)
```xml
<BasicAuthentication name="BA-EncodeForBackend">
  <Operation>Encode</Operation>
  <User ref="private.kvm.backendUser"/>
  <Password ref="private.kvm.backendPass"/>
  <AssignTo createNew="false">request.header.Authorization</AssignTo>
</BasicAuthentication>
```
Concatenates `user:pass`, Base64-encodes, outputs `Basic dXNlcjpwYXNz` to the target variable.

### Common Pattern: KVM Credentials → Basic Auth Header
```xml
<!-- Step 1: Get credentials from encrypted KVM -->
<Step><Name>KVM-GetBackendCreds</Name></Step>
<!-- Step 2: Encode into Authorization header for backend -->
<Step><Name>BA-EncodeForBackend</Name></Step>
```

## JWT Policies

### GenerateJWT (Signed)

```xml
<GenerateJWT name="JWT-GenerateSigned">
  <Algorithm>RS256</Algorithm>
  <PrivateKey>
    <Value ref="private.rsa_privatekey"/>
  </PrivateKey>
  <Subject ref="desired_subject"/>
  <Issuer>urn://apigee</Issuer>
  <Audience ref="desired_audience"/>
  <ExpiresIn>3600s</ExpiresIn>
  <AdditionalClaims>
    <Claim name="role" ref="custom.role"/>
  </AdditionalClaims>
  <OutputVariable>output_jwt</OutputVariable>
</GenerateJWT>
```

Supported algorithm options: `RS256`, `RS384`, `RS512`, `PS256`, `PS384`, `PS512`, `ES256`, `ES384`, `ES512`, `HS256`, `HS384`, `HS512`.

- RSA algorithms (`RS*`, `PS*`) use `<PrivateKey>` for signing and `<PublicKey>` for verification.
- Elliptic curve algorithms (`ES*`) use `<PrivateKey>` and `<PublicKey>` similarly.
- HMAC algorithms (`HS*`) use `<SecretKey>` for both signing and verification.

### VerifyJWT

```xml
<VerifyJWT name="JWT-VerifyToken">
  <Algorithm>RS256</Algorithm>
  <Source>request.header.Authorization</Source>
  <PublicKey>
    <JWKS uri="https://example.com/.well-known/jwks.json"/>
  </PublicKey>
  <Issuer>urn://apigee</Issuer>
  <Audience>my-api</Audience>
  <AdditionalClaims>
    <Claim name="role" type="string"/>
  </AdditionalClaims>
</VerifyJWT>
```

Auto-populated variables after verification: `jwt.{policy-name}.decoded.claim.{name}`, `jwt.{policy-name}.decoded.header.{name}`, `jwt.{policy-name}.valid`, `jwt.{policy-name}.expiry`.

### DecodeJWT

```xml
<DecodeJWT name="JWT-Decode">
  <Source>request.header.Authorization</Source>
</DecodeJWT>
```

Decodes the JWT WITHOUT verifying the signature. Use this for pre-routing decisions (such as reading the `iss` claim to select an upstream) and then verify the full token later in the flow with VerifyJWT.

## HMAC Policy

Computes or verifies an HMAC (Hash-based Message Authentication Code) for message integrity validation.

```xml
<HMAC name="HMAC-Verify">
  <Algorithm>SHA-256</Algorithm>
  <SecretKey>
    <Value ref="private.hmac_secret"/>
  </SecretKey>
  <Message ref="request.content"/>
  <Output encoding="base64">hmac_output</Output>
  <VerificationValue ref="request.header.x-signature"/>
</HMAC>
```

When `<VerificationValue>` is provided, the policy computes the HMAC and compares it to the supplied value. A mismatch raises a fault. Omit `<VerificationValue>` to compute only and store the result in the output variable.

## CORS Policy

Handles Cross-Origin Resource Sharing headers for browser-based API consumers.

```xml
<CORS name="CORS-AllowOrigins">
  <AllowOrigins>{request.header.origin}</AllowOrigins>
  <AllowMethods>GET, PUT, POST, DELETE</AllowMethods>
  <AllowHeaders>origin, x-requested-with, accept, content-type, authorization</AllowHeaders>
  <ExposeHeaders>*</ExposeHeaders>
  <MaxAge>3600</MaxAge>
  <AllowCredentials>false</AllowCredentials>
  <GeneratePreflightResponse>true</GeneratePreflightResponse>
  <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
</CORS>
```

| Element | Description | Default |
|---|---|---|
| `<AllowOrigins>` | Origins allowed. Comma-separated URLs, `*` for all, or flow variable like `{request.header.origin}`. Max ~50 values recommended. | Required |
| `<AllowMethods>` | HTTP methods allowed. Comma-separated or `*` for all. | `GET, POST, HEAD, OPTIONS` |
| `<AllowHeaders>` | Headers the client may send. Comma-separated. | None |
| `<ExposeHeaders>` | Headers the browser may access in the response. `*` for all. | Not set |
| `<MaxAge>` | Preflight cache duration in seconds. `-1` disables caching (forces preflight on every call). | `1800` |
| `<AllowCredentials>` | Whether the browser should send credentials (cookies, auth). | `false` |
| `<GeneratePreflightResponse>` | Auto-handle OPTIONS preflight. If `false`, sets flow variables instead. | `true` |

**OPTIONS preflight behavior:** When an OPTIONS request is received, the CORS policy **skips all proxy request flows** and transfers directly to the Proxy Response PreFlow. No need to create a separate condition to handle OPTIONS — the policy does it automatically.

**AllowOrigins options:**
```xml
<!-- Single URL -->
<AllowOrigins>https://www.example.com</AllowOrigins>
<!-- Multiple URLs (comma-separated) -->
<AllowOrigins>https://app.example.com, https://admin.example.com</AllowOrigins>
<!-- Dynamic from request header (recommended) -->
<AllowOrigins>{request.header.origin}</AllowOrigins>
<!-- Wildcard (CAUTION: disables same-origin protection) -->
<AllowOrigins>*</AllowOrigins>
```

**Security warning:** Setting `AllowOrigins` to `*` disables same-origin protection for your API. Use specific origins or `{request.header.origin}` in production.

Place the CORS policy in PreFlow Request so it runs before authentication policies that would reject an unauthenticated OPTIONS preflight.

## AccessControl Policy

Controls access based on client IP address. Useful for restricting traffic to known internal networks or blocking specific sources.

```xml
<AccessControl name="AC-AllowInternal">
  <IPRules noRuleMatchAction="DENY">
    <MatchRule action="ALLOW">
      <SourceAddress mask="24">10.0.0.0</SourceAddress>
    </MatchRule>
    <MatchRule action="ALLOW">
      <SourceAddress mask="16">172.16.0.0</SourceAddress>
    </MatchRule>
  </IPRules>
</AccessControl>
```

Rules are evaluated in order. When `noRuleMatchAction` is `DENY`, any IP not matching an ALLOW rule is rejected.

## VerifyIAM Policy

Authorizes requests using Google Cloud IAM credentials. This policy verifies that the caller has the required IAM permission on a specified resource, integrating Apigee authorization with Google Cloud's IAM system.

```xml
<VerifyIAM name="VIAM-CheckPermission">
  <CredentialSource>request.header.Authorization</CredentialSource>
  <Resource>projects/{organization.name}/resources/{proxy.name}</Resource>
  <Permission>apigee.apiproxies.invoke</Permission>
</VerifyIAM>
```

## JSONThreatProtection

Validates JSON payloads against structural constraints to prevent attacks using deeply nested or oversized JSON.

```xml
<JSONThreatProtection name="JTP-ValidatePayload">
  <ArrayElementCount>20</ArrayElementCount>
  <ContainerDepth>10</ContainerDepth>
  <ObjectEntryCount>15</ObjectEntryCount>
  <ObjectEntryNameLength>50</ObjectEntryNameLength>
  <StringValueLength>500</StringValueLength>
  <Source>request</Source>
</JSONThreatProtection>
```

Each element acts as a threshold. If any limit is exceeded, the policy raises a fault. Omitting an element means no limit is enforced for that dimension.

## XMLThreatProtection

Validates XML payloads against structural constraints to prevent XML-based attacks such as entity expansion or deeply nested elements.

```xml
<XMLThreatProtection name="XTP-ValidateXML">
  <NameLimits>
    <Element>32</Element>
    <Attribute>32</Attribute>
  </NameLimits>
  <StructureLimits>
    <NodeDepth>10</NodeDepth>
    <AttributeCountPerElement>5</AttributeCountPerElement>
    <ChildCount>25</ChildCount>
  </StructureLimits>
  <ValueLimits>
    <Text>500</Text>
    <Attribute>128</Attribute>
  </ValueLimits>
  <Source>request</Source>
</XMLThreatProtection>
```

## OASValidation

Validates requests and responses against an OpenAPI 3.0 specification bundled with the proxy.

### Basic Usage
```xml
<OASValidation name="OAS-ValidateRequest">
  <OASResource>oas://my-spec.yaml</OASResource>
  <Options>
    <ValidateMessageBody>true</ValidateMessageBody>
  </Options>
  <Source>request</Source>
</OASValidation>
```

### Strict Validation (reject unspecified parameters)
```xml
<OASValidation name="OAS-StrictValidation">
  <OASResource>oas://my-spec.yaml</OASResource>
  <Options>
    <ValidateMessageBody>true</ValidateMessageBody>
    <AllowUnspecifiedParameters>
      <Header>false</Header>
      <Query>false</Query>
      <Cookie>false</Cookie>
    </AllowUnspecifiedParameters>
  </Options>
  <Source>request</Source>
</OASValidation>
```

| Element | Description | Default |
|---|---|---|
| `<OASResource>` | Path to the OpenAPI spec: `oas://filename.yaml` or `oas://filename.json`. File stored in `apiproxy/resources/oas/`. | Required |
| `<ValidateMessageBody>` | Validate body against the spec's request body schema. Only works when `Content-Type` is `application/json`; other content types skip body validation automatically. | `false` |
| `<AllowUnspecifiedParameters>` | Control behavior for params not defined in the spec. Child elements: `<Header>`, `<Query>`, `<Cookie>` (each `true`/`false`). | All `true` (allow extra params) |
| `<Source>` | Which message to validate: `request`, `response`, or `message` (auto-detects based on flow phase). | `request` |

**Important:** Body validation only applies to `application/json` content. Non-JSON bodies pass validation automatically without being checked.

## GraphQL Policy

Parses and validates GraphQL queries against a schema, enforcing depth and complexity limits.

```xml
<GraphQL name="GQL-Validate">
  <OperationType>query</OperationType>
  <MaxDepth>5</MaxDepth>
  <MaxCount>10</MaxCount>
  <Action>parse</Action>
  <ResourceURL>graphql://schema.graphql</ResourceURL>
</GraphQL>
```

`MaxDepth` prevents deeply nested queries that could overload backend resolvers. `MaxCount` limits the number of fields or fragments in a single query. The schema file is stored in `apiproxy/resources/graphql/`.

## API Products, Apps, and Developers

The security policies above validate credentials against the Apigee entity model:

- **API Products** define which API proxies, resource paths, environments, and scopes are accessible. They represent a bundle of API capabilities offered as a unit.
- **Developer Apps** are registered by developers and associated with one or more API Products. Each app receives a consumer key (API key) and secret.
- **Developers** represent the people or organizations consuming APIs. They own one or more developer apps.

When `VerifyAPIKey` or `OAuthV2 VerifyAccessToken` succeeds, Apigee resolves the credential back to the app, developer, and product. Flow variables like `apiproduct.name`, `developer.email`, and `developer.app.name` become available for use in conditions, quotas, analytics, and downstream policies.

---

[Mediation Policies](policies_mediation.md) | [Proxy Bundle Anatomy](proxy_bundle_anatomy.md) | [Flows and Execution](flows_and_execution.md) | [Flow Variables and Conditions](flow_variables_and_conditions.md) | [Endpoints and Routing](endpoints_and_routing.md)
