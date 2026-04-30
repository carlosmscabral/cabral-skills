// Copyright 2024 Google LLC
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

import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as sns from 'aws-cdk-lib/aws-sns';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';

/**
 * Example 4: TypeScript AWS CDK Stack
 *
 * Defines a Lambda-backed REST API with DynamoDB, an SNS topic, and an SQS queue.
 * This example is used to test CDK detection in analyze_lambda.py.
 *
 * GCP Migration path:
 *   - Lambda functions  → Cloud Run Services
 *   - API Gateway       → Cloud Run built-in HTTPS URL (or API Gateway on GCP)
 *   - DynamoDB          → Cloud Firestore or Cloud Spanner
 *   - SNS topic         → Pub/Sub topic
 *   - SQS queue         → Cloud Tasks queue
 *   - CDK stack         → Terraform (google provider) or CDKTF
 */
export class OrderApiStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // DynamoDB table for orders (→ Firestore or Cloud SQL)
    const ordersTable = new dynamodb.Table(this, 'OrdersTable', {
      tableName: 'orders',
      partitionKey: { name: 'order_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // SNS topic for order events (→ Pub/Sub topic)
    const orderEventsTopic = new sns.Topic(this, 'OrderEventsTopic', {
      topicName: 'order-events',
    });

    // SQS queue for async processing (→ Cloud Tasks queue)
    const processingQueue = new sqs.Queue(this, 'ProcessingQueue', {
      queueName: 'processing-queue',
      visibilityTimeout: cdk.Duration.seconds(30),
    });

    // Lambda function for the Orders API (→ Cloud Run Service)
    const ordersLambda = new lambda.Function(this, 'OrdersFunction', {
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'handler.handler',
      code: lambda.Code.fromAsset('src'),
      environment: {
        ORDERS_TABLE: ordersTable.tableName,
        SNS_TOPIC_ARN: orderEventsTopic.topicArn,
        SQS_QUEUE_URL: processingQueue.queueUrl,
      },
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
    });

    // Grant permissions
    ordersTable.grantReadWriteData(ordersLambda);
    orderEventsTopic.grantPublish(ordersLambda);
    processingQueue.grantSendMessages(ordersLambda);

    // API Gateway REST API (→ Cloud Run HTTPS URL or GCP API Gateway)
    const api = new apigw.LambdaRestApi(this, 'OrdersApi', {
      handler: ordersLambda,
      restApiName: 'Orders API',
      description: 'REST API for orders service',
    });

    new cdk.CfnOutput(this, 'ApiUrl', { value: api.url });
  }
}
