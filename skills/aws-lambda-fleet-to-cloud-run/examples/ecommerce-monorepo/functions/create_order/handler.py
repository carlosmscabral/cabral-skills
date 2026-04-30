# Copyright 2026 Google LLC
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

import json
import os
import boto3
import uuid

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
sns = boto3.client('sns', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

TABLE_NAME = os.environ['ORDERS_TABLE']
TOPIC_ARN = os.environ['ORDER_EVENTS_TOPIC']


def handler(event, context):
    """
    POST /orders
    Creates a new order in DynamoDB and publishes an 'order.created' event to SNS.
    """
    try:
        body = json.loads(event.get('body', '{}'))
        order_id = str(uuid.uuid4())
        order = {
            'orderId': order_id,
            'customerId': body.get('customerId'),
            'items': body.get('items', []),
            'totalAmount': body.get('totalAmount', 0),
            'status': 'PENDING',
            'currency': body.get('currency', 'USD'),
        }

        # Write to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item=order)

        # Publish order created event to SNS
        sns.publish(
            TopicArn=TOPIC_ARN,
            Message=json.dumps({'eventType': 'order.created', 'order': order}),
            MessageAttributes={
                'eventType': {'DataType': 'String', 'StringValue': 'order.created'}
            }
        )

        return {
            'statusCode': 201,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'orderId': order_id, 'status': 'PENDING'}),
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
