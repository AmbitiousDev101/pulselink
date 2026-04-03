# PulseLink — Real-Time URL Analysis Platform

PulseLink is a distributed, real-time URL analysis platform built to demonstrate production-grade systems design. Paste any URL and get an instant, comprehensive analysis — page title, response time, SSL certificate status, redirect chain, detected tech stack, safety score, and a live screenshot. Every analysis appears on a public live feed that updates in real time via WebSockets for all connected users.

Under the hood, PulseLink uses an async event-driven architecture: the API gateway publishes submissions to Kafka (Redpanda) for non-blocking ingestion, a worker service consumes and analyzes URLs, and results fan out to all connected clients through WebSocket broadcast. The result is an API that responds in under 50ms regardless of how long the actual analysis takes.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PULSELINK                                  │
│                                                                     │
│  ┌────────┐     ┌──────────────┐     ┌──────────┐                  │
│  │ Next.js│────▶│  FastAPI API  │────▶│ Redpanda │                  │
│  │Frontend│◀────│   Gateway    │     │  (Kafka) │                  │
│  └────────┘  WS └──────┬───────┘     └────┬─────┘                  │
│     :3000        :8000  │                  │                        │
│                         │    ┌─────────────┘                        │
│                         │    │                                      │
│                    ┌────▼────▼───┐                                  │
│                    │   Worker    │                                  │
│                    │  Service   │                                  │
│                    └──┬────┬────┘                                  │
│                       │    │                                        │
│              ┌────────▼┐  ┌▼────────┐                              │
│              │PostgreSQL│  │   S3    │                              │
│              │  :5432   │  │  (AWS)  │                              │
│              └─────────┘  └─────────┘                              │
│                                                                     │
│  ┌───────┐                                                         │
│  │ Redis │  Cache + Rate Limiting                                  │
│  │ :6379 │                                                         │
│  └───────┘                                                         │
└─────────────────────────────────────────────────────────────────────┘

Data Flow:
  User submits URL → API checks Redis cache → cache miss →
  publish to Kafka "url.submitted" → return 202 + job_id instantly →
  Worker consumes → fetches URL, checks SSL, detects tech, screenshots →
  writes result to PostgreSQL → publishes to Kafka "url.analyzed" →
  API WebSocket consumer broadcasts to all connected clients →
  Frontend live feed updates in real time
```

## Tech Stack

| Technology | Role | Why |
|---|---|---|
| **Python + FastAPI** | API Gateway | Async-first, sub-50ms responses, auto-generated OpenAPI docs |
| **Next.js 15 + TypeScript** | Frontend | SSR, App Router, real-time WebSocket integration |
| **Redpanda (Kafka)** | Message Queue | Decouples ingestion from processing — submissions queue without failing |
| **Redis** | Cache + Rate Limiter | SHA-256 URL hash with 1hr TTL, sliding window rate limiting |
| **PostgreSQL** | Primary Database | JSONB results, indexed lookups, full analysis history |
| **Playwright** | Screenshot Engine | Headless Chromium captures live page screenshots |
| **Docker + Compose** | Local Development | Full stack in one `docker compose up` command |
| **Kubernetes (kind)** | Container Orchestration | Real K8s manifests with HPA, tested locally with kind |
| **GitHub Actions** | CI/CD | Auto test → build → push to ECR → deploy to EC2 on every push |
| **AWS (EC2 + S3 + RDS)** | Production Hosting | Free-tier deployment with bash setup scripts |

## Local Development

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Node.js 20+](https://nodejs.org/) (for frontend development)

### Quick Start

```bash
# Clone the repo
git clone https://github.com/your-username/pulselink.git
cd pulselink

# Start everything
docker compose up -d

# That's it! Open:
#   Frontend: http://localhost:3000
#   API Docs: http://localhost:8000/docs
#   Health:   http://localhost:8000/health
```

### Development Mode (hot reload)

```bash
# Start infrastructure only
docker compose up -d redpanda redis postgres

# Run API service locally
cd api-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Run worker locally (in another terminal)
cd worker-service
pip install -r requirements.txt
python main.py

# Run frontend locally (in another terminal)
cd frontend
npm install
npm run dev
```

## Kubernetes Local Testing

```bash
# Create a kind cluster
kind create cluster --config k8s/kind-config.yaml --name pulselink

# Build and load images
docker build -t pulselink-api:latest api-service/
docker build -t pulselink-worker:latest worker-service/
docker build -t pulselink-frontend:latest frontend/
kind load docker-image pulselink-api:latest pulselink-worker:latest pulselink-frontend:latest --name pulselink

# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get hpa
```

See [k8s/README.md](k8s/README.md) for detailed instructions.

## AWS Deployment

PulseLink includes bash scripts to provision free-tier AWS infrastructure:

```bash
chmod +x aws/*.sh
./aws/setup.sh
```

See [aws/README.md](aws/README.md) for the full deployment guide.

## How to Demo It

1. **Start the stack**: `docker compose up -d`
2. **Open the frontend**: http://localhost:3000
3. **Click "Simulate Live Traffic"** — the live feed populates with realistic analyses
4. **Paste a real URL** (e.g., `https://github.com`) — watch it appear in the feed when done
5. **Click any result** — see the full analysis: status code, response time, SSL, tech stack, redirects
6. **Open a second browser tab** — both tabs update simultaneously via WebSocket
7. **Show the API docs** at http://localhost:8000/docs — full OpenAPI spec
8. **Show the architecture**: `docker compose ps` — 5 services, all healthy

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/urls` | Submit a URL for analysis (returns 202 + job_id) |
| `GET` | `/api/v1/urls/{id}` | Get analysis result by ID |
| `GET` | `/api/v1/urls` | Paginated list of completed analyses |
| `POST` | `/api/v1/simulate` | Generate 5 fake analyses for demo |
| `WS` | `/ws/feed` | WebSocket live feed of all analyses |
| `GET` | `/health` | Service health check |

## GitHub Secrets Required

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `ECR_REGISTRY` | ECR registry URL |
| `EC2_HOST` | EC2 instance public IP |
| `EC2_SSH_KEY` | EC2 SSH private key (PEM) |
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `AWS_BUCKET_NAME` | S3 screenshots bucket name |


## Project Structure

```
pulselink/
├── api-service/          # FastAPI gateway
│   ├── routes/           # URL and health endpoints
│   ├── services/         # Cache, Kafka, WebSocket managers
│   ├── main.py           # App entry point
│   ├── database.py       # asyncpg pool + migrations
│   ├── models.py         # Pydantic schemas
│   └── Dockerfile
├── worker-service/       # URL analysis worker
│   ├── analyzer.py       # Core analysis logic
│   ├── kafka_consumer.py # Kafka consumer loop
│   ├── s3_upload.py      # Screenshot upload
│   └── Dockerfile
├── frontend/             # Next.js 15 dashboard
│   ├── app/              # Pages (App Router)
│   ├── components/       # UrlForm, ResultCard, LiveFeed
│   └── lib/              # API client, WebSocket manager
├── k8s/                  # Kubernetes manifests
├── aws/                  # AWS setup scripts
├── .github/workflows/    # CI/CD pipelines
├── docker-compose.yml    # Full local stack
└── .env.example          # Environment variables reference
```
