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
import io
import csv
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
s3 = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))

TABLE_NAME = os.environ['ORDERS_TABLE']
REPORTS_BUCKET = 'ecommerce-reports'


def handler(event, context):
    """
    EventBridge cron trigger (02:00 UTC nightly).
    Scans all orders from DynamoDB, generates a CSV reconciliation report,
    and uploads it to S3.
    """
    # Full table scan — acceptable for daily batch job
    table = dynamodb.Table(TABLE_NAME)
    items = []
    response = table.scan()
    items.extend(response.get('Items', []))
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    # Build CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['orderId', 'customerId', 'status', 'totalAmount', 'currency'])
    writer.writeheader()
    for item in items:
        writer.writerow({
            'orderId': item.get('orderId', ''),
            'customerId': item.get('customerId', ''),
            'status': item.get('status', ''),
            'totalAmount': item.get('totalAmount', 0),
            'currency': item.get('currency', 'USD'),
        })

    # Upload to S3
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    key = f'reconciliation/{date_str}/orders.csv'
    s3.put_object(
        Bucket=REPORTS_BUCKET,
        Key=key,
        Body=output.getvalue().encode('utf-8'),
        ContentType='text/csv',
    )

    print(f'Reconciliation report written: s3://{REPORTS_BUCKET}/{key} ({len(items)} orders)')
    return {'statusCode': 200, 'report_key': key, 'total_orders': len(items)}
