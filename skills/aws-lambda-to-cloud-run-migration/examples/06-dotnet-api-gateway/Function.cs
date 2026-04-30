// Copyright 2026 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.DynamoDBv2;
using Amazon.DynamoDBv2.Model;
using Amazon.SimpleNotificationService;
using Amazon.SimpleNotificationService.Model;
using System.Text.Json;

[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.SystemTextJson.DefaultLambdaJsonSerializer))]

namespace OrdersApi;

/// <summary>
/// AWS Lambda handler for an Orders API.
/// Triggered by API Gateway (REST), reads/writes DynamoDB, and publishes to SNS.
///
/// MIGRATION NOTE: On Cloud Run, this becomes an ASP.NET Core Minimal API.
/// - Replace ILambdaContext + APIGatewayProxyRequest with HttpContext
/// - Replace AmazonDynamoDBClient with Google.Cloud.Datastore or Npgsql (Cloud SQL)
/// - Replace AmazonSimpleNotificationServiceClient with Google.Cloud.PubSub.V1
/// </summary>
public class Function
{
    private readonly AmazonDynamoDBClient _dynamoDb;
    private readonly AmazonSimpleNotificationServiceClient _sns;
    private readonly string _tableName;
    private readonly string _snsTopicArn;

    public Function()
    {
        _dynamoDb = new AmazonDynamoDBClient();
        _sns = new AmazonSimpleNotificationServiceClient();
        _tableName = Environment.GetEnvironmentVariable("ORDERS_TABLE") ?? "orders";
        _snsTopicArn = Environment.GetEnvironmentVariable("SNS_TOPIC_ARN") ?? string.Empty;
    }

    /// <summary>
    /// Lambda entry point — triggered by API Gateway POST /orders
    /// </summary>
    public async Task<APIGatewayProxyResponse> FunctionHandler(
        APIGatewayProxyRequest request, ILambdaContext context)
    {
        context.Logger.LogInformation($"Processing {request.HttpMethod} {request.Path}");

        try
        {
            var body = JsonSerializer.Deserialize<OrderRequest>(request.Body)
                ?? throw new ArgumentException("Empty request body");

            // Write to DynamoDB — maps to Cloud SQL / Firestore on GCP
            var orderId = Guid.NewGuid().ToString();
            await _dynamoDb.PutItemAsync(new PutItemRequest
            {
                TableName = _tableName,
                Item = new Dictionary<string, AttributeValue>
                {
                    ["order_id"] = new AttributeValue { S = orderId },
                    ["product"]  = new AttributeValue { S = body.Product },
                    ["quantity"] = new AttributeValue { N = body.Quantity.ToString() },
                    ["status"]   = new AttributeValue { S = "PENDING" }
                }
            });

            // Publish to SNS — maps to Pub/Sub on GCP
            if (!string.IsNullOrEmpty(_snsTopicArn))
            {
                await _sns.PublishAsync(new PublishRequest
                {
                    TopicArn = _snsTopicArn,
                    Message  = JsonSerializer.Serialize(new { order_id = orderId, status = "PENDING" }),
                    Subject  = "OrderCreated"
                });
            }

            return new APIGatewayProxyResponse
            {
                StatusCode = 201,
                Body       = JsonSerializer.Serialize(new { order_id = orderId, status = "PENDING" }),
                Headers    = new Dictionary<string, string> { ["Content-Type"] = "application/json" }
            };
        }
        catch (Exception ex)
        {
            context.Logger.LogError($"Error: {ex.Message}");
            return new APIGatewayProxyResponse
            {
                StatusCode = 500,
                Body       = JsonSerializer.Serialize(new { error = ex.Message })
            };
        }
    }
}

public record OrderRequest(string Product, int Quantity);
