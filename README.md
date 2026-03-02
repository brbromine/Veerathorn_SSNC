# SS&C Technical Exercise — Hello World on AWS ECS Fargate

> Deployed a containerised "Hello World" FastAPI web application on AWS ECS Fargate using Terraform, with a full CI/CD pipeline, health checks, and CloudWatch observability.

## Live Demo

| | URL |
|---|---|
| **Hello World UI** | http://ssnc-hello-world-alb-1675712513.us-east-1.elb.amazonaws.com |
| **Health Check** | http://ssnc-hello-world-alb-1675712513.us-east-1.elb.amazonaws.com/health |
| **Swagger Docs** | http://ssnc-hello-world-alb-1675712513.us-east-1.elb.amazonaws.com/docs |

---

## Architecture

![SS&C Hello World Architecture](evidence/SSNC_Architecture_Desgin.drawio.png)

> Full architecture diagram showing VPC, ALB, ECS Fargate, ECR, IAM, and CloudWatch across 2 Availability Zones in us-east-1.

### Architecture Notes

- **ALB** is a single resource — AWS automatically places an ALB node in each AZ's subnet. It is not two separate load balancers.
- **ECS Cluster** runs `desired_count = 1` (single task for cost reasons). The task can land in either AZ. Set to `2` for true zero-downtime HA across both AZs.
- **Security groups** are attached to the services (ALB and ECS tasks), not the subnets themselves.
- **Route Table** — one shared public route table (`0.0.0.0/0 → IGW`) is associated to both subnets. Traffic from the internet enters via the IGW, gets routed to the subnet, then hits the ALB.
- **GitHub Actions** never enters the VPC — it talks directly to AWS APIs (ECR, ECS, Terraform) over HTTPS using IAM credentials.

### AWS Services Used

| Service | Purpose |
|---|---|
| **ECS Fargate** | Serverless container runtime — no EC2 to manage |
| **ECR** | Private Docker image registry |
| **ALB** | Internet-facing load balancer, spans 2 AZs, routes HTTP traffic |
| **VPC + Subnets** | Isolated network, 2 public subnets across 2 AZs (required by ALB) |
| **IGW** | Internet Gateway — entry point for all inbound internet traffic |
| **Route Table** | Single public route table (`0.0.0.0/0 → IGW`) shared by both subnets |
| **CloudWatch Logs** | Container stdout/stderr logs (`/ecs/ssnc-hello-world`, 7-day retention) |
| **CloudWatch Alarms** | CPU > 80% and Memory > 80% threshold alerts |
| **Container Insights** | ECS cluster-level metrics dashboard |
| **IAM** | Least-privilege execution role — ECR pull + CloudWatch write only |
| **Terraform Cloud** | Remote state store for Terraform (local execution mode) |

---

## Project Structure

```
SSNC_Technical_Interview/
├── app/
│   ├── main.py              # FastAPI app — /, /echo, /health endpoints
│   ├── requirements.txt     # fastapi + uvicorn
│   └── Dockerfile           # python:3.12-slim, port 8000
├── terraform/
│   ├── main.tf              # Root module — wires everything together
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf          # AWS provider, Terraform version
│   └── modules/
│       ├── networking/      # VPC, subnets, IGW, security groups
│       ├── ecr/             # ECR repo + lifecycle policy
│       ├── alb/             # ALB, target group, HTTP listener
│       ├── ecs/             # Fargate cluster, task def, IAM role, service
│       └── monitoring/      # CloudWatch log group + CPU/memory alarms
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD pipeline (3 jobs)
├── tests/
│   └── health_check.sh      # Integration test script
└── evidence/                # Screenshots from live AWS deployment
```

---

## Application

Built with **FastAPI (Python)** — lightweight, fast, and comes with auto-generated Swagger docs.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Interactive Hello World UI |
| `POST` | `/echo` | Accepts a message, returns a response, logs to CloudWatch |
| `GET` | `/health` | Health check — returns `{"status":"healthy"}` |
| `GET` | `/docs` | Auto-generated Swagger UI |

### Interactive Echo

Type one of the two supported inputs:

| Input | Response |
|---|---|
| `Hello World` | `Hello SS&C! 👋` |
| `Veerathorn` | `Hi! It's me Veerathorn, Nice to meet you! 🙌` |
| anything else | Prompt to use one of the two options |

Every submission is logged to **CloudWatch** with timestamp, IP, input, and reply.

---

## CI/CD Pipeline

**GitHub Actions** — triggers on every push to `main`, or manually via **Run workflow** with a deploy mode choice.

### Deploy Modes

| Mode | When to Use | Jobs That Run |
|---|---|---|
| `full` | First deploy or after infrastructure changes | Terraform + Build & Push + Integration Test |
| `app-only` | Code-only changes — infra already exists | Build & Push + Integration Test (Terraform skipped) |

Trigger manually: **GitHub → Actions → Deploy → Run workflow → choose mode**

### Pipeline Flow

```
Push to main (or workflow_dispatch)
           │
           ▼
┌────────────────────────────────────────────┐
│  Job 1: Terraform Apply  [full mode only]  │
│                                            │
│  terraform init  ──────────────────────►  Terraform Cloud
│  terraform plan                           (remote state store)
│  terraform apply                               │
│       └── Creates AWS infra ◄─────────────────┘
└──────────────────────┬─────────────────────────┘
                       │ (skipped in app-only mode)
                       ▼
┌───────────────────────────────────────────────┐
│  Job 2: Build & Push  [full + app-only]       │
│                                               │
│  docker build → tag :latest → push to ECR    │
│  aws ecs update-service --force-new-deployment│
└──────────────────────┬────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────┐
│  Job 3: Integration Health Check              │
│                                               │
│  health_check.sh → curl ALB /health          │
│  Fails pipeline if not HTTP 200               │
└───────────────────────────────────────────────┘
```

---

## Terraform State Management

Terraform state is stored in **Terraform Cloud** (free tier) using the `cloud {}` backend block in `versions.tf`.

| Setting | Value |
|---|---|
| **Organization** | `ssnc-veerathorn` |
| **Workspace** | `ssnc-hello-world` |
| **Execution mode** | Local (plan/apply runs on GitHub Actions runner — not TF Cloud servers) |
| **State storage** | Terraform Cloud (remote, versioned, locked) |

**Why this matters**: Local state files (`terraform.tfstate`) are ephemeral on GitHub Actions runners — they are lost after each run. With Terraform Cloud as the backend, state is persisted remotely, which means:
- Subsequent runs correctly detect existing AWS resources (no "already exists" errors)
- State is versioned and recoverable
- `TF_API_TOKEN` in GitHub Secrets authenticates the runner to Terraform Cloud

---

## Infrastructure (Terraform)

All infrastructure is defined as code across 5 modules:

- **networking** — VPC (`10.0.0.0/16`), 2 public subnets across AZs, IGW, route tables, ALB + ECS security groups
- **ecr** — Private ECR repository with lifecycle policy (retains last 5 images)
- **alb** — Internet-facing ALB, target group with `/health` health check, HTTP listener
- **ecs** — Fargate cluster with Container Insights, IAM execution role, task definition, service with rolling deployment
- **monitoring** — CloudWatch log group (7-day retention), CPU > 80% alarm, Memory > 80% alarm

### Security design
- ECS tasks are only reachable **via the ALB** — ECS security group restricts inbound to ALB SG only
- No direct public access to containers
- IAM role follows **least privilege** — only ECR pull and CloudWatch write
- No secrets hardcoded — AWS credentials passed via GitHub Secrets

---

## What I'd Add with More Time

| Addition | Reason |
|---|---|
| HTTPS + ACM certificate | Encrypt traffic in transit; terminate TLS at the ALB |
| Private subnets + NAT Gateway | Move ECS tasks off public subnets for defence in depth |
| AWS Secrets Manager | Rotate secrets without redeploying the container |
| ECS Auto Scaling (target tracking) | Scale task count based on CPU/memory — not just `desired_count = 1` |
| WAF on the ALB | Block common web exploits at the edge |
| Route 53 record | Friendly domain name instead of raw ALB DNS |
| AWS X-Ray | Distributed tracing across requests |
| `desired_count = 2` | One task per AZ for true zero-downtime rolling deploys |


