# Containerization & Refactoring Strategy for Cloud Run

When migrating from AWS Lambda to Google Cloud Run, you must first answer one critical question: **Is this code a Service or a Job?**

## 0. The Paradigm Choice: Services vs. Jobs

**AWS Lambda** executes a single handler function regardless of whether it was triggered by a user clicking a button on a website, or a nightly cron schedule. 

**Google Cloud Run** splits these paradigms for better performance and cost:

### Path A: Cloud Run Service (For APIs, Webhooks, and Event-Driven Architecture)
- **Use Case:** The Lambda was behind API Gateway, an ALB, or triggered by SNS/SQS.
- **Requirement:** The container **MUST start an HTTP Web Server** and listen continuously on the port defined by `$PORT` (default 8080).
- **Migration:** You must wrap the Lambda logic in a framework like Express (Node.js), FastAPI/Flask (Python), or `net/http` (Go), OR use the Google Functions Framework.

### Path B: Cloud Run Job (For Cron Jobs, Batch Processing, and Scripts)
- **Use Case:** The Lambda was triggered by EventBridge (Cron), executed data processing, or took up to 15 minutes to run.
- **Requirement:** The container **DOES NOT need a web server**. It runs as a standard script from top to bottom and exits (`process.exit(0)` or `sys.exit(0)`).
- **Migration:** This is actually *easier* than a Service. You simply execute the main file. 

*Example: Python Job Dockerfile*
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# NO web server needed. Just execute the script!
CMD ["python", "main.py"] 
```

---

*If you determine the workload is a **Service**, proceed to choose one of the following two containerization strategies:*

## Strategy 1: The "Functions" Path (Google Functions Framework)
**Best for:** 1:1 migrations, keeping code logic as close to the original Lambda as possible, and avoiding infrastructure boilerplate.

Google provides the open-source **Functions Framework** to wrap function-level code into a Cloud Run-compatible web server automatically.

### The "No Dockerfile" Advantage (Buildpacks)
When using the Functions Framework, you **do not need a Dockerfile**. Google Cloud Buildpacks will automatically detect your language and build the container for you when you run:
`gcloud run deploy my-service --source .`

### Language Examples

#### Node.js
**package.json**: `"dependencies": { "@google-cloud/functions-framework": "^3.0.0" }`

**BEFORE (AWS Lambda):**
```javascript
exports.handler = async (event, context) => {
  return {
    statusCode: 200,
    body: JSON.stringify({ message: "Success", data: JSON.parse(event.body) })
  };
};
```

**AFTER (GCP Cloud Run - HTTP Trigger):**
```javascript
const functions = require('@google-cloud/functions-framework');

functions.http('myHttpFunction', (req, res) => {
  // Interact directly with the Express-like request and response objects
  res.status(200).send({ message: 'Success', data: req.body });
});
```

**AFTER (GCP Cloud Run - Eventarc/PubSub Trigger):**
```javascript
const functions = require('@google-cloud/functions-framework');

functions.cloudEvent('myEventFunction', cloudEvent => {
  // GCP uses standardized CloudEvents instead of proprietary AWS Event shapes
  console.log(`Event Data:`, cloudEvent.data);
});
```

#### Python
**requirements.txt**: `functions-framework==3.*`

**BEFORE (AWS Lambda):**
```python
import json

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Success", "data": body})
    }
```

**AFTER (GCP Cloud Run - HTTP Trigger):**
```python
import functions_framework

@functions_framework.http
def my_http_function(request):
    # Request is a Flask Request object
    return {"message": "Success", "data": request.get_json(silent=True)}, 200
```

#### Java (Functions Framework API)
Google provides a lightweight Functions Framework API for Java, allowing a clean transition from AWS Lambda's `RequestHandler`.

**pom.xml dependencies:**
```xml
<dependency>
  <groupId>com.google.cloud.functions</groupId>
  <artifactId>functions-framework-api</artifactId>
  <version>1.1.0</version>
</dependency>
```

**BEFORE (AWS Lambda):**
```java
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import java.util.Map;

public class MyHandler implements RequestHandler<Map<String,String>, String> {
    @Override
    public String handleRequest(Map<String,String> event, Context context) {
        return "{\"message\": \"Success\"}";
    }
}
```

**AFTER (GCP Cloud Run):**
```java
package com.example;

import com.google.cloud.functions.HttpFunction;
import com.google.cloud.functions.HttpRequest;
import com.google.cloud.functions.HttpResponse;
import java.io.BufferedWriter;

public class MyFunction implements HttpFunction {
    @Override
    public void service(HttpRequest request, HttpResponse response) throws Exception {
        BufferedWriter writer = response.getWriter();
        response.setStatusCode(200);
        response.setContentType("application/json");
        writer.write("{\"message\": \"Success\"}");
    }
}
```

### Optional: Functions Framework + Custom Dockerfile
If your function requires specific OS-level dependencies (e.g., C-libraries, `ffmpeg`, specific Debian packages), you can still use the Functions Framework but provide a custom `Dockerfile`.

*Example Python Functions Framework Dockerfile:*
```dockerfile
FROM python:3.11-slim
# Install OS dependencies not handled by standard Buildpacks
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Start the functions framework explicitly
CMD exec functions-framework --target=my_http_function --port=$PORT
```

#### PHP (Shim / Framework Wrap)
Google does not provide a Functions Framework for PHP. If you are migrating a PHP Lambda (often powered by the **Bref** framework), you have two choices for turning it into an HTTP service:

1. **Use a PHP Web Framework:** Wrap your logic in Laravel, Symfony, or a micro-framework like Slim.
2. **Use a Shim:** Write a small vanilla PHP script that listens on `0.0.0.0:$PORT` using a modern PHP app server like FrankenPHP or RoadRunner.

**BEFORE (AWS Lambda with Bref):**
```php
<?php
// handler.php
return function ($event, $context) {
    return [
        'statusCode' => 200,
        'body' => json_encode(['message' => 'Success', 'data' => $event])
    ];
};
```

**AFTER (GCP Cloud Run - Slim PHP Example):**
```php
<?php
// index.php
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\Factory\AppFactory;

require __DIR__ . '/vendor/autoload.php';

$app = AppFactory::create();

// Catch-all route acting as the Lambda shim
$app->any('/[{path:.*}]', function (Request $request, Response $response, array $args) {
    $event = [
        'path' => $request->getUri()->getPath(),
        'httpMethod' => $request->getMethod(),
        'headers' => $request->getHeaders(),
        'queryStringParameters' => $request->getQueryParams(),
        'body' => (string) $request->getBody(),
    ];
    
    // Call legacy Bref handler
    $handler = require 'handler.php';
    $result = $handler($event, null);
    
    $response->getBody()->write($result['body']);
    return $response->withStatus($result['statusCode']);
});

$app->run();
```

#### .NET / C# — ASP.NET Core Minimal API

.NET Lambda functions come in two flavors — and each has a different migration path:

**Flavor A: Simple `FunctionHandler` (no HTTP server)** — Used for event-driven triggers (SQS, SNS, DynamoDB Streams). The handler signature takes a typed event object and `ILambdaContext`. On Cloud Run, this becomes a **minimal HTTP endpoint** or a **Cloud Run Job**.

**Flavor B: `LambdaEntryPoint` inheriting `APIGatewayProxyFunction`** — Used for full ASP.NET Core apps running behind API Gateway. On Cloud Run, _remove the Lambda adapter entirely_ and run ASP.NET Core directly. This is the easiest migration.

---

**BEFORE (AWS Lambda — Flavor A, event handler):**
```csharp
// Function.cs
using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.DynamoDBv2;

public class Function
{
    private readonly AmazonDynamoDBClient _dynamo = new();

    public async Task<APIGatewayProxyResponse> FunctionHandler(
        APIGatewayProxyRequest request, ILambdaContext context)
    {
        // ... handler logic calling DynamoDB, SNS, etc.
        return new APIGatewayProxyResponse { StatusCode = 200, Body = "{}" };
    }
}
```

**AFTER (Cloud Run — ASP.NET Core Minimal API):**
```csharp
// Program.cs — replaces Function.cs + LambdaEntryPoint entirely
using Google.Cloud.Firestore;         // replaces Amazon.DynamoDBv2
using Google.Cloud.PubSub.V1;        // replaces Amazon.SimpleNotificationService

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddSingleton(FirestoreDb.Create(
    Environment.GetEnvironmentVariable("GOOGLE_CLOUD_PROJECT")));
builder.Services.AddSingleton(PublisherServiceApiClient.Create());

var app = builder.Build();
app.MapPost("/orders", async (OrderRequest req, FirestoreDb db, PublisherServiceApiClient pub) =>
{
    // Write to Firestore (replaces DynamoDBv2 PutItem)
    var docRef = db.Collection("orders").Document();
    await docRef.SetAsync(new { product = req.Product, quantity = req.Quantity, status = "PENDING" });

    // Publish to Pub/Sub (replaces SNS Publish)
    var topicName = TopicName.FromProjectTopic(
        Environment.GetEnvironmentVariable("GOOGLE_CLOUD_PROJECT"),
        Environment.GetEnvironmentVariable("PUBSUB_TOPIC"));
    await pub.PublishAsync(topicName, new[] {
        new PubsubMessage { Data = Google.Protobuf.ByteString.CopyFromUtf8(
            System.Text.Json.JsonSerializer.Serialize(new { order_id = docRef.Id })) }
    });

    return Results.Created($"/orders/{docRef.Id}", new { order_id = docRef.Id, status = "PENDING" });
})
.WithName("CreateOrder");

// Cloud Run injects PORT — ASP.NET Core reads ASPNETCORE_URLS or listen on $PORT
app.Run();

record OrderRequest(string Product, int Quantity);
```

**Dockerfile (Multi-stage build — .NET 8 on Cloud Run):**
```dockerfile
# Stage 1: Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY *.csproj .
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app/publish --no-restore

# Stage 2: Runtime (use the smaller aspnet image, NOT the SDK)
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .

# Cloud Run injects $PORT. ASP.NET Core respects ASPNETCORE_HTTP_PORTS (>= .NET 8)
# or ASPNETCORE_URLS for older versions.
ENV ASPNETCORE_HTTP_PORTS=${PORT:-8080}
ENTRYPOINT ["dotnet", "OrdersApi.dll"]
```

**`csproj` — NuGet package migration:**
```xml
<!-- REMOVE: AWS-specific packages -->
<!-- <PackageReference Include="Amazon.Lambda.Core" Version="2.*" /> -->
<!-- <PackageReference Include="Amazon.Lambda.APIGatewayEvents" Version="2.*" /> -->
<!-- <PackageReference Include="AWSSDK.DynamoDBv2" Version="3.*" /> -->
<!-- <PackageReference Include="AWSSDK.SimpleNotificationService" Version="3.*" /> -->

<!-- ADD: GCP equivalents -->
<PackageReference Include="Google.Cloud.Firestore"   Version="3.*" />
<PackageReference Include="Google.Cloud.PubSub.V1"   Version="3.*" />
<PackageReference Include="Google.Cloud.SecretManager.V1" Version="2.*" />
<!-- Authentication is handled automatically via the Cloud Run Service Account -->
<!-- No explicit credential management needed (no AWS.Credentials equivalent) -->
```

> **Connection Pool Note (.NET + EF Core):** Lambda instances handle one request at a time, so EF Core's default connection pool of 1 is fine. Cloud Run handles concurrent requests per instance — increase `MaxPoolSize` in your `DbContext` options to match your expected concurrency (e.g., `Pooling=true;MinPoolSize=1;MaxPoolSize=20` in the connection string).

---

## Strategy 2: The "Microservice / Cloud Run Native" Path
**Best for:** Consolidating multiple related Lambdas into a single robust microservice, or utilizing the native, highly-concurrent web server capabilities of languages like Go.

Instead of keeping 10 distinct Lambdas as 10 distinct Cloud Run services, you refactor them into standard web routes using native libraries or frameworks. This approach *requires* you to define a `Dockerfile`.

### Language Examples

#### Go (Native net/http)
Go's built-in HTTP server is so robust and lightweight that the Functions Framework is rarely needed. A multi-stage build results in incredibly small, secure images.

**Dockerfile (Multi-stage Distroless):**
```dockerfile
# Build Stage
FROM golang:1.21 as builder
WORKDIR /app
COPY go.* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -v -o server

# Production Stage (Distroless for security & size)
FROM gcr.io/distroless/static-debian11
COPY --from=builder /app/server /server
CMD ["/server"]
```

**BEFORE (AWS Lambda using aws-lambda-go):**
```go
package main

import (
	"context"
	"github.com/aws/aws-lambda-go/lambda"
)

type MyEvent struct {
	Name string `json:"name"`
}

func HandleRequest(ctx context.Context, name MyEvent) (string, error) {
	return "Success", nil
}

func main() {
	lambda.Start(HandleRequest)
}
```

**AFTER (GCP Cloud Run):**
```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
)

func main() {
	http.HandleFunc("/", handler)

	// Cloud Run injects the PORT environment variable
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Listening on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func handler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]string{"message": "Success"})
}
```

#### Python (FastAPI with Uvicorn)
Consolidate many Lambdas into a single FastAPI deployment.

**Dockerfile:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

**main.py:**
```python
import os
from fastapi import FastAPI, Request
# Assuming these were previously separate Lambda functions in separate files
from old_lambdas import user_handler, order_handler

app = FastAPI()

@app.post("/users")
async def create_user(request: Request):
    # Shim to adapt FastAPI request to the old Lambda handler signature
    event = {"body": await request.json()}
    response = user_handler.lambda_handler(event, {})
    return response

@app.post("/orders")
async def create_order(request: Request):
    event = {"body": await request.json()}
    response = order_handler.lambda_handler(event, {})
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

#### PHP (FrankenPHP or RoadRunner)
For production PHP on Cloud Run, **avoid traditional Apache/Nginx + PHP-FPM** setups if possible. They require two processes running in the same container, which is harder to configure for logs and scaling. Instead, use modern, single-binary application servers like **FrankenPHP** or **RoadRunner**.

**Dockerfile (FrankenPHP - Recommended for Laravel/Symfony/Slim):**
```dockerfile
# Use the official FrankenPHP image
FROM dunglas/frankenphp:1-php8.2-alpine

WORKDIR /app

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Copy application files
COPY . .
RUN composer install --no-dev --optimize-autoloader

# Cloud Run injects $PORT at runtime (default 8080). SERVER_NAME must be set
# dynamically at container start — do NOT hardcode it as an ENV instruction.
CMD ["sh", "-c", "SERVER_NAME=:${PORT:-8080} frankenphp run --config /etc/caddy/Caddyfile"]
```

**Dockerfile (RoadRunner - High Performance Worker Pool):**
```dockerfile
FROM php:8.2-cli-alpine

# Install RoadRunner binary
COPY --from=spiralscout/roadrunner:2023.3 /usr/bin/rr /usr/bin/rr

WORKDIR /app
COPY composer.json composer.lock ./
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer \
    && composer install --no-dev --optimize-autoloader

COPY . .

# Create a basic .rr.yaml dynamically if not present, connecting to $PORT
CMD echo "http: { address: 0.0.0.0:${PORT:-8080} }" > .rr.yaml && \
    rr serve -c .rr.yaml
```


## 3. The API Gateway "Shim" Pattern (Lift & Shift)

If the Lambda was previously triggered by API Gateway, the original AWS code heavily expects an AWS API Gateway `event` dictionary (e.g., `event['queryStringParameters']`, `event['headers']`). 

Rewriting hundreds of handler files to use native HTTP frameworks (like `req.body`) is time-consuming. Instead, use an **Adapter (Shim) Pattern**. The web server catches the incoming HTTP request, translates it into an AWS API Gateway event shape, passes it to the unmodified Lambda handler, and translates the response back to HTTP.

**Python Example (FastAPI Adapter):**
```python
from fastapi import FastAPI, Request
from old_lambda_code import lambda_handler # The unmodified AWS code

app = FastAPI()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path: str):
    # 1. Translate GCP HTTP Request -> AWS API Gateway Event
    body_bytes = await request.body()
    event = {
        "resource": f"/{path}",
        "path": f"/{path}",
        "httpMethod": request.method,
        "headers": dict(request.headers),
        "queryStringParameters": dict(request.query_params) or None,
        "body": body_bytes.decode('utf-8') if body_bytes else None,
        "isBase64Encoded": False
    }
    
    # 2. Call the unmodified AWS Lambda handler
    # Note: AWS Context object is often mocked as an empty dict or dummy class
    response = lambda_handler(event, context={})
    
    # 3. Translate AWS Response -> GCP HTTP Response
    from fastapi.responses import JSONResponse
    import json
    
    body = response.get("body", "")
    try:
        body = json.loads(body) # Try to return native JSON if possible
    except:
        pass
        
    return JSONResponse(
        status_code=response.get("statusCode", 200),
        content=body,
        headers=response.get("headers", {})
    )
```
*This allows you to migrate to Cloud Run instantly, and gradually refactor the legacy handlers to native FastAPI/Express routes over time.*

---

## 4. Crucial: State & Concurrency Refactoring (Applies to ALL Strategies)

AWS Lambda initializes the environment, executes the handler for **exactly one** event, and waits. 
Cloud Run handles **multiple concurrent requests** (up to 1000) per container instance. 

**The Refactoring Rule:**
You must initialize expensive resources (Database connections, GCP SDK clients) **globally (outside the handler function)** so they are reused. However, you must ensure these global clients are **thread-safe** to handle Cloud Run's concurrency.

> **PHP Specific Warning:** If using traditional PHP-FPM, Cloud Run's concurrency setting essentially maps to `pm.max_children`. If using RoadRunner or FrankenPHP, PHP worker state *persists* across requests. You must avoid memory leaks or storing request-specific data in global singletons.

**Wrong (AWS pattern adapted poorly):**
```python
@functions_framework.http
def my_http_function(request):
    # BAD: Opens a new connection pool for EVERY concurrent request.
    # Will instantly exhaust database connections on Cloud Run.
    db = psycopg2.connect(dsn)
    db.execute("SELECT * FROM users")
```

**Right (GCP Cloud Run Native pattern):**
```python
# GOOD: Initialized globally. Reused by all threads safely.
from sqlalchemy import create_engine
# Ensure the pool size accounts for your expected concurrent requests
engine = create_engine(dsn, pool_size=5, max_overflow=2)

@functions_framework.http
def my_http_function(request):
    with engine.connect() as connection:
        result = connection.execute("SELECT * FROM users")
    return {"status": "ok"}, 200
```
