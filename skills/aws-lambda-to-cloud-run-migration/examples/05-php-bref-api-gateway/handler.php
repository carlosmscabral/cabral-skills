<?php
/*
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

require __DIR__ . '/vendor/autoload.php';

use Aws\S3\S3Client;
use Aws\Sns\SnsClient;
use GuzzleHttp\Client;

return function ($event, $context) {
    // 1. AWS SDK Usage (S3 & SNS)
    $s3 = new S3Client([
        'version' => 'latest',
        'region'  => 'us-east-1'
    ]);
    
    $sns = new SnsClient([
        'version' => 'latest',
        'region'  => 'us-east-1'
    ]);

    $bucket = getenv('BUCKET_NAME');
    $topicArn = getenv('SNS_TOPIC_ARN');

    // Example of retrieving payload from API Gateway event
    $body = json_decode($event['body'] ?? '{}', true);
    
    $s3->putObject([
        'Bucket' => $bucket,
        'Key'    => 'logs/' . time() . '.json',
        'Body'   => json_encode($body)
    ]);

    $sns->publish([
        'Message' => 'New payload processed',
        'TopicArn' => $topicArn
    ]);

    // 2. Raw HTTP Usage (Simulating legacy hardcoded API calls)
    try {
        $client = new Client();
        $response = $client->post('https://api.internal.example.com/sync', [
            'auth' => ['legacy_client_id', 'legacy_secret_key'], // Potential secret detection
            'json' => $body
        ]);
        
        $syncStatus = $response->getStatusCode();
    } catch (\Exception $e) {
        $syncStatus = 500;
    }

    return [
        'statusCode' => 200,
        'headers' => ['Content-Type' => 'application/json'],
        'body' => json_encode([
            'message' => 'Processed successfully via Bref',
            'sync' => $syncStatus
        ])
    ];
};
