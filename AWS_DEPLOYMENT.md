# AWS Deployment Guide - Air Traffic Control System

This guide covers deploying the ATC system to AWS using various services for a distributed, cloud-based architecture.

## 🏗 Architecture Options

### Option 1: Serverless Architecture (Recommended for Learning)

```
┌─────────────────────────────────────────────────────────────┐
│                        AWS CloudFront                        │
│                     (Content Delivery)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                        AWS S3                                │
│                   (Static Frontend)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                   AWS API Gateway                            │
│                  (REST API Endpoint)                         │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    AWS Lambda                                │
│          (Python Functions - app.py endpoints)               │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    AWS RDS PostgreSQL                        │
│                     (Database)                               │
└─────────────────────────────────────────────────────────────┘
```

**Pros**: Auto-scaling, pay-per-use, high availability
**Cons**: Cold start latency, function timeout limits

---

### Option 2: Container-Based Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Application Load Balancer (ALB)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    AWS ECS/Fargate                          │
│              (Docker Containers - Backend)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │Container1│  │Container2│  │Container3│                 │
│  └──────────┘  └──────────┘  └──────────┘                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    AWS RDS PostgreSQL                        │
└─────────────────────────────────────────────────────────────┘
```

**Pros**: Easy deployment, consistent environments, standard Docker
**Cons**: Higher cost than serverless, requires container management

---

### Option 3: Traditional EC2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Elastic Load Balancer (ELB)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                   EC2 Auto Scaling Group                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  │  EC2-1   │  │  EC2-2   │  │  EC2-3   │                 │
│  │ (Backend)│  │ (Backend)│  │ (Backend)│                 │
│  └──────────┘  └──────────┘  └──────────┘                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    AWS RDS PostgreSQL                        │
└─────────────────────────────────────────────────────────────┘
```

**Pros**: Full control, no function limits, easier debugging
**Cons**: Higher cost, manual scaling configuration

---

## 🚀 Detailed Deployment Instructions

## Option 1: Serverless Deployment (AWS Lambda)

### Prerequisites

1. AWS Account
2. AWS CLI installed and configured
3. Python 3.9+
4. Serverless Framework or SAM CLI (optional)

### Step 1: Prepare Lambda Function

Create `lambda_function.py`:

```python
import json
from app import create_app

# Create Flask app
app = create_app('production')

def lambda_handler(event, context):
    """AWS Lambda handler"""
    from werkzeug.wrappers import Request, Response

    # Convert Lambda event to WSGI environ
    headers = event.get('headers', {})
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    body = event.get('body', '')

    # Create WSGI request
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': event.get('queryStringParameters', ''),
        'CONTENT_LENGTH': len(body),
        'wsgi.input': body,
        'HTTP_HOST': headers.get('Host', ''),
    }

    # Get response from Flask app
    with app.request_context(environ):
        response = app.full_dispatch_request()

    return {
        'statusCode': response.status_code,
        'headers': dict(response.headers),
        'body': response.get_data(as_text=True)
    }
```

### Step 2: Create RDS Database

```bash
# Using AWS CLI
aws rds create-db-instance \
    --db-instance-identifier atc-database \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password YourPassword123 \
    --allocated-storage 20
```

### Step 3: Package Lambda Function

```bash
# Install dependencies
pip install -r requirements.txt -t ./package

# Copy your code
cp *.py ./package/

# Create deployment package
cd package
zip -r ../lambda_deployment.zip .
cd ..
```

### Step 4: Create Lambda Function

```bash
aws lambda create-function \
    --function-name atc-backend \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://lambda_deployment.zip \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables="{DATABASE_URL=postgresql://admin:pass@rds-endpoint:5432/atc}"
```

### Step 5: Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
    --name "ATC System API" \
    --description "Air Traffic Control System REST API"

# Configure routes to Lambda function
# (Use AWS Console for easier setup)
```

### Step 6: Deploy Frontend to S3

```bash
# Create S3 bucket
aws s3 mb s3://atc-frontend-bucket

# Configure bucket for static website hosting
aws s3 website s3://atc-frontend-bucket \
    --index-document index.html

# Update API endpoint in script.js
# const API_BASE_URL = 'https://your-api-gateway-url/api';

# Upload frontend files
aws s3 sync ./frontend/ s3://atc-frontend-bucket --acl public-read
```

### Step 7: Setup CloudFront (Optional)

```bash
aws cloudfront create-distribution \
    --origin-domain-name atc-frontend-bucket.s3.amazonaws.com \
    --default-root-object index.html
```

---

## Option 2: Docker Container Deployment (ECS/Fargate)

### Step 1: Create Dockerfile

Already provided in README.md:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Step 2: Build and Push to ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repository
aws ecr create-repository --repository-name atc-system

# Build image
docker build -t atc-system .

# Tag image
docker tag atc-system:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/atc-system:latest

# Push to ECR
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/atc-system:latest
```

### Step 3: Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name atc-cluster
```

### Step 4: Create Task Definition

Create `task-definition.json`:

```json
{
  "family": "atc-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "atc-backend",
      "image": "YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/atc-system:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "DATABASE_URL",
          "value": "postgresql://admin:pass@rds-endpoint:5432/atc"
        }
      ],
      "essential": true
    }
  ]
}
```

Register task:
```bash
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

### Step 5: Create Service

```bash
aws ecs create-service \
    --cluster atc-cluster \
    --service-name atc-service \
    --task-definition atc-backend \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### Step 6: Setup Load Balancer

Use AWS Console to:
1. Create Application Load Balancer
2. Configure target group (port 5000)
3. Attach to ECS service
4. Configure health checks

---

## Option 3: EC2 Deployment

### Step 1: Launch EC2 Instance

```bash
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t2.micro \
    --key-name your-key-pair \
    --security-groups atc-sg \
    --user-data file://setup-script.sh
```

### Step 2: Create Setup Script

`setup-script.sh`:
```bash
#!/bin/bash
# Update system
sudo yum update -y

# Install Python 3.9
sudo yum install python39 python39-pip -y

# Clone repository (or copy files)
cd /home/ec2-user
# Copy application files

# Install dependencies
pip3.9 install -r requirements.txt

# Setup systemd service
sudo tee /etc/systemd/system/atc.service > /dev/null <<EOF
[Unit]
Description=ATC System Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/atc
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable atc
sudo systemctl start atc
```

### Step 3: Configure Security Groups

```bash
# Allow HTTP/HTTPS
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0

# Allow application port
aws ec2 authorize-security-group-ingress \
    --group-id sg-xxxxx \
    --protocol tcp \
    --port 5000 \
    --cidr 0.0.0.0/0
```

---

## 📊 Database Setup (RDS PostgreSQL)

### Create RDS Instance

```bash
aws rds create-db-instance \
    --db-instance-identifier atc-database \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 14.7 \
    --master-username atcadmin \
    --master-user-password SecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name default \
    --backup-retention-period 7 \
    --publicly-accessible false
```

### Initialize Database

```bash
# SSH to EC2 or use Lambda function
python init_db.py
```

### Connection String

```
DATABASE_URL=postgresql://atcadmin:SecurePassword123!@atc-database.xxxxx.us-east-1.rds.amazonaws.com:5432/postgres
```

---

## 🔒 Security Configuration

### IAM Roles

**Lambda Execution Role:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rds:DescribeDBInstances",
        "rds:Connect"
      ],
      "Resource": "*"
    }
  ]
}
```

### Security Groups

**Backend Security Group:**
- Inbound: Port 5000 from Load Balancer SG
- Outbound: Port 5432 to RDS SG

**RDS Security Group:**
- Inbound: Port 5432 from Backend SG
- Outbound: All

**Load Balancer Security Group:**
- Inbound: Ports 80, 443 from 0.0.0.0/0
- Outbound: Port 5000 to Backend SG

---

## 📈 Monitoring & Logging

### CloudWatch

```bash
# Create log group
aws logs create-log-group --log-group-name /aws/atc-system

# Setup alarms
aws cloudwatch put-metric-alarm \
    --alarm-name atc-high-error-rate \
    --alarm-description "Alert on high error rate" \
    --metric-name Errors \
    --namespace AWS/Lambda \
    --statistic Sum \
    --period 300 \
    --evaluation-periods 1 \
    --threshold 10 \
    --comparison-operator GreaterThanThreshold
```

### Cost Monitoring

Enable AWS Cost Explorer and set budget alerts:

```bash
aws budgets create-budget \
    --account-id YOUR_ACCOUNT \
    --budget file://budget.json
```

---

## 💰 Cost Estimates

### Serverless (Low Usage)
- Lambda: ~$5/month (1M requests)
- API Gateway: ~$3.50/month
- RDS t3.micro: ~$15/month
- S3 + CloudFront: ~$1/month
- **Total: ~$25/month**

### Container (ECS Fargate)
- Fargate (2 tasks): ~$30/month
- Load Balancer: ~$20/month
- RDS t3.micro: ~$15/month
- **Total: ~$65/month**

### EC2
- t2.micro instances (2): ~$15/month
- Load Balancer: ~$20/month
- RDS t3.micro: ~$15/month
- **Total: ~$50/month**

---

## 🧪 Testing Deployment

### Health Check

```bash
curl https://your-api-url/api/health
```

### Load Testing

```bash
# Install Apache Bench
sudo yum install httpd-tools -y

# Run load test
ab -n 1000 -c 10 https://your-api-url/api/dashboard
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build and push Docker image to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
          docker build -t atc-system .
          docker tag atc-system:latest $ECR_URI/atc-system:latest
          docker push $ECR_URI/atc-system:latest

      - name: Update ECS service
        run: |
          aws ecs update-service --cluster atc-cluster --service atc-service --force-new-deployment
```

---

## 📝 Post-Deployment Checklist

- [ ] Database initialized with schema
- [ ] Environment variables configured
- [ ] Security groups properly configured
- [ ] SSL certificate installed (HTTPS)
- [ ] CloudWatch alarms setup
- [ ] Backup strategy implemented
- [ ] Cost alerts configured
- [ ] Load testing completed
- [ ] Documentation updated with endpoints
- [ ] Team trained on monitoring dashboard

---

## 🆘 Troubleshooting

### Lambda Cold Starts
- Increase memory allocation (faster cold start)
- Use provisioned concurrency
- Implement warming function

### Database Connections
- Use connection pooling
- Set appropriate timeout values
- Monitor RDS connections in CloudWatch

### CORS Issues
- Verify API Gateway CORS configuration
- Check CloudFront cache behavior
- Update allowed origins

---

**For AWS support, consult AWS documentation or AWS Support depending on your support tier.**
