# Enterprise Cloud Banking Platform

A secure, highly available, and scalable 3-Tier cloud infrastructure on AWS for core banking CRUD operations. Built with **Terraform (IaC)**, **Python FastAPI**, **Docker**, **AWS ECS Fargate (Serverless Containers)**, **Amazon RDS PostgreSQL**, and **GitHub Actions CI/CD**.

---

## 1. Architecture Overview

The platform implements a **Secure 3-Tier Multi-AZ Serverless Architecture** strictly adhering to the AWS Well-Architected Framework and financial industry security standards.

```
                                [ Internet Clients ]
                                         │
                                         ▼ HTTP (Port 80)
       ┌────────────────────────────────────────────────────────────────────────┐
       │ AWS VPC (10.0.0.0/16)                                                  │
       │                                                                        │
       │  [ Tier 1: Public Web Subnets (AZ-a & AZ-b) ]                          │
       │  ┌──────────────────────────────────────────────────────────────────┐  │
       │  │       Application Load Balancer (ALB)                            │  │
       │  │       • Security Group: Inbound 80 (HTTP) from 0.0.0.0/0         │  │
       │  │       • Automated Health Checks (/health)                        │  │
       │  │       • Target Group: Port 8000 (Target Type: "ip")              │  │
       │  └──────────────────────────────────┬───────────────────────────────┘  │
       │                                     │ Ingress Port 8000                │
       │                                     ▼                                  │
       │  [ Tier 2: Private Application Subnets (AZ-a & AZ-b) ]                 │
       │  ┌──────────────────────────────────────────────────────────────────┐  │
       │  │   AWS ECS Fargate Service (Serverless Containers)                │  │
       │  │   • Cluster: banking-platform-cluster                            │  │
       │  │   • Network Mode: 'awsvpc' (dedicated micro-VM ENIs)             │  │
       │  │   • High Availability: 2 tasks distributed across Multi-AZ       │  │
       │  │   • Zero VM Management / Zero OS Patching                        │  │
       │  │   • Native AWS Secrets Manager Secret Injection (KMS)            │  │
       │  │   • Container logs streamed to AWS CloudWatch via awslogs        │  │
       │  └──────────────────────────────────┬───────────────────────────────┘  │
       │                                     │ Port 5432                        │
       │                                     ▼                                  │
       │  [ Tier 3: Isolated Database Subnets (AZ-a & AZ-b) ]                   │
       │  ┌──────────────────────────────────────────────────────────────────┐  │
       │  │   Amazon RDS PostgreSQL (db.t3.micro)                            │  │
       │  │   • Security Group: Ingress 5432 strictly from ECS Tasks SG      │  │
       │  │   • Encrypted at rest via AWS KMS (AES-256)                      │  │
       │  │   • Public Access: DISABLED                                      │  │
       │  │   • Passwords managed via AWS Secrets Manager                    │  │
       │  └──────────────────────────────────────────────────────────────────┘  │
       └────────────────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> **Protocol & TLS Design Note:** The Application Load Balancer currently listens on **HTTP (Port 80)** because AWS Certificate Manager (ACM) does not issue SSL/TLS certificates for default `*.elb.amazonaws.com` hostnames without a custom domain. In an enterprise production deployment, a custom domain registered in **Amazon Route 53** (e.g., `api.banking.com`) is attached with an **AWS ACM TLS 1.3 certificate on Port 443**, and Port 80 is configured with an automated HTTP $\rightarrow$ HTTPS 301 redirect.

---

## 2. Key Architectural Decisions

| Requirement | Implementation | Design Justification |
| :--- | :--- | :--- |
| **Serverless Compute (Zero OS Overhead)** | **AWS ECS Fargate** | Eliminates virtual machine management, golden AMIs, and host operating system CVE patching. Tasks run in isolated, dedicated micro-VMs. |
| **High Availability & Resilience** | **Multi-AZ ECS Fargate Service (Desired Count: 2)** | Container tasks are distributed across multiple Availability Zones. If an availability zone or task degrades, the ALB and ECS service automatically re-route traffic and replace tasks. |
| **Micro-Segmentation & Security** | **`awsvpc` Networking Mode** | Each container task receives its own Elastic Network Interface (ENI) with a dedicated private IP address, enforcing fine-grained security group isolation. |
| **Data Consistency & ACID** | **Amazon RDS PostgreSQL** | Banking transactions require ACID guarantees. PostgreSQL with row-level locks (`SELECT ... FOR UPDATE`) prevents concurrent balance race conditions. |
| **Least-Privilege Security** | **Chained Security Groups** | The database only accepts port 5432 connections from the ECS tasks; ECS tasks only accept port 8000 connections from the ALB. Zero SSH or administrative ports exposed. |
| **Runtime Secret Management** | **AWS Secrets Manager + KMS** | Database passwords are never baked into Docker images or committed to Git. ECS agent decrypts and injects secrets directly into container memory via native integration. |

---

## 3. Security Implementation Details

1. **Zero Host Attack Surface:**
   * Traditional EC2 instances expose SSH ports and host Linux operating systems. ECS Fargate operates on serverless micro-VMs with zero inbound administrative ports open.
2. **Native Secrets Injection (12-Factor App):**
   * Database credentials are generated randomly and stored in **AWS Secrets Manager**.
   * AWS ECS Fargate natively reads the secret ARN using the Task Execution Role and injects it into container RAM before process startup.
3. **Encryption Everywhere:**
   * **At Rest:** Amazon RDS storage is encrypted using **AWS KMS**. ECR images are encrypted with AES-256.
   * **In Transit:** Traffic within the VPC communicates over private interfaces, and database drivers enforce encrypted connections.
4. **Automated Vulnerability Scanning:**
   * Amazon ECR repository is configured with `scan_on_push = true` to automatically scan images for CVEs upon each push.

---

## 4. API Endpoints Specification

| Method | Endpoint | Description | Sample Payload |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Health check for ALB target group | None |
| `GET` | `/accounts/{id}/balance` | Retrieves account balance & holder details | None |
| `POST` | `/accounts/{id}/deposit` | Deposits money into account | `{"amount": 250.00}` |
| `POST` | `/accounts/{id}/withdraw` | Withdraws money (validates insufficient funds) | `{"amount": 100.00}` |
| `GET` | `/docs` | Interactive Swagger UI documentation | None |

---

## 5. Step-by-Step Setup & Deployment Guide

### Prerequisites
* AWS CLI installed and configured (`aws configure`).
* Terraform `>= 1.5.0` installed.
* Docker installed locally.

---

### Step 1: Clone Repository
```bash
git clone <YOUR_GITHUB_REPO_URL>
cd secure-banking-platform
```

---

### Step 2: Provision Cloud Infrastructure via Terraform

1. Navigate to the terraform directory:
   ```bash
   cd terraform
   ```
2. Initialize Terraform providers:
   ```bash
   terraform init
   ```
3. Preview the infrastructure plan:
   ```bash
   terraform plan
   ```
4. Deploy the infrastructure:
   ```bash
   terraform apply -auto-approve
   ```
5. Note the outputs:
   * `alb_dns_name`: Public URL of the banking application.
   * `api_docs_swagger_url`: Swagger documentation link.
   * `ecr_repository_url`: Docker registry URL.

---

### Step 3: Build & Push Initial Container Image

Log into your newly created AWS ECR repository and push the banking application image:

```bash
# Set your AWS region and ECR URL from terraform output
export AWS_REGION="ap-southeast-1"
export ECR_URL="$(terraform output -raw ecr_repository_url)"

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URL

# Build Docker image
cd ../app
docker build -t $ECR_URL:latest .

# Push image to ECR
docker push $ECR_URL:latest
```

---

### Step 4: Configure GitHub Actions CI/CD Pipeline

To enable automated testing and continuous deployment:
1. In your GitHub repository, navigate to **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
2. Add the following secrets:
   * `AWS_ACCESS_KEY_ID`: Your AWS IAM Access Key.
   * `AWS_SECRET_ACCESS_KEY`: Your AWS IAM Secret Access Key.
3. Every subsequent push to `main` will:
   * Automatically run the `pytest` test suite.
   * Build and tag the Docker image.
   * Push the container to Amazon ECR.
   * Trigger an AWS ECS Fargate **Rolling Deployment** to replace tasks with the updated container with zero downtime.

---

## 6. Verification & Testing Runbook

Once deployed, you can verify and test all endpoints using `curl` or the automated browser UI.

### Option A: Interactive Swagger UI (Recommended)
Open your browser and navigate to:
```
http://<ALB-DNS-NAME>/docs
```
You can interactively test the balance check, deposits, and withdrawals directly on the web page.

### Option B: Command-Line Verification (`curl`)

1. **Verify Health Check:**
   ```bash
   curl http://<ALB-DNS-NAME>/health
   ```
   *Expected Response:*
   ```json
   {"status":"HEALTHY","service":"banking-api"}
   ```

2. **Query Initial Account Balance:**
   ```bash
   curl http://<ALB-DNS-NAME>/accounts/1/balance
   ```
   *Expected Response:*
   ```json
   {"id":1,"account_number":"ACC-1001","holder_name":"Praveen Bonala","balance":1000.0}
   ```

3. **Deposit Funds:**
   ```bash
   curl -X POST http://<ALB-DNS-NAME>/accounts/1/deposit \
     -H "Content-Type: application/json" \
     -d '{"amount": 500.00}'
   ```
   *Expected Response:*
   ```json
   {"message":"Deposit successful","account_id":1,"account_number":"ACC-1001","new_balance":1500.0}
   ```

4. **Withdraw Funds:**
   ```bash
   curl -X POST http://<ALB-DNS-NAME>/accounts/1/withdraw \
     -H "Content-Type: application/json" \
     -d '{"amount": 300.00}'
   ```
   *Expected Response:*
   ```json
   {"message":"Withdrawal successful","account_id":1,"account_number":"ACC-1001","new_balance":1200.0}
   ```

5. **Test Overdraft / Insufficient Funds Validation:**
   ```bash
   curl -X POST http://<ALB-DNS-NAME>/accounts/1/withdraw \
     -H "Content-Type: application/json" \
     -d '{"amount": 5000.00}'
   ```
   *Expected Response (HTTP 400 Bad Request):*
   ```json
   {"detail":"Insufficient funds. Current balance: 1200.0, Requested: 5000.0"}
   ```

---

## 7. Monitoring & Observability

The infrastructure includes proactive **Amazon CloudWatch Alarms**:
1. **ALB 5XX Errors Alarm (`banking-platform-alb-high-5xx-errors`):**
   * Monitors `HTTPCode_Target_5XX_Count`. Triggers an alert if more than 5 server errors occur in a 1-minute window.
2. **Latency Alarm (`banking-platform-alb-high-latency`):**
   * Monitors `TargetResponseTime`. Triggers if average latency exceeds 2.0 seconds.
3. **Database Health Alarm (`banking-platform-rds-high-cpu`):**
   * Monitors `CPUUtilization` on the PostgreSQL instance. Triggers if CPU exceeds 80% for 4 minutes.

---

## 8. Clean Teardown

To avoid unnecessary AWS charges after grading/evaluation:

```bash
cd terraform
terraform destroy -auto-approve
```
All resources (VPC, ALB, ECS Fargate cluster & services, RDS PostgreSQL instance, ECR repository, and Secrets Manager secret) will be cleanly terminated.
