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

ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
SENDER_EMAIL = 'orders@example.com'


def handler(event, context):
    """
    Triggered by SNS 'order.created' event.
    Sends an order confirmation email to the customer via AWS SES.
    """
    for record in event.get('Records', []):
        sns_message = json.loads(record['Sns']['Message'])
        order = sns_message.get('order', {})
        customer_id = order.get('customerId', 'customer')
        order_id = order.get('orderId', 'unknown')
        total = order.get('totalAmount', 0)
        currency = order.get('currency', 'USD')

        recipient = f'{customer_id}@example.com'

        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': f'Order Confirmation — {order_id}'},
                'Body': {
                    'Text': {
                        'Data': (
                            f'Thank you for your order!\n\n'
                            f'Order ID: {order_id}\n'
                            f'Total: {total} {currency}\n\n'
                            f'We will notify you when your order ships.'
                        )
                    }
                },
            },
        )

    return {'statusCode': 200}
