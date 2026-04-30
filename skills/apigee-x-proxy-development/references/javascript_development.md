# JavaScript Development in Apigee X

## JavaScript Policy Configuration

```xml
<Javascript name="JS-TransformResponse">
  <ResourceURL>jsc://transform-response.js</ResourceURL>
</Javascript>
```

JavaScript files are stored in the `apiproxy/resources/jsc/` directory. The ResourceURL format is `jsc://filename.js`. Use IncludeURL to load shared libraries before the main script executes.

Add `timeLimit` attribute to prevent runaway scripts: `<Javascript name="JS-Transform" timeLimit="200">`. Default timeout varies; always set explicitly in production.

```xml
<Javascript name="JS-ProcessOrder">
  <IncludeURL>jsc://utils.js</IncludeURL>
  <IncludeURL>jsc://validation-helpers.js</IncludeURL>
  <ResourceURL>jsc://process-order.js</ResourceURL>
</Javascript>
```

### Inline JavaScript (for very short scripts)

```xml
<Javascript name="JS-SetVariable">
  <Source>
    context.setVariable("custom.processed", "true");
  </Source>
</Javascript>
```

## Object Model

### context Object

The primary object providing access to flow state and variables.

```javascript
// Get/set/remove flow variables
var userId = context.getVariable("request.queryparam.user_id");
context.setVariable("custom.processedAt", new Date().toISOString());
context.removeVariable("temp.scratch");

// Current flow phase
var phase = context.flow;
// Values: PROXY_REQ_FLOW, TARGET_REQ_FLOW, TARGET_RES_FLOW, PROXY_RES_FLOW

// Access message objects by phase
var proxyReq = context.proxyRequest;    // Client request (inbound)
var proxyResp = context.proxyResponse;  // Client response (outbound)
var targetReq = context.targetRequest;  // Backend request (outbound)
var targetResp = context.targetResponse; // Backend response (inbound)
```

### request and response Shortcuts

```javascript
// Request properties (shorthand for current phase)
var method = context.getVariable("request.verb");
var path = context.getVariable("request.path");
var body = context.getVariable("request.content");
var header = context.getVariable("request.header.Authorization");
var param = context.getVariable("request.queryparam.id");

// Response properties
var status = context.getVariable("response.status.code");
var respBody = context.getVariable("response.content");
var respHeader = context.getVariable("response.header.Content-Type");
```

### Setting Response

```javascript
context.setVariable("response.content", JSON.stringify(payload));
context.setVariable("response.header.Content-Type", "application/json");
context.setVariable("response.status.code", 200);
```

## Common Patterns

### JSON Parsing and Transformation

```javascript
var reqBody = JSON.parse(context.getVariable("request.content"));

var transformed = {
  id: reqBody.userId,
  fullName: reqBody.firstName + " " + reqBody.lastName,
  processedAt: new Date().toISOString()
};

context.setVariable("request.content", JSON.stringify(transformed));
```

### Dynamic Target Routing

```javascript
var tier = context.getVariable("apiproduct.name");

if (tier === "premium") {
  context.setVariable("target.url", "https://premium-api.example.com/v2");
} else {
  context.setVariable("target.url", "https://standard-api.example.com/v1");
}
```

### Response Aggregation from Multiple ServiceCallouts

```javascript
var userResp = JSON.parse(context.getVariable("userResponse.content"));
var orderResp = JSON.parse(context.getVariable("orderResponse.content"));

var result = {
  user: userResp,
  orders: orderResp.items,
  total: orderResp.total,
  generatedAt: new Date().toISOString()
};

context.setVariable("response.content", JSON.stringify(result));
context.setVariable("response.header.Content-Type", "application/json");
context.setVariable("response.status.code", 200);
```

### Error Handling in JavaScript

```javascript
try {
  var data = JSON.parse(context.getVariable("request.content"));

  if (!data.email) {
    context.setVariable("custom.errorCode", "MISSING_EMAIL");
    context.setVariable("custom.errorMessage", "Email field is required");
    context.setVariable("custom.raiseError", "true");
  }
} catch (e) {
  context.setVariable("custom.errorCode", "INVALID_JSON");
  context.setVariable("custom.errorMessage", "Request body is not valid JSON");
  context.setVariable("custom.raiseError", "true");
}
```

Then in the flow, follow with a conditional RaiseFault:

```xml
<Step>
  <Name>JS-ValidateInput</Name>
</Step>
<Step>
  <Condition>custom.raiseError = "true"</Condition>
  <Name>RF-ValidationError</Name>
</Step>
```

### Header Manipulation

```javascript
// Copy and transform headers
var authHeader = context.getVariable("request.header.Authorization");
if (authHeader && authHeader.indexOf("Bearer ") === 0) {
  var token = authHeader.substring(7);
  context.setVariable("custom.bearerToken", token);
}

// Add multiple headers
context.setVariable("request.header.X-Forwarded-For",
  context.getVariable("client.ip"));
context.setVariable("request.header.X-Request-ID",
  context.getVariable("system.uuid"));
```

### Iterating Over Collections

```javascript
var items = JSON.parse(context.getVariable("response.content"));

var filtered = items.filter(function(item) {
  return item.status === "active";
});

context.setVariable("response.content", JSON.stringify(filtered));
```

### Pagination and Array Slicing

```javascript
var allItems = JSON.parse(context.getVariable("response.content"));
var offset = parseInt(context.getVariable("request.queryparam.offset") || "0");
var limit = parseInt(context.getVariable("request.queryparam.limit") || "20");

var paged = allItems.slice(offset, offset + limit);
var result = {
  items: paged,
  totalCount: allItems.length,
  offset: offset,
  limit: limit
};

context.setVariable("response.content", JSON.stringify(result));
```

### Key-Value Map (KVM) Lookup via Variables

```javascript
// After a KeyValueMapOperations policy has extracted values
var configValue = context.getVariable("private.kvm.apiEndpoint");
var apiSecret = context.getVariable("private.kvm.apiSecret");

if (configValue) {
  context.setVariable("target.url", configValue);
}
```

## httpClient for Async HTTP Calls

```javascript
var url = "https://api.example.com/validate";
var headers = { "Content-Type": "application/json" };
var body = JSON.stringify({ token: context.getVariable("custom.token") });

var exchange = httpClient.send(new Request(url, "POST", headers, body));
exchange.waitForComplete();

if (exchange.isSuccess()) {
  var resp = exchange.getResponse();
  context.setVariable("custom.validationStatus", resp.status);
  context.setVariable("custom.validationBody", resp.content);
} else {
  context.setVariable("custom.validationStatus", "error");
}
```

`httpClient.send()` is non-blocking until `waitForComplete()` is called. Use this for calls that cannot be expressed as ServiceCallout policies.

Convenience method for simple GET requests:

```javascript
var exchange = httpClient.get("https://api.example.com/data");
exchange.waitForComplete();
if (exchange.isSuccess()) {
  var resp = exchange.getResponse();
}
```

### Parallel HTTP Calls with httpClient

```javascript
var exchange1 = httpClient.send(
  new Request("https://api.example.com/users/123", "GET", {}, null)
);
var exchange2 = httpClient.send(
  new Request("https://api.example.com/orders?user=123", "GET", {}, null)
);

exchange1.waitForComplete();
exchange2.waitForComplete();

var user = {};
var orders = [];

if (exchange1.isSuccess()) {
  user = JSON.parse(exchange1.getResponse().content);
}
if (exchange2.isSuccess()) {
  orders = JSON.parse(exchange2.getResponse().content);
}

var result = { user: user, orders: orders };
context.setVariable("response.content", JSON.stringify(result));
context.setVariable("response.header.Content-Type", "application/json");
```

## crypto Object

The built-in `crypto` object provides hashing operations via an object-based API. Each method returns a hash object supporting `.update()` and `.digest()` / `.digest64()`.

```javascript
// SHA-256 hash (hex output)
var hash = crypto.getSHA256().update(context.getVariable("request.content")).digest();
// SHA-256 hash (base64 output)
var hash64 = crypto.getSHA256().update("data").digest64();
// SHA-1 hash
var sha1 = crypto.getSHA1().update("data").digest();
// MD5 hash
var md5 = crypto.getMD5().update("data").digest();

// Chain multiple updates before final digest
var combined = crypto.getSHA256().update("part1").update("part2").digest();
```

Note: There is no `crypto.SHA256()`, `crypto.MD5()`, or `crypto.base64()` function. Always use the `get*()` methods. For base64 output, use `.digest64()` on the hash object.

## print() for Debug Logging

```javascript
// Output goes to the Apigee debug session / trace tool
print("Processing request for user: " + userId);
print("Target URL resolved to: " + targetUrl);
```

Use `print()` statements to emit debug information visible in the Apigee trace/debug tool. Remove or guard verbose logging before deploying to production.

## Limitations

- No Node.js modules -- `require()` and `import` are not available
- No file system access
- No network access except through the `httpClient` object
- Execution timeout (default varies by environment)
- ECMAScript 5.1 compatible -- no ES6+ features (no arrow functions, `let`/`const`, template literals, destructuring, Promises)
- No access to Java classes (use the JavaCallout policy instead)
- String concatenation with `+` operator only (no template literals)

## When to Use JavaScript vs Built-in Policies

| Scenario | Recommendation |
|---|---|
| Set/remove headers | AssignMessage policy |
| Extract values from JSON/XML | ExtractVariables policy |
| Simple payload transformation | AssignMessage with message templates |
| Complex JSON transformation | JavaScript |
| Conditional logic with multiple branches | JavaScript |
| Response aggregation | JavaScript |
| Dynamic routing logic | JavaScript |
| Crypto operations | JavaScript (crypto object) |
| Data validation with complex rules | JavaScript |
| XML to JSON conversion | XMLToJSON policy |
| Simple variable assignment | AssignMessage policy |
| Pattern matching / regex extraction | ExtractVariables policy |

Prefer built-in policies when they can accomplish the task. Policies are optimized by the Apigee runtime and easier to maintain. Use JavaScript when the logic exceeds what policies can express declaratively.

---

See also:
- [Proxy Bundle Anatomy](proxy_bundle_anatomy.md)
- [Flows and Execution](flows_and_execution.md)
- [Flow Variables and Conditions](flow_variables_and_conditions.md)
- [Fault Handling](fault_handling.md)
- [Mediation Policies](policies_mediation.md)
- [Integration Policies](policies_integration.md)
