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

// Example 2: Node.js Lambda with AWS SDK v3 (API Gateway trigger)
//
// This is a realistic example of a Lambda that:
// - Is triggered by API Gateway (HTTP API)
// - Uses @aws-sdk/client-s3 to store and retrieve objects
// - Uses @aws-sdk/client-sqs to enqueue processing tasks
// - Exports a standard Lambda handler (exports.handler)
//
// This example represents a Node.js "storage + queue" pattern — a common
// Lambda shape that maps naturally to Cloud Storage + Cloud Tasks on GCP.

const { S3Client, PutObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { SQSClient, SendMessageCommand } = require('@aws-sdk/client-sqs');

// AWS SDK v3 clients — initialized at module level
const s3 = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });
const sqs = new SQSClient({ region: process.env.AWS_REGION || 'us-east-1' });

const BUCKET_NAME = process.env.DOCUMENTS_BUCKET || 'my-documents-bucket';
const SQS_QUEUE_URL = process.env.PROCESSING_QUEUE_URL || 'https://sqs.us-east-1.amazonaws.com/123456789012/processing-queue';

exports.handler = async (event, context) => {
  const method = event.requestContext?.http?.method || event.httpMethod || 'GET';
  const path = event.rawPath || event.path || '/';

  try {
    if (method === 'PUT' && path.startsWith('/documents/')) {
      return await uploadDocument(event);
    } else if (method === 'GET' && path.startsWith('/documents/')) {
      return await getDocument(event);
    } else {
      return response(404, { error: 'Route not found' });
    }
  } catch (err) {
    console.error('Unhandled error:', err);
    return response(500, { error: 'Internal server error' });
  }
};

async function uploadDocument(event) {
  const docId = (event.pathParameters || {}).id || Date.now().toString();
  const body = event.body ? Buffer.from(event.body, event.isBase64Encoded ? 'base64' : 'utf-8') : Buffer.from('');

  // Store document in S3 (lock-in!)
  await s3.send(new PutObjectCommand({
    Bucket: BUCKET_NAME,
    Key: `documents/${docId}`,
    Body: body,
    ContentType: event.headers?.['content-type'] || 'application/octet-stream',
  }));

  // Enqueue processing task in SQS (lock-in!)
  await sqs.send(new SendMessageCommand({
    QueueUrl: SQS_QUEUE_URL,
    MessageBody: JSON.stringify({ docId, action: 'PROCESS' }),
    DelaySeconds: 0,
  }));

  return response(202, { message: 'Document uploaded and queued for processing', docId });
}

async function getDocument(event) {
  const docId = (event.pathParameters || {}).id;
  if (!docId) {
    return response(400, { error: 'Missing document ID' });
  }

  try {
    const result = await s3.send(new GetObjectCommand({
      Bucket: BUCKET_NAME,
      Key: `documents/${docId}`,
    }));

    const chunks = [];
    for await (const chunk of result.Body) {
      chunks.push(chunk);
    }

    return {
      statusCode: 200,
      headers: {
        'Content-Type': result.ContentType || 'application/octet-stream',
      },
      body: Buffer.concat(chunks).toString('base64'),
      isBase64Encoded: true,
    };
  } catch (err) {
    if (err.name === 'NoSuchKey') {
      return response(404, { error: 'Document not found' });
    }
    throw err;
  }
}

function response(statusCode, body) {
  return {
    statusCode,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  };
}
