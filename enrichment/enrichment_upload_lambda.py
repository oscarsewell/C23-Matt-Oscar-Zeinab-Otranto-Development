import logging
import os
import openai as oa
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


def lambda_handler(event, context):
    """AWS Lambda handler function to process incoming events."""
    try:
        # Extract article data from the event (this will depend on your event structure)
        article_data = {
            # Ensure ISO format with 'Z' if needed
            "published_at": event["published_at"] if len(event["published_at"]) == 19 else event["published_at"][:19],
            "url": event["url"],
            "title": event["title"],
            "authors": event["authors"],
            "body": event["body"],
            "description": event["description"]
        }
        client = get_llm_client()
        analysis_result = analyze_text(client, article_data["body"])
        if not validate_enriched_data(analysis_result):
            logger.error("Enriched data validation failed.")
            return {"statusCode": 400, "body": "Invalid enriched data"}
        dynamo_items = get_dynamodb_items(analysis_result, article_data)
        if not dynamo_items:
            logger.error("Error creating items for DynamoDB upload.")
            return {"statusCode": 400, "body": "No valid items to upload"}
        upload_to_dynamodb(dynamo_items)
        return {"statusCode": 200, "body": "Data processed and uploaded successfully"}
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return {"statusCode": 500, "body": "Internal server error"}
