#!/bin/bash
# PulseLink AWS Setup — Master Script
# Runs all setup scripts in order to provision AWS infrastructure.
#
# Prerequisites:
#   - AWS CLI installed and configured (aws configure)
#   - Sufficient IAM permissions for S3, RDS, EC2, ECR, IAM
#
# Usage: chmod +x aws/*.sh && ./aws/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "  PulseLink AWS Infrastructure Setup"
echo "============================================"
echo ""

# Verify AWS CLI is configured
if ! aws sts get-caller-identity &>/dev/null; then
    echo "ERROR: AWS CLI is not configured."
    echo "Run 'aws configure' first, then re-run this script."
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region || echo "us-east-1")
echo "AWS Account: $ACCOUNT_ID"
echo "AWS Region:  $REGION"
echo ""

read -p "Continue with setup? (y/N) " confirm
if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

# Run each setup script
echo ">>> Step 1/4: Setting up S3 bucket..."
source "$SCRIPT_DIR/01-s3.sh"
echo ""

echo ">>> Step 2/4: Setting up RDS PostgreSQL..."
source "$SCRIPT_DIR/02-rds.sh"
echo ""

echo ">>> Step 3/4: Setting up EC2 instance..."
source "$SCRIPT_DIR/03-ec2.sh"
echo ""

echo ">>> Step 4/4: Setting up ECR repositories..."
source "$SCRIPT_DIR/04-ecr.sh"
echo ""

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Copy these values into your GitHub Secrets:"
echo "  AWS_REGION=$REGION"
echo "  ECR_REGISTRY=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
echo "  EC2_HOST=$EC2_PUBLIC_IP"
echo "  AWS_BUCKET_NAME=$BUCKET_NAME"
echo "  DATABASE_URL=postgresql://pulselink:<password>@$RDS_ENDPOINT/pulselink"
echo ""
echo "Next steps:"
echo "  1. Set a strong SECRET_KEY in GitHub Secrets"
echo "  2. Add your EC2 SSH private key as EC2_SSH_KEY secret"
echo "  3. Push to main branch to trigger the first deploy"
