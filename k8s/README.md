# Kubernetes Local Testing with kind

This guide explains how to run PulseLink on a local Kubernetes cluster using [kind](https://kind.sigs.k8s.io/) (Kubernetes in Docker).

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed and running
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) installed
- [kubectl](https://kubernetes.io/docs/tasks/tools/) installed

## Setup

### 1. Create the kind cluster

```bash
kind create cluster --config kind-config.yaml --name pulselink
```

### 2. Build and load images into the cluster

```bash
# Build the images
docker build -t pulselink-api:latest ../api-service/
docker build -t pulselink-worker:latest ../worker-service/
docker build -t pulselink-frontend:latest ../frontend/

# Load images into kind
kind load docker-image pulselink-api:latest --name pulselink
kind load docker-image pulselink-worker:latest --name pulselink
kind load docker-image pulselink-frontend:latest --name pulselink
```

### 3. Update image references

Before applying manifests, update the image references in the deployment files to use local images:

```yaml
# In api-deployment.yaml, worker-deployment.yaml, frontend-deployment.yaml
# Change:
image: <ECR_ACCOUNT_ID>.dkr.ecr.<REGION>.amazonaws.com/pulselink-api:latest
# To:
image: pulselink-api:latest
imagePullPolicy: Never
```

### 4. Apply all manifests

```bash
kubectl apply -f k8s/
```

### 5. Check status

```bash
# View all pods
kubectl get pods

# View all services
kubectl get svc

# View HPA status
kubectl get hpa

# View pod logs
kubectl logs -l component=api -f
kubectl logs -l component=worker -f

# Describe a pod for troubleshooting
kubectl describe pod <pod-name>
```

### 6. Access the application

- **Frontend**: http://localhost:80
- **API**: http://localhost:8000

## Cleanup

```bash
# Delete the cluster
kind delete cluster --name pulselink
```

## Architecture Notes

- **API Service**: 2 replicas behind a ClusterIP service, with readiness/liveness probes on `/health`
- **Worker Service**: Starts with 1 replica, auto-scales to 6 via HPA based on CPU utilization
- **Frontend**: 2 replicas behind a LoadBalancer service exposing port 80
- **Secrets**: Managed via Kubernetes Secrets (see `services.yaml`)
- **Config**: Shared environment variables via ConfigMap (`configmap.yaml`)

> **Note on Worker HPA**: In production, you'd use [KEDA](https://keda.sh/) to scale based on Kafka consumer lag instead of CPU utilization. This provides more accurate scaling based on actual workload demand.
