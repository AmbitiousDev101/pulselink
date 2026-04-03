#!/bin/bash
# PulseLink AWS Setup — EC2 Instance (Free Tier)
# Creates a t2.micro EC2 with Docker, Docker Compose, and AWS CLI.

set -euo pipefail

REGION=$(aws configure get region || echo "us-east-1")
KEY_NAME="pulselink-key"
SG_NAME="pulselink-sg"
INSTANCE_NAME="pulselink-server"

echo "Setting up EC2 instance..."

# Get default VPC ID
VPC_ID=$(aws ec2 describe-vpcs \
    --filters Name=isDefault,Values=true \
    --query "Vpcs[0].VpcId" \
    --output text \
    --region "$REGION")
echo "  Default VPC: $VPC_ID"

# Create security group
echo "  Creating security group: $SG_NAME"
SG_ID=$(aws ec2 create-security-group \
    --group-name "$SG_NAME" \
    --description "PulseLink security group" \
    --vpc-id "$VPC_ID" \
    --query "GroupId" \
    --output text \
    --region "$REGION" 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters Name=group-name,Values="$SG_NAME" \
        --query "SecurityGroups[0].GroupId" \
        --output text \
        --region "$REGION")

# Add inbound rules
for PORT in 22 80 443 8000 3000; do
    aws ec2 authorize-security-group-ingress \
        --group-id "$SG_ID" \
        --protocol tcp \
        --port "$PORT" \
        --cidr 0.0.0.0/0 \
        --region "$REGION" 2>/dev/null || true
done
echo "  Security group: $SG_ID (ports 22, 80, 443, 8000, 3000)"

# Create key pair (if not exists)
if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    echo "  Creating key pair: $KEY_NAME"
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query "KeyMaterial" \
        --output text \
        --region "$REGION" > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "  ⚠ Private key saved to: ${KEY_NAME}.pem"
    echo "  ⚠ Add this key content as EC2_SSH_KEY GitHub secret"
else
    echo "  Key pair '$KEY_NAME' already exists"
fi

# Get latest Amazon Linux 2023 AMI
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters \
        "Name=name,Values=al2023-ami-2023*-x86_64" \
        "Name=state,Values=available" \
    --query "Images | sort_by(@, &CreationDate) | [-1].ImageId" \
    --output text \
    --region "$REGION")
echo "  AMI: $AMI_ID"

# User data script — installs Docker, Docker Compose, AWS CLI
USER_DATA=$(cat <<'USERDATA'
#!/bin/bash
set -e

# Install Docker
dnf update -y
dnf install -y docker git
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

# Install Docker Compose
DOCKER_COMPOSE_VERSION="v2.27.0"
curl -SL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
    -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Docker compose plugin
mkdir -p /usr/local/lib/docker/cli-plugins
cp /usr/local/bin/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose

# Create app directory
mkdir -p /home/ec2-user/pulselink
chown ec2-user:ec2-user /home/ec2-user/pulselink

echo "EC2 setup complete!"
USERDATA
)

# Create IAM role for EC2
ROLE_NAME="pulselink-ec2-role"
INSTANCE_PROFILE="pulselink-ec2-profile"

# Create role (if not exists)
aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || true

# Attach policies
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess 2>/dev/null || true

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly 2>/dev/null || true

aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess 2>/dev/null || true

# Create instance profile (if not exists)
aws iam create-instance-profile \
    --instance-profile-name "$INSTANCE_PROFILE" 2>/dev/null || true

aws iam add-role-to-instance-profile \
    --instance-profile-name "$INSTANCE_PROFILE" \
    --role-name "$ROLE_NAME" 2>/dev/null || true

# Wait for instance profile propagation
sleep 10

# Launch EC2 instance
echo "  Launching EC2 instance (t2.micro)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type t2.micro \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --iam-instance-profile Name="$INSTANCE_PROFILE" \
    --user-data "$USER_DATA" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Project,Value=PulseLink}]" \
    --query "Instances[0].InstanceId" \
    --output text \
    --region "$REGION")

echo "  Instance ID: $INSTANCE_ID"
echo "  Waiting for instance to be running..."

aws ec2 wait instance-running \
    --instance-ids "$INSTANCE_ID" \
    --region "$REGION"

# Get public IP
EC2_PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids "$INSTANCE_ID" \
    --query "Reservations[0].Instances[0].PublicIpAddress" \
    --output text \
    --region "$REGION")

echo "✓ EC2 instance launched"
echo "  Public IP: $EC2_PUBLIC_IP"
echo "  SSH: ssh -i ${KEY_NAME}.pem ec2-user@${EC2_PUBLIC_IP}"
export EC2_PUBLIC_IP
