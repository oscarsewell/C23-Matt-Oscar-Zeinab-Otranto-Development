from bluesky_functions import login_to_bluesky, is_sentiment_score_valid, create_positive_sentiment_post, create_negative_sentiment_post, read_bio, post_to_bluesky
import os
from dotenv import load_dotenv
import logging

load_dotenv()  # Load environment variables from .env file
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def lambda_handler(event, context):
    """AWS Lambda handler function to process incoming events"""

    logger.info(f"Received event: {event}")
    if not is_sentiment_score_valid(event['NewImage']['sentiment_score'], threshold=0):
        logger.info(
            f"Sentiment score too low, skipping post creation. score: {event['NewImage']['sentiment_score']}")

        return {
            "statusCode": 400,
            "body": "Invalid sentiment score. Must be a float above 3.5."
        }
    if not event['eventName'] == 'INSERT':
        logger.info(
            f"Event ignored. Only INSERT events are processed. eventName: {event['eventName']}")
        return {
            "statusCode": 400,
            "body": "Event ignored. Only INSERT events are processed."
        }

    client = login_to_bluesky(os.environ.get("BLUESKY_HANDLE"),
                              os.environ.get("BLUESKY_APP_PASSWORD"))
    if event.get("subject_name") != read_bio(client, os.environ.get("BLUESKY_HANDLE")):
        logger.info(
            f"Subject name does not match the target profile (in bio), skipping post creation. subject_name: {event.get('subject_name')}")
        return {
            "statusCode": 400,
            "body": "Event ignored. Only events from the subject are processed."
        }
    else:
        post_to_bluesky(client, create_positive_sentiment_post(
            event['NewImage']['article_url']))
        logger.info(
            f"Post created successfully for subject: {event['NewImage'].get('subject_name')} with url: {event['NewImage']['article_url']}")
        return {
            "statusCode": 200,
            "body": f"Post created successfully. for subject: {event['NewImage'].get('subject_name')} with url: {event['NewImage']['article_url']}"
        }
