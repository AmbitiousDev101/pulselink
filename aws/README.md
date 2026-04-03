# AWS Deployment Guide for PulseLink

Step-by-step instructions to deploy PulseLink on AWS free-tier infrastructure.

## Prerequisites

1. **AWS Account** — [Create one here](https://aws.amazon.com/free/) if you don't have one
2. **AWS CLI** — [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. **Configure AWS CLI**:
   ```bash
   aws configure
   # Enter your Access Key ID, Secret Access Key, Region (e.g., us-east-1)
   ```

## Setup

### 1. Make scripts executable and run setup

```bash
chmod +x aws/*.sh
./aws/setup.sh
```

This will create:
- **S3 Bucket** — stores URL screenshots (public read)
- **RDS PostgreSQL** — free tier db.t3.micro, 20GB storage
- **EC2 Instance** — free tier t2.micro with Docker pre-installed
- **ECR Repositories** — Docker image registry for all services

### 2. Copy outputs to GitHub Secrets

After setup completes, you'll see output values. Add these as GitHub repository secrets:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `ECR_REGISTRY` | ECR registry URL (from setup output) |
| `EC2_HOST` | EC2 public IP (from setup output) |
| `EC2_SSH_KEY` | Contents of `pulselink-key.pem` |
| `DATABASE_URL` | RDS connection string (from setup output) |
| `SECRET_KEY` | A strong random string for JWT signing |
| `AWS_BUCKET_NAME` | S3 bucket name (from setup output) |

### 3. Trigger first deploy

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

The GitHub Actions pipeline will:
1. Run tests
2. Build Docker images
3. Push to ECR
4. SSH into EC2 and deploy

### 4. Verify deployment

```bash
# SSH into the EC2 instance
ssh -i pulselink-key.pem ec2-user@<EC2_HOST>

# Check running containers
docker compose ps

# Check API health
curl http://<EC2_HOST>:8000/health

# Open frontend
open http://<EC2_HOST>:3000
```

## Teardown

To delete **all** AWS resources and avoid any charges:

```bash
./aws/teardown.sh
```

This will prompt for confirmation before deleting anything.

## Cost Estimates (Free Tier)

| Service | Free Tier Limit | Monthly Cost (after free tier) |
|---|---|---|
| EC2 t2.micro | 750 hrs/month (12 months) | ~$8.50/month |
| RDS db.t3.micro | 750 hrs/month (12 months) | ~$12/month |
| S3 | 5GB storage | ~$0.02/GB |
| ECR | 500MB storage | ~$0.10/GB |

**Total during free tier: $0/month**

> ⚠ Always run `./aws/teardown.sh` when you're done to avoid unexpected charges.
