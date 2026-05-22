from bluesky_functions import login_to_bluesky, is_sentiment_score_valid, create_positive_sentiment_post, create_negative_sentiment_post, read_bio, post_to_bluesky
import os
from dotenv import load_dotenv
import logging
import boto3
import json

load_dotenv()  # Load environment variables from .env file
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# AWS clients
secrets_client = boto3.client('secretsmanager')


def get_bluesky_credentials():
    """Retrieve Bluesky credentials from Secrets Manager"""
    try:
        secret_name = os.environ.get('SECRETS_MANAGER_SECRET', 'c23-smearbot')
        region = os.environ.get('SECRETS_MANAGER_REGION', 'eu-west-2')

        response = secrets_client.get_secret_value(SecretId=secret_name)

        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            bluesky_handle = secret.get('BLUESKY_HANDLE')
            bluesky_password = secret.get('BLUESKY_APP_PASSWORD')

            if not bluesky_handle or not bluesky_password:
                logger.error(
                    "Missing BLUESKY_HANDLE or BLUESKY_APP_PASSWORD in secret")
                raise ValueError(
                    "Missing Bluesky credentials in Secrets Manager")

            return bluesky_handle, bluesky_password
        else:
            logger.error("Secret format not supported")
            raise ValueError("Unsupported secret format")
    except Exception as e:
        logger.error(f"Failed to retrieve Bluesky credentials: {e}")
        raise


def parse_dynamodb_value(value):
    """Parse DynamoDB typed value (e.g., {'S': 'string'} or {'N': '123'})"""
    if isinstance(value, dict):
        if 'S' in value:
            return value['S']
        elif 'N' in value:
            return float(value['N'])
        elif 'M' in value:
            # Map type
            return {k: parse_dynamodb_value(v) for k, v in value['M'].items()}
        elif 'L' in value:
            # List type
            return [parse_dynamodb_value(v) for v in value['L']]
    return value


def lambda_handler(event, context):
    """AWS Lambda handler function to process incoming DynamoDB stream events"""

    logger.info(
        f"Received event with {len(event.get('Records', []))} record(s)")

    # Handle DynamoDB Streams format: Records array with stream event data
    if 'Records' not in event:
        logger.error(
            f"Invalid event structure: missing 'Records' key. Event: {event}")
        return {
            "statusCode": 400,
            "body": "Invalid event structure: missing 'Records' key"
        }

    records = event['Records']
    if not records:
        logger.info("No records to process")
        return {
            "statusCode": 200,
            "body": "No records to process"
        }

    # Process the first record (Lambda is configured for BatchSize: 1)
    record = records[0]

    # Validate record structure
    if 'eventName' not in record:
        logger.error(
            f"Invalid record structure: missing 'eventName' key. Record: {record}")
        return {
            "statusCode": 400,
            "body": "Invalid record structure: missing 'eventName' key"
        }

    # Check event type
    if record['eventName'] != 'INSERT':
        logger.info(
            f"Event ignored. Only INSERT events are processed. eventName: {record['eventName']}")
        return {
            "statusCode": 200,
            "body": "Event ignored. Only INSERT events are processed."
        }

    # Extract DynamoDB stream data
    if 'dynamodb' not in record:
        logger.error(
            f"Invalid record structure: missing 'dynamodb' key. Record: {record}")
        return {
            "statusCode": 400,
            "body": "Invalid record structure: missing 'dynamodb' key"
        }

    dynamodb_record = record['dynamodb']
    if 'NewImage' not in dynamodb_record:
        logger.error(
            f"Invalid record structure: missing 'NewImage' in dynamodb. Record: {record}")
        return {
            "statusCode": 400,
            "body": "Invalid record structure: missing 'NewImage' in dynamodb"
        }

    # Parse the DynamoDB NewImage format
    new_image_raw = dynamodb_record['NewImage']
    new_image = {k: parse_dynamodb_value(v) for k, v in new_image_raw.items()}

    logger.info(f"Parsed NewImage: {new_image}")

    # Validate sentiment score
    sentiment_score = new_image.get('sentiment_score')
    if sentiment_score is None:
        logger.error(f"Invalid record: missing 'sentiment_score' in NewImage")
        return {
            "statusCode": 400,
            "body": "Invalid record: missing 'sentiment_score' in NewImage"
        }

    if not is_sentiment_score_valid(sentiment_score, threshold=0):
        logger.info(
            f"Sentiment score too low, skipping post creation. score: {sentiment_score}")
        return {
            "statusCode": 200,
            "body": "Sentiment score too low for posting"
        }

    # Get subject name
    subject_name = new_image.get('subject_name')
    if not subject_name:
        logger.error(f"Invalid record: missing 'subject_name' in NewImage")
        return {
            "statusCode": 400,
            "body": "Invalid record: missing 'subject_name' in NewImage"
        }

    # Get article URL
    article_url = new_image.get('article_url')
    if not article_url:
        logger.error(f"Invalid record: missing 'article_url' in NewImage")
        return {
            "statusCode": 400,
            "body": "Invalid record: missing 'article_url' in NewImage"
        }

    # Login to Bluesky and verify subject
    try:
        bluesky_handle, bluesky_password = get_bluesky_credentials()
    except Exception as e:
        logger.error(f"Failed to get Bluesky credentials: {e}")
        return {
            "statusCode": 500,
            "body": "Failed to retrieve Bluesky credentials"
        }

    try:
        client = login_to_bluesky(bluesky_handle, bluesky_password)
    except Exception as e:
        logger.error(f"Failed to login to Bluesky: {e}")
        return {
            "statusCode": 500,
            "body": f"Failed to login to Bluesky: {e}"
        }

    bio_subject = read_bio(client, bluesky_handle)

    if subject_name != bio_subject:
        logger.info(
            f"Subject name does not match the target profile (in bio), skipping post creation. subject_name: {subject_name}, bio_subject: {bio_subject}")
        return {
            "statusCode": 200,
            "body": "Event ignored. Subject name does not match bio."
        }

    # Create and post to Bluesky
    try:
        post_to_bluesky(client, create_positive_sentiment_post(article_url))
        logger.info(
            f"Post created successfully for subject: {subject_name} with url: {article_url}")
        return {
            "statusCode": 200,
            "body": f"Post created successfully for subject: {subject_name} with url: {article_url}"
        }
    except Exception as e:
        logger.error(f"Failed to post to Bluesky: {e}")
        return {
            "statusCode": 500,
            "body": f"Failed to post to Bluesky: {e}"
        }
