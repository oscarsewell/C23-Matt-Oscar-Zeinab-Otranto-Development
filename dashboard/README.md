# Dashboard
Web-based dashboard for viewing enriched articles stored in DynamoDB with search and filtering capabilities.

## Overview
**app.py** - Streamlit web application that displays articles and provides search functionality.

**data_access.py** - Functions for querying DynamoDB and retrieving article data.

**transformations.py** - Data transformation and normalization functions for dashboard display.

## Features
- View all enriched articles from DynamoDB
- Search articles by subject name, keywords, or content
- Filter and sort results
- Display article metadata including sentiment scores

## Running Locally

**Pre-requisite**
- Python 3.12+
- AWS credentials configured

Install dependencies:
```bash
pip install -r requirements.txt
```

Run the dashboard:
```bash
streamlit run app.py
```

The dashboard will be available at `http://localhost:8501`

## Docker Build & Deployment

Build the image:
```bash
docker build -t c23-smearbot-dashboard:latest .
```

Tag and push to ECR:
```bash
# Login to ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com

# Tag image for ECR
docker tag c23-smearbot-dashboard:latest <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/c23-smearbot-dashboard:latest

# Push to repository
docker push <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/c23-smearbot-dashboard:latest
```

## AWS Configuration

**Environment Variables:**
- `DYNAMODB_TABLE_NAME` - DynamoDB table name (default: "c23-smearbot-dynamodb-table")
- `AWS_REGION` - AWS region (default: "eu-west-2")

**IAM Permissions Required:**
- `dynamodb:Scan`
- `dynamodb:Query`
- `dynamodb:GetItem`