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

The most complex Apigee policy. Supports OAuth 2.0 grant types (`client_credentials`, `authorization_code`, `password`, `implicit`) through 7 operations. Always set `<RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>` for standards-compliant token responses.

### GenerateAccessToken (client_credentials)

```xml
<OAuthV2 name="OAuth-GenerateToken">
  <Operation>GenerateAccessToken</Operation>
  <ExpiresIn>3600000</ExpiresIn>
  <RefreshTokenExpiresIn>86400000</RefreshTokenExpiresIn>
  <SupportedGrantTypes>
    <GrantType>client_credentials</GrantType>
  </SupportedGrantTypes>
  <GrantType>request.formparam.grant_type</GrantType>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
  <Attributes>
    <Attribute name="tenant_id" ref="custom.tenant" display="false"/>
  </Attributes>
</OAuthV2>
```

Key elements:
- `<ExpiresIn>`: access token lifetime in milliseconds
- `<RefreshTokenExpiresIn>`: refresh token lifetime (separate from access token)
- `<GrantType>`: where to find the grant_type parameter (default: `request.formparam.grant_type`)
- `<ClientId>` / `<ClientSecret>`: where to find credentials (default: `request.formparam.client_id` / `request.formparam.client_secret`, or from `Authorization: Basic` header)
- `<GenerateResponse enabled="true"/>`: auto-generate JSON response. When `false`, no response body is sent — token values are available only via flow variables (use for custom response formatting)
- `<RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>`: enforce RFC 6749 compliance. Default `false` may omit `token_type` and other required fields.
- `<Attributes>`: attach up to 18 custom key-value pairs to the token. `display="false"` hides from response but value is still stored.

### VerifyAccessToken

```xml
<OAuthV2 name="OAuth-VerifyToken">
  <Operation>VerifyAccessToken</Operation>
</OAuthV2>
```

By default, expects `Authorization: Bearer {token}` header. To customize:
```xml
<OAuthV2 name="OAuth-VerifyCustomLocation">
  <Operation>VerifyAccessToken</Operation>
  <AccessToken>request.header.X-Custom-Token</AccessToken>
  <AccessTokenPrefix>Token</AccessTokenPrefix>
</OAuthV2>
```

### GenerateAuthorizationCode

Step 1 of the authorization code grant — generates a short-lived code the client exchanges for a token:
```xml
<OAuthV2 name="OAuth-GenerateAuthCode">
  <Operation>GenerateAuthorizationCode</Operation>
  <ExpiresIn>600000</ExpiresIn>
  <GenerateResponse enabled="true"/>
</OAuthV2>
```

Step 2 — exchange code for token (in the `/token` endpoint flow):
```xml
<OAuthV2 name="OAuth-ExchangeCode">
  <Operation>GenerateAccessToken</Operation>
  <SupportedGrantTypes>
    <GrantType>authorization_code</GrantType>
  </SupportedGrantTypes>
  <Code>request.formparam.code</Code>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
</OAuthV2>
```

Custom attributes on the authorization code are **automatically inherited** by the generated access token.

### RefreshAccessToken

```xml
<OAuthV2 name="OAuth-RefreshToken">
  <Operation>RefreshAccessToken</Operation>
  <ExpiresIn>3600000</ExpiresIn>
  <RefreshTokenExpiresIn>86400000</RefreshTokenExpiresIn>
  <RefreshToken>request.formparam.refresh_token</RefreshToken>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
</OAuthV2>
```

**Gotcha:** Custom attributes with `display="false"` on the original token are NOT preserved on refresh — they become visible in the refresh response. Use `GetOAuthV2Info` to retrieve and re-apply them.

### InvalidateToken (Revoke)

```xml
<OAuthV2 name="OAuth-RevokeToken">
  <Operation>InvalidateToken</Operation>
  <Tokens>
    <Token type="accesstoken" cascade="true">request.formparam.token</Token>
  </Tokens>
</OAuthV2>
```

- `type`: `accesstoken` or `refreshtoken`
- `cascade="true"`: revokes both access AND refresh tokens together
- `cascade="false"`: revokes only the specified token type

### Password Grant

Only for highly trusted first-party apps where the client collects user credentials directly:
```xml
<OAuthV2 name="OAuth-PasswordGrant">
  <Operation>GenerateAccessToken</Operation>
  <SupportedGrantTypes>
    <GrantType>password</GrantType>
  </SupportedGrantTypes>
  <UserName>request.formparam.username</UserName>
  <PassWord>request.formparam.password</PassWord>
  <GenerateResponse enabled="true"/>
  <RFCCompliantRequestResponse>true</RFCCompliantRequestResponse>
</OAuthV2>
```

Apigee does NOT validate the username/password — you must validate credentials yourself (via ServiceCallout to an identity provider) BEFORE this policy executes. The policy only generates the token.

### Implicit Grant

For browser-based SPAs that cannot securely store a client secret:
```xml
<OAuthV2 name="OAuth-ImplicitGrant">
  <Operation>GenerateAccessTokenImplicitGrant</Operation>
  <ExpiresIn>600000</ExpiresIn>
  <GenerateResponse enabled="true"/>
</OAuthV2>
```

Implicit grants **cannot issue refresh tokens**. Use very short expiration times.

### Token Endpoint Proxy Pattern

Create conditional flows to isolate OAuth operations from resource API traffic:
```xml
<Flow name="token">
  <Condition>(proxy.pathsuffix MatchesPath "/token") and (request.verb = "POST")</Condition>
  <Request>
    <Step><Name>OAuth-GenerateToken</Name></Step>
  </Request>
</Flow>
<Flow name="refresh">
  <Condition>(proxy.pathsuffix MatchesPath "/token") and (request.verb = "POST") and (request.formparam.grant_type = "refresh_token")</Condition>
  <Request>
    <Step><Name>OAuth-RefreshToken</Name></Step>
  </Request>
</Flow>
<Flow name="revoke">
  <Condition>(proxy.pathsuffix MatchesPath "/revoke") and (request.verb = "POST")</Condition>
  <Request>
    <Step><Name>OAuth-RevokeToken</Name></Step>
  </Request>
</Flow>
```

Use null RouteRules for token/revoke flows (no backend call needed).

### Custom Token Attributes

Attach metadata to tokens for downstream authorization decisions:
```xml
<Attributes>
  <Attribute name="tenant_id" ref="custom.tenant" display="false"/>
  <Attribute name="user_role" ref="custom.role" display="true"/>
  <Attribute name="region" ref="request.header.X-Region" display="true"/>
</Attributes>
```

- Up to 18 custom attributes per token
- `ref`: flow variable to read the value from
- `display="true"` (default): attribute appears in the token response JSON
- `display="false"`: hidden from response but stored (accessible after VerifyAccessToken)
- After verification, access as: `oauthv2accesstoken.{policy-name}.{attribute-name}`
- Auth code attributes are inherited by the generated access token

### Third-Party OAuth Integration

Accept tokens from external OAuth providers (Okta, Auth0, custom):
```xml
<OAuthV2 name="OAuth-ExternalToken">
  <Operation>GenerateAccessToken</Operation>
  <ExternalAuthorization>true</ExternalAuthorization>
  <ExternalAccessToken>request.header.external_access_token</ExternalAccessToken>
  <StoreToken>true</StoreToken>
  <ExpiresIn>3600000</ExpiresIn>
  <GenerateResponse enabled="true"/>
</OAuthV2>
```

- `<ExternalAuthorization>true</ExternalAuthorization>`: bypass Apigee's internal credential validation
- `<ExternalAccessToken>`: location of the externally-generated token (max 2 KB)
- `<StoreToken>true</StoreToken>`: persist the external token in Apigee's token store
- Validate the external token yourself (e.g., via ServiceCallout) BEFORE this policy

### GetOAuthV2Info and SetOAuthV2Info

Retrieve or update token metadata at runtime:
```xml
<!-- Get token info (read custom attributes) -->
<GetOAuthV2Info name="GetTokenInfo">
  <AccessToken ref="request.header.Authorization"/>
</GetOAuthV2Info>

<!-- Set/update custom attributes on existing token -->
<SetOAuthV2Info name="UpdateTokenAttrs">
  <AccessToken ref="request.header.Authorization"/>
  <Attributes>
    <Attribute name="last_accessed" display="false">{system.timestamp}</Attribute>
  </Attributes>
</SetOAuthV2Info>
```

### Auto-populated Variables

After `VerifyAccessToken` succeeds:

| Variable | Description |
|---|---|
| `oauthv2accesstoken.{policy}.access_token` | The access token value |
| `oauthv2accesstoken.{policy}.scope` | Granted scopes (space-separated) |
| `oauthv2accesstoken.{policy}.token_type` | Token type (Bearer) |
| `oauthv2accesstoken.{policy}.expires_in` | Remaining lifetime in seconds |
| `oauthv2accesstoken.{policy}.status` | Token status (approved/revoked/expired) |
| `oauthv2accesstoken.{policy}.client_id` | Client ID that obtained the token |
| `oauthv2accesstoken.{policy}.developer.email` | Developer email |
| `oauthv2accesstoken.{policy}.developer.app.name` | App name |
| `oauthv2accesstoken.{policy}.{custom-attr}` | Custom attribute values |
| `apiproduct.name` | API product name |

### Scope Validation

Scopes are defined on API products and validated during token verification:
```xml
<OAuthV2 name="OAuth-VerifyWithScope">
  <Operation>VerifyAccessToken</Operation>
  <Scope>read write admin</Scope>
</OAuthV2>
```

**Important: Scope check is logical OR** — the token needs ANY ONE of the listed scopes, not all of them. To enforce AND (require multiple scopes), use separate VerifyAccessToken policies:
```xml
<Step><Name>OAuth-RequireRead</Name></Step>   <!-- Scope: read -->
<Step><Name>OAuth-RequireWrite</Name></Step>  <!-- Scope: write -->
```

If `<Scope>` is omitted or empty, no scope validation is performed.

### OAuth Gotchas

**180-second cache:** Apigee caches OAuth entities (tokens, apps, products) for a minimum of 180 seconds. `ExpiresIn` values below 180000ms cannot be reliably enforced. Revoked tokens may continue to work for up to 3 minutes.

**JWT vs opaque tokens:** Apigee can issue JWT-format tokens (RFC 9068). JWT tokens are validated by signature and expiry — they **cannot be revoked** once issued. Use opaque tokens when revocation capability is required.

**GenerateResponse=false:** When disabled, no response body is returned. Token values are only available as flow variables (`oauthv2accesstoken.{policy}.access_token`, etc.). Use AssignMessage to craft a custom response.

**Token transmission:** Clients send tokens via `Authorization: Bearer {token}` header by default. The VerifyAccessToken policy strips the "Bearer " prefix automatically.

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

Additional elements: `<Id>` (JWT ID/jti claim, auto-generates UUID if omitted), `<NotBefore>` (nbf claim, e.g., `<NotBefore>0s</NotBefore>`), `<AdditionalHeaders>` (custom JWT header claims, not payload). Claim `type` attribute supports: `string`, `number`, `boolean`, `map`. Set `array="true"` on `<Claim>` for array values.

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

`<TimeAllowance>` adds a grace period (in seconds) for exp/nbf validation (e.g., `<TimeAllowance>60s</TimeAllowance>` allows 60s clock skew). When using `<JWKS uri="..."/>`, Apigee caches the JWKS for 300 seconds — key rotation takes up to 5 minutes to take effect.

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

Encoding attributes: `<SecretKey encoding="utf8|hex|base16|base64">`, `<Output encoding="hex|base16|base64|base64url">` (default: base64), `<VerificationValue encoding="hex|base16|base64|base64url">`. Encoding mismatch between signing and verification is a common source of silent failures.

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

Supports both IPv4 and IPv6 addresses. Add `<ValidateBasedOn>` to control which IP is checked when `X-Forwarded-For` contains multiple IPs: `FIRST` (leftmost/client), `LAST` (rightmost/nearest proxy), or default checks all.

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

**Important:** This policy only executes when the request `Content-Type` is `application/json`. Requests with other content types (or no content type) bypass threat protection entirely.

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

**Important:** This policy only executes when the request `Content-Type` is `application/xml`, `text/xml`, or `application/*+xml`. Other content types bypass validation.

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

Additional elements: `<MaxPayloadSizeInBytes>` (limit payload size), `<Source>` (`request`/`response`/`message`). `<OperationType>` values: `query`, `mutation`, `subscription`. `<Action>` values: `parse` (syntax only), `parse-verify` (validate against schema). Schema file location: `apiproxy/resources/graphql/`.

## API Products, Apps, and Developers

The security policies above validate credentials against the Apigee entity model:

- **API Products** define which API proxies, resource paths, environments, and scopes are accessible. They represent a bundle of API capabilities offered as a unit.
- **Developer Apps** are registered by developers and associated with one or more API Products. Each app receives a consumer key (API key) and secret.
- **Developers** represent the people or organizations consuming APIs. They own one or more developer apps.

When `VerifyAPIKey` or `OAuthV2 VerifyAccessToken` succeeds, Apigee resolves the credential back to the app, developer, and product. Flow variables like `apiproduct.name`, `developer.email`, and `developer.app.name` become available for use in conditions, quotas, analytics, and downstream policies.

---

[Mediation Policies](policies_mediation.md) | [Proxy Bundle Anatomy](proxy_bundle_anatomy.md) | [Flows and Execution](flows_and_execution.md) | [Flow Variables and Conditions](flow_variables_and_conditions.md) | [Endpoints and Routing](endpoints_and_routing.md)
