from bluesky_functions import login_to_bluesky, is_sentiment_score_valid, create_positive_sentiment_post, create_negative_sentiment_post, read_bio, post_to_bluesky
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file


def lambda_handler(event, context):
    """AWS Lambda handler function to process incoming events"""

    if not is_sentiment_score_valid(event['NewImage']['sentiment_score'], threshold=0):
        return {
            "statusCode": 400,
            "body": "Invalid sentiment score. Must be a float above 3.5."
        }
    if not event['eventName'] == 'INSERT':
        return {
            "statusCode": 400,
            "body": "Event ignored. Only INSERT events are processed."
        }

    client = login_to_bluesky(os.environ.get("BLUESKY_HANDLE"),
                              os.environ.get("BLUESKY_APP_PASSWORD"))
    if event.get("subject_name") != read_bio(client, os.environ.get("BLUESKY_HANDLE")):

        return {
            "statusCode": 400,
            "body": "Event ignored. Only events from the subject are processed."
        }
    else:
        post_to_bluesky(client, create_positive_sentiment_post(
            event['NewImage']['article_url']))
        return {
            "statusCode": 200,
            "body": f"Post created successfully. for subject: {event['NewImage'].get('subject_name')} with url: {event['NewImage']['article_url']}"
        }
