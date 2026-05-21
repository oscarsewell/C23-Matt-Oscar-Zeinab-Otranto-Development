import logging
import os
import json
from dotenv import load_dotenv
import boto3

from enrichment_and_upload import (
    get_llm_client,
    analyze_text,
    validate_enriched_data,
    get_dynamodb_items,
    upload_to_dynamodb
)

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager', region_name=os.getenv(
    'SECRETS_MANAGER_REGION', 'eu-west-2'))


def get_openai_api_key():
    """Retrieve OpenAI API key from AWS Secrets Manager."""
    try:
        secret_name = os.getenv('SECRETS_MANAGER_SECRET', 'c23-smearbot')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_dict = json.loads(response['SecretString'])
        api_key = secret_dict.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in secret")
        return api_key
    except Exception as e:
        logger.error(
            f"Failed to retrieve API key from Secrets Manager: {str(e)}")
        raise


def lambda_handler(event, context):
    """AWS Lambda handler function to process articles from S3."""
    try:
        # Set OpenAI API key from Secrets Manager
        api_key = get_openai_api_key()

        # Extract S3 bucket and key from the event (directly at root level from Step Function)
        s3_bucket = event.get("s3_bucket")
        s3_key = event.get("s3_key")

        if not s3_bucket or not s3_key:
            logger.error(
                f"Missing s3_bucket or s3_key in event. Event: {json.dumps(event)}")
        logger.info(f"Reading articles from S3: s3://{s3_bucket}/{s3_key}")
        try:
            response = s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            articles_data = json.loads(response['Body'].read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to read articles from S3: {str(e)}")
            return {"status": "error", "message": f"Failed to read from S3: {str(e)}"}

        # Ensure articles_data is a list
        if not isinstance(articles_data, list):
            articles_data = [articles_data]

        logger.info(f"Processing {len(articles_data)} articles")

        client = get_llm_client(api_key)
        all_dynamo_items = []

        # Process each article
        for article in articles_data:
            try:
                # Ensure required fields exist with defaults
                article_data = {
                    "published_at": article.get("published_at", "")[:19] if article.get("published_at") else "",
                    "url": article.get("url", ""),
                    "title": article.get("title", ""),
                    "authors": article.get("authors", []) or [],
                    "body": article.get("body", "") or "",
                    "description": article.get("description", "") or ""
                }

                # Skip if missing required fields
                if not article_data["body"] or not article_data["url"]:
                    logger.warning(
                        f"Skipping article with missing body or URL: {article_data.get('url', 'unknown')}")
                    continue

                # Analyze text
                analysis_result = analyze_text(client, article_data["body"])

                if not validate_enriched_data(analysis_result):
                    logger.warning(
                        f"Validation failed for article: {article_data['url']}")
                    continue

                # Create DynamoDB items
                dynamo_items = get_dynamodb_items(
                    analysis_result, article_data)
                if dynamo_items:
                    all_dynamo_items.extend(dynamo_items)

            except Exception as e:
                logger.error(f"Error processing article: {str(e)}")
                continue

        # Upload all items to DynamoDB
        if all_dynamo_items:
            logger.info(f"Uploading {len(all_dynamo_items)} items to DynamoDB")
            upload_to_dynamodb(all_dynamo_items)

        return {
            "status": "success",
            "message": "Data processed and uploaded successfully",
            "items_count": len(all_dynamo_items),
            "articles_processed": len(articles_data)
        }

    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return {"status": "error", "message": f"Internal server error: {str(e)}"}
