#!/bin/bash
# PulseLink AWS Setup — RDS PostgreSQL (Free Tier)
# Creates a db.t3.micro PostgreSQL instance with 20GB storage.

set -euo pipefail

REGION=$(aws configure get region || echo "us-east-1")
DB_INSTANCE_ID="pulselink-db"
DB_NAME="pulselink"
DB_USER="pulselink"
DB_PASSWORD="pulselink-$(head -c 8 /dev/urandom | xxd -p)"

echo "Creating RDS PostgreSQL instance: $DB_INSTANCE_ID"
echo "  DB Password: $DB_PASSWORD (save this!)"

# Create DB instance (free tier eligible)
aws rds create-db-instance \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version "16" \
    --master-username "$DB_USER" \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage 20 \
    --storage-type gp2 \
    --db-name "$DB_NAME" \
    --no-multi-az \
    --publicly-accessible \
    --backup-retention-period 7 \
    --tags Key=Project,Value=PulseLink \
    --region "$REGION"

echo "Waiting for RDS instance to become available (this takes 5-10 minutes)..."
aws rds wait db-instance-available \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --region "$REGION"

# Get the endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$DB_INSTANCE_ID" \
    --query "DBInstances[0].Endpoint.Address" \
    --output text \
    --region "$REGION")

echo "✓ RDS instance created"
echo "  Endpoint: $RDS_ENDPOINT"
echo "  DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/${DB_NAME}"
export RDS_ENDPOINT
export DB_PASSWORD
