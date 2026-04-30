# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Example AWS Terraform configuration equivalent to the OrderApiStack CDK example.
# This file intentionally represents the AWS-side IaC that would be migrated.
#
# GCP Migration target: see Path A (Terraform) and Path B (Scripted) in
# references/iac_translation.md for the full before/after templates.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# ── Variables ────────────────────────────────────────────────────────────────

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ── DynamoDB Table (→ Firestore or Cloud SQL on GCP) ─────────────────────────

resource "aws_dynamodb_table" "orders" {
  name         = "orders-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ── SNS Topic (→ Pub/Sub topic on GCP) ───────────────────────────────────────

resource "aws_sns_topic" "order_events" {
  name = "order-events-${var.environment}"
}

# ── SQS Queue (→ Cloud Tasks queue on GCP) ───────────────────────────────────

resource "aws_sqs_queue" "processing_queue" {
  name                       = "processing-queue-${var.environment}"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400
}

# ── IAM Execution Role (→ GCP Service Account) ───────────────────────────────

resource "aws_iam_role" "lambda_exec" {
  name = "orders-lambda-exec-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_permissions" {
  name = "orders-lambda-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Resource = aws_dynamodb_table.orders.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = aws_sns_topic.order_events.arn
      },
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = aws_sqs_queue.processing_queue.arn
      }
    ]
  })
}

# ── Lambda Function (→ google_cloud_run_v2_service on GCP) ───────────────────

resource "aws_lambda_function" "orders_api" {
  function_name = "orders-api-${var.environment}"
  role          = aws_iam_role.lambda_exec.arn
  handler       = "handler.handler"
  runtime       = "nodejs18.x"
  memory_size   = 256
  timeout       = 30

  # In practice, source_code_hash + filename or s3_bucket/s3_key
  filename = "dist/orders-api.zip"

  environment {
    variables = {
      ORDERS_TABLE     = aws_dynamodb_table.orders.name
      SNS_TOPIC_ARN    = aws_sns_topic.order_events.arn
      SQS_QUEUE_URL    = aws_sqs_queue.processing_queue.url
      NODE_ENV         = var.environment
    }
  }

  tags = {
    Environment = var.environment
  }
}

# ── API Gateway (→ built-in Cloud Run HTTPS URL, or google_api_gateway_api) ──

resource "aws_api_gateway_rest_api" "orders_api_gw" {
  name        = "orders-api-${var.environment}"
  description = "REST API for the Orders service"
}

resource "aws_api_gateway_integration" "lambda_integration" {
  rest_api_id             = aws_api_gateway_rest_api.orders_api_gw.id
  resource_id             = aws_api_gateway_rest_api.orders_api_gw.root_resource_id
  http_method             = "ANY"
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.orders_api.invoke_arn
}

resource "aws_lambda_permission" "apigw_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.orders_api.function_name
  principal     = "apigateway.amazonaws.com"
}

# ── Outputs ───────────────────────────────────────────────────────────────────

output "api_gateway_url" {
  description = "The invoke URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.orders_api_gw.id}.execute-api.us-east-1.amazonaws.com/${var.environment}"
}

output "lambda_function_arn" {
  value = aws_lambda_function.orders_api.arn
}
