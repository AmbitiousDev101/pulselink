#!/bin/bash
# PulseLink AWS Setup — S3 Bucket for Screenshots
# Creates an S3 bucket with public read access and CORS enabled.

set -euo pipefail

SUFFIX=$(head -c 4 /dev/urandom | xxd -p)
BUCKET_NAME="pulselink-screenshots-${SUFFIX}"
REGION=$(aws configure get region || echo "us-east-1")

echo "Creating S3 bucket: $BUCKET_NAME"

# Create bucket
if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION"
else
    aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION"
fi

# Disable block public access (needed for public-read objects)
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Set bucket policy for public read on screenshots/
aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy "{
        \"Version\": \"2012-10-17\",
        \"Statement\": [
            {
                \"Sid\": \"PublicReadScreenshots\",
                \"Effect\": \"Allow\",
                \"Principal\": \"*\",
                \"Action\": \"s3:GetObject\",
                \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}/screenshots/*\"
            }
        ]
    }"

# Enable CORS
aws s3api put-bucket-cors \
    --bucket "$BUCKET_NAME" \
    --cors-configuration '{
        "CORSRules": [
            {
                "AllowedOrigins": ["*"],
                "AllowedMethods": ["GET"],
                "AllowedHeaders": ["*"],
                "MaxAgeSeconds": 3600
            }
        ]
    }'

echo "✓ S3 bucket created: $BUCKET_NAME"
echo "  URL: https://${BUCKET_NAME}.s3.${REGION}.amazonaws.com"
export BUCKET_NAME
