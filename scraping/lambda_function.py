import json
import boto3
import os
import logging
from datetime import datetime
from scraper import scrape_articles

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
CACHING_BUCKET = os.getenv('S3_CACHING_BUCKET', 'c23-smearbot-caching-bucket')


def lambda_handler(event, context):
    urls = event.get("urls", [])

    if not urls:
        return {
            "s3_bucket": CACHING_BUCKET,
            "s3_key": None,
            "error": "No URLs provided",
            "articles_count": 0
        }

    articles = scrape_articles(urls)

    if not articles:
        return {
            "s3_bucket": CACHING_BUCKET,
            "s3_key": None,
            "error": "No articles scraped",
            "articles_count": 0
        }

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    execution_id = context.invoked_function_arn.split(
        ":")[-1] if context else "unknown"
    s3_key = f"scraping-results/{execution_id}_{timestamp}/articles.json"

    try:
        s3_client.put_object(
            Bucket=CACHING_BUCKET,
            Key=s3_key,
            Body=json.dumps(articles),
            ContentType='application/json'
        )
        logger.info(
            f"Wrote {len(articles)} articles to S3: s3://{CACHING_BUCKET}/{s3_key}")
    except Exception as e:
        logger.error(f"Failed to write articles to S3: {str(e)}")
        return {
            "s3_bucket": CACHING_BUCKET,
            "s3_key": None,
            "error": f"Failed to write to S3: {str(e)}",
            "articles_count": 0
        }

    return {
        "s3_key": s3_key,
        "s3_bucket": CACHING_BUCKET,
        "articles_count": len(articles)
    }
