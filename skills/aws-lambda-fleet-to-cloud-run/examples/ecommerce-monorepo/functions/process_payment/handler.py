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
import requests  # raw HTTP call to external payment gateway

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
TABLE_NAME = os.environ['ORDERS_TABLE']
PAYMENT_GATEWAY_URL = os.environ['PAYMENT_GATEWAY_URL']
PAYMENT_API_KEY = os.environ['PAYMENT_API_KEY']


def handler(event, context):
    """
    Triggered by SNS 'order.created' event.
    Calls an external payment gateway via raw HTTP using a hardcoded API key.
    Updates order status in DynamoDB.
    """
    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])
        order = sns_message.get('order', {})
        order_id = order.get('orderId')

        # Raw HTTP call to external payment gateway — uses hardcoded API key
        response = requests.post(
            PAYMENT_GATEWAY_URL,
            headers={
                'Authorization': f'Bearer {PAYMENT_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'amount': order.get('totalAmount'),
                'currency': order.get('currency', 'USD'),
                'metadata': {'orderId': order_id},
            },
            timeout=30,
        )

        if response.status_code == 200:
            new_status = 'PAYMENT_CONFIRMED'
        else:
            new_status = 'PAYMENT_FAILED'

        # Update order status in DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'orderId': order_id},
            UpdateExpression='SET #s = :status',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':status': new_status},
        )

    return {'statusCode': 200}
