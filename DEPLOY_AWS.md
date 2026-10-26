# VisionCheck AI - AWS Deployment Guide

This guide describes the recommended meaningful AWS component for the final competition entry.

## Target architecture

Desktop/Web Client -> API Gateway -> AWS Lambda (OpenCV 5) -> JSON result

Optional supporting services:
- Amazon S3: input image and result archive
- Amazon CloudWatch: logs, invocation count, errors, latency
- Amazon ECR: Lambda container image when packaging OpenCV 5 as a container

## Why use a Lambda container image

OpenCV is a native dependency. A Lambda container image makes the runtime reproducible and allows the exact OpenCV 5 build to travel with the function.

## Deployment outline

1. Install Docker and AWS CLI v2.
2. Configure AWS credentials with least-privilege access.
3. Create an ECR repository named `visioncheck-ai`.
4. Build the image from `aws_lambda/Dockerfile`.
5. Push the image to ECR.
6. Create a Lambda function from that container image.
7. Set memory to at least 1024 MB initially and choose a practical timeout such as 30 seconds.
8. Create an API Gateway HTTP/REST endpoint that invokes the Lambda function.
9. Test using a small JPEG encoded as base64 JSON or an S3 object key.
10. Enable CloudWatch logs.
11. Record the endpoint, region, runtime configuration, memory, and measured latency for the technical report.

## Required evidence to capture before submission

- AWS Region
- Lambda function name
- deployed container image digest/tag
- OpenCV version printed by the Lambda function
- API endpoint or live demonstration instructions
- 5-10 measured request latencies
- one successful response JSON
- one handled failure case
- CloudWatch screenshot/log excerpt

## Security notes

- Do not embed AWS access keys in source code.
- Use IAM roles for Lambda.
- Limit S3 bucket access.
- If the endpoint is public, apply request-size limits and rate limiting.
- Do not store user images unless necessary; document retention behavior.
