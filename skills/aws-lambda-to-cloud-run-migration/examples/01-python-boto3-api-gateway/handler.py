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

# Example 1: Python Lambda with boto3 (API Gateway trigger)
#
# This is a realistic example of a Lambda that:
# - Is triggered by API Gateway (REST API)
# - Uses boto3 to read from DynamoDB
# - Uses boto3 to publish an SNS notification on write
# - Has a raw HTTP call to an internal service using Client ID / Secret
#
# This example is intentionally representative of common AWS lock-ins
# so that analyze_lambda.py can surface meaningful findings.

import json
import os
import boto3
import requests

# --- AWS SDK clients (initialized at module level — Lambda anti-pattern) ---
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')

TABLE_NAME = os.environ.get('ORDERS_TABLE', 'orders')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:123456789012:order-events')
INTERNAL_API_URL = os.environ.get('INTERNAL_API_URL', 'https://internal.example.com/enrich')

# Hardcoded credentials — a common anti-pattern this skill helps identify
CLIENT_ID = os.environ.get('CLIENT_ID', 'my-client-id')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', 'my-super-secret-value')


def lambda_handler(event, context):
    """
    Handles GET and POST requests routed via Amazon API Gateway.

    GET  /orders?id=<order_id>  → Fetch order from DynamoDB
    POST /orders                → Create order in DynamoDB & publish SNS event
    """
    http_method = event.get('httpMethod', 'GET')

    if http_method == 'GET':
        return handle_get(event)
    elif http_method == 'POST':
        return handle_post(event)
    else:
        return _response(405, {'error': 'Method Not Allowed'})


def handle_get(event):
    order_id = (event.get('queryStringParameters') or {}).get('id')
    if not order_id:
        return _response(400, {'error': 'Missing query parameter: id'})

    table = dynamodb.Table(TABLE_NAME)
    result = table.get_item(Key={'order_id': order_id})
    item = result.get('Item')

    if not item:
        return _response(404, {'error': 'Order not found'})

    # Enrich with internal service using raw HTTP + Basic Auth (lock-in!)
    try:
        enriched = requests.post(
            INTERNAL_API_URL,
            json={'order_id': order_id},
            auth=(CLIENT_ID, CLIENT_SECRET),
            timeout=5,
        )
        item['enrichment'] = enriched.json()
    except Exception:
        item['enrichment'] = None

    return _response(200, item)


def handle_post(event):
    body = json.loads(event.get('body') or '{}')
    order_id = body.get('order_id')
    if not order_id:
        return _response(400, {'error': 'Missing field: order_id'})

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        'order_id': order_id,
        'status': body.get('status', 'PENDING'),
        'customer': body.get('customer', 'unknown'),
    })

    # Notify downstream systems via SNS (lock-in!)
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=json.dumps({'event': 'ORDER_CREATED', 'order_id': order_id}),
        Subject='New Order',
    )

    return _response(201, {'message': 'Order created', 'order_id': order_id})


def _response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(body),
    }
