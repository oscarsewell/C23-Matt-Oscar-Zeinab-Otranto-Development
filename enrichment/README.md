# Enrichment
This program is to enrich text data parsed through a web scraper using OpenAI API for text analysis and subject identification. 

## Overview
**enrichment_and_upload.py** - Core functions used to create the enrichment_upload_lambda.py script. Handles the requests to the API, Data validation and uploading to DynamoDB.

**enrichment_upload_lambda.py** - AWS Lambda handler which executes the functions of enrichment_and_upload.py in a format suitable for AWS Lambda functions.

 
## Docker Build & ECR Upload

**Pre-requisite**
- Docker

Build the image:
```bash
docker buildx build -t c23-smearbot-data-enrichment:latest --provenance=false --platform="linux/amd64" .
```

Tag and push to ECR:
```bash
# Login to ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com

# Tag image for ECR
docker tag c23-smearbot-data-enrichment:latest <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/c23-smearbot-rss-extraction:latest

# Push to repository
docker push <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/c23-smearbot-data-enrichment:latest
```


## Secrets Manager

The enrichment script utilizes OpenAI API for text analysis and enrichment. Ensure you store your sensitive data properly.
- Upload an Openai key to AWS Secrets Manager. Use the Secret key value: **"OPENAI_API_KEY"**

