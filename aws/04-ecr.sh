#!/bin/bash
# PulseLink AWS Setup — ECR Repositories
# Creates ECR repositories for API and Worker Docker images.

set -euo pipefail

REGION=$(aws configure get region || echo "us-east-1")

echo "Creating ECR repositories..."

# Create api repository
API_REPO_URI=$(aws ecr create-repository \
    --repository-name pulselink-api \
    --image-scanning-configuration scanOnPush=true \
    --query "repository.repositoryUri" \
    --output text \
    --region "$REGION" 2>/dev/null || \
    aws ecr describe-repositories \
        --repository-names pulselink-api \
        --query "repositories[0].repositoryUri" \
        --output text \
        --region "$REGION")

echo "  ✓ pulselink-api: $API_REPO_URI"

# Create worker repository
WORKER_REPO_URI=$(aws ecr create-repository \
    --repository-name pulselink-worker \
    --image-scanning-configuration scanOnPush=true \
    --query "repository.repositoryUri" \
    --output text \
    --region "$REGION" 2>/dev/null || \
    aws ecr describe-repositories \
        --repository-names pulselink-worker \
        --query "repositories[0].repositoryUri" \
        --output text \
        --region "$REGION")

echo "  ✓ pulselink-worker: $WORKER_REPO_URI"

# Create frontend repository
FRONTEND_REPO_URI=$(aws ecr create-repository \
    --repository-name pulselink-frontend \
    --image-scanning-configuration scanOnPush=true \
    --query "repository.repositoryUri" \
    --output text \
    --region "$REGION" 2>/dev/null || \
    aws ecr describe-repositories \
        --repository-names pulselink-frontend \
        --query "repositories[0].repositoryUri" \
        --output text \
        --region "$REGION")

echo "  ✓ pulselink-frontend: $FRONTEND_REPO_URI"

# Set lifecycle policy (keep last 10 images to save space)
LIFECYCLE_POLICY='{
    "rules": [{
        "rulePriority": 1,
        "description": "Keep last 10 images",
        "selection": {
            "tagStatus": "any",
            "countType": "imageCountMoreThan",
            "countNumber": 10
        },
        "action": { "type": "expire" }
    }]
}'

for REPO in pulselink-api pulselink-worker pulselink-frontend; do
    aws ecr put-lifecycle-policy \
        --repository-name "$REPO" \
        --lifecycle-policy-text "$LIFECYCLE_POLICY" \
        --region "$REGION" >/dev/null
done

echo "✓ ECR repositories created with lifecycle policies"
echo "  ECR Registry: $(echo $API_REPO_URI | cut -d'/' -f1)"
