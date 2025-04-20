#!/bin/bash

# Replace these with your values
S3_BUCKET="your-s3-bucket-name"
CLOUDFRONT_DISTRIBUTION_ID="your-cloudfront-distribution-id"

# Upload files to S3
echo "Uploading files to S3..."
aws s3 sync . s3://$S3_BUCKET \
    --exclude "*.sh" \
    --exclude "*.md" \
    --exclude ".git/*" \
    --exclude "node_modules/*" \
    --cache-control "max-age=3600"

# Invalidate CloudFront cache
echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
    --paths "/*"

echo "Deployment complete!" 