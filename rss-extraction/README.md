# RSS Feed Parser

Python module for extracting story URLs from RSS feeds with S3-based caching and Lambda integration.

## Overview

**rss_parser.py** — Core RSS extraction with HTTP conditional requests (ETag/Last-Modified) and S3 caching. Extracts URLs from feeds, detects new stories by comparing with cached URLs, and handles offline fallback.

**lambda_function.py** — AWS Lambda handler that processes an event containing a list of feed URLs, returns newly discovered URLs and metrics.

## Docker Build & ECR Upload

Build the image:
```bash
docker build -t c23-smearbot-rss-extraction:latest .
```

Tag and push to ECR:
```bash
# Login to ECR
aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com

# Tag image for ECR
docker tag c23-smearbot-rss-extraction:latest <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/c23-smearbot-rss-extraction:latest

# Push to repository
docker push <ACCOUNT_ID>.dkr.ecr.eu-west-2.amazonaws.com/c23-smearbot-rss-extraction:latest
```

## Configuration

Set environment variables:
- `AWS_REGION` — AWS region (default: eu-west-2)
- `S3_CACHING_BUCKET` — S3 bucket for caching (default: c23-smearbot-caching-bucket)
- `S3_CACHE_PREFIX` — S3 prefix for cache files (default: rss_feed_cache/)

## Lambda Invocation

Event:
```json
{
    "feed_urls": [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://www.theguardian.com/world/rss"
    ]
}
```

Response:
```json
{
    "statusCode": 200,
    "body": {
        "new_urls": ["url1", "url2", ...],
        "feeds_processed": 2,
        "total_new_urls": 15
    }
}
```

## Testing

```bash
pytest -v
pytest --cov=rss_parser --cov=lambda_function
```