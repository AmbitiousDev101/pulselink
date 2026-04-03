#!/bin/bash
# PulseLink AWS Teardown
# Deletes ALL AWS resources created by the setup scripts.
# This will permanently destroy data — use with caution.

set -euo pipefail

REGION=$(aws configure get region || echo "us-east-1")

echo "============================================"
echo "  PulseLink AWS Teardown"
echo "============================================"
echo ""
echo "⚠ WARNING: This will permanently delete:"
echo "  - S3 bucket and all screenshots"
echo "  - RDS database and all data"
echo "  - EC2 instance"
echo "  - ECR repositories and all images"
echo "  - Security groups, key pairs, IAM roles"
echo ""

read -p "Are you sure? Type 'DELETE' to confirm: " confirm
if [[ "$confirm" != "DELETE" ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

# 1. Delete EC2 instance
echo ">>> Terminating EC2 instances..."
INSTANCE_IDS=$(aws ec2 describe-instances \
    --filters "Name=tag:Project,Values=PulseLink" "Name=instance-state-name,Values=running,stopped" \
    --query "Reservations[].Instances[].InstanceId" \
    --output text \
    --region "$REGION" 2>/dev/null || echo "")

if [[ -n "$INSTANCE_IDS" ]]; then
    aws ec2 terminate-instances --instance-ids $INSTANCE_IDS --region "$REGION" >/dev/null
    echo "  Waiting for termination..."
    aws ec2 wait instance-terminated --instance-ids $INSTANCE_IDS --region "$REGION"
    echo "  ✓ EC2 instances terminated"
else
    echo "  No instances found"
fi

# 2. Delete RDS instance
echo ">>> Deleting RDS instance..."
if aws rds describe-db-instances --db-instance-identifier pulselink-db --region "$REGION" &>/dev/null; then
    aws rds delete-db-instance \
        --db-instance-identifier pulselink-db \
        --skip-final-snapshot \
        --region "$REGION" >/dev/null
    echo "  Waiting for deletion (this takes a few minutes)..."
    aws rds wait db-instance-deleted --db-instance-identifier pulselink-db --region "$REGION" 2>/dev/null || true
    echo "  ✓ RDS instance deleted"
else
    echo "  No RDS instance found"
fi

# 3. Delete S3 buckets
echo ">>> Deleting S3 buckets..."
BUCKETS=$(aws s3api list-buckets \
    --query "Buckets[?starts_with(Name, 'pulselink-screenshots')].Name" \
    --output text 2>/dev/null || echo "")

for BUCKET in $BUCKETS; do
    echo "  Emptying $BUCKET..."
    aws s3 rm "s3://$BUCKET" --recursive >/dev/null 2>&1 || true
    aws s3api delete-bucket --bucket "$BUCKET" --region "$REGION" >/dev/null
    echo "  ✓ Deleted $BUCKET"
done

if [[ -z "$BUCKETS" ]]; then
    echo "  No S3 buckets found"
fi

# 4. Delete ECR repositories
echo ">>> Deleting ECR repositories..."
for REPO in pulselink-api pulselink-worker pulselink-frontend; do
    if aws ecr describe-repositories --repository-names "$REPO" --region "$REGION" &>/dev/null; then
        aws ecr delete-repository --repository-name "$REPO" --force --region "$REGION" >/dev/null
        echo "  ✓ Deleted $REPO"
    fi
done

# 5. Delete security group
echo ">>> Deleting security group..."
SG_ID=$(aws ec2 describe-security-groups \
    --filters Name=group-name,Values=pulselink-sg \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region "$REGION" 2>/dev/null || echo "None")

if [[ "$SG_ID" != "None" && -n "$SG_ID" ]]; then
    aws ec2 delete-security-group --group-id "$SG_ID" --region "$REGION" >/dev/null 2>&1 || true
    echo "  ✓ Deleted security group"
else
    echo "  No security group found"
fi

# 6. Delete key pair
echo ">>> Deleting key pair..."
aws ec2 delete-key-pair --key-name pulselink-key --region "$REGION" 2>/dev/null || true
rm -f pulselink-key.pem 2>/dev/null || true
echo "  ✓ Key pair deleted"

# 7. Delete IAM role and instance profile
echo ">>> Cleaning up IAM..."
aws iam remove-role-from-instance-profile \
    --instance-profile-name pulselink-ec2-profile \
    --role-name pulselink-ec2-role 2>/dev/null || true

aws iam delete-instance-profile \
    --instance-profile-name pulselink-ec2-profile 2>/dev/null || true

for POLICY in AmazonS3FullAccess AmazonEC2ContainerRegistryReadOnly CloudWatchLogsFullAccess; do
    aws iam detach-role-policy \
        --role-name pulselink-ec2-role \
        --policy-arn "arn:aws:iam::aws:policy/$POLICY" 2>/dev/null || true
done

aws iam delete-role --role-name pulselink-ec2-role 2>/dev/null || true
echo "  ✓ IAM resources deleted"

echo ""
echo "============================================"
echo "  Teardown Complete!"
echo "============================================"
echo "All PulseLink AWS resources have been deleted."
