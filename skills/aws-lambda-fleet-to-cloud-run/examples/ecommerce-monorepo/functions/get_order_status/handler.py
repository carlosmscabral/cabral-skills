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
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
TABLE_NAME = os.environ['ORDERS_TABLE']


def handler(event, context):
    """
    GET /orders/{orderId}
    Returns the current status and details of an order from DynamoDB.
    """
    try:
        order_id = event.get('pathParameters', {}).get('orderId')
        if not order_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'orderId is required'})}

        table = dynamodb.Table(TABLE_NAME)
        result = table.get_item(Key={'orderId': order_id})
        item = result.get('Item')

        if not item:
            return {'statusCode': 404, 'body': json.dumps({'error': 'Order not found'})}

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(item),
        }
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({'error': str(e)})}
