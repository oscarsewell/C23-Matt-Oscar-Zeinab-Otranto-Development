"""AWS Lambda handler for RSS feed extraction and new URL detection"""

import json
import logging
from typing import Any, Dict

from rss_parser import extract_story_urls, get_new_urls, update_cached_urls

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda handler for RSS feed extraction and new URL detection"""
    try:
        if not isinstance(event, dict):
            return error_response(
                400,
                "Event must be a JSON object"
            )

        feed_urls = event.get('feed_urls')
        if not feed_urls:
            return error_response(
                400,
                "Missing required field: feed_urls"
            )

        if not isinstance(feed_urls, list):
            return error_response(
                400,
                "feed_urls must be a list"
            )

        if len(feed_urls) == 0:
            return error_response(
                400,
                "feed_urls cannot be empty"
            )

        if not all(isinstance(url, str) for url in feed_urls):
            return error_response(
                400,
                "All feed URLs must be strings"
            )

        all_new_urls = []
        feeds_processed = 0

        for feed_url in feed_urls:
            try:
                current_urls = extract_story_urls(feed_url)

                new_urls = get_new_urls(feed_url, current_urls)

                if current_urls:
                    update_cached_urls(feed_url, current_urls)

                all_new_urls.extend(new_urls)
                feeds_processed += 1

                logger.info(
                    f"Processed {feed_url}: "
                    f"{len(current_urls)} total, "
                    f"{len(new_urls)} new"
                )

            except Exception as e:
                logger.error(f"Error processing feed {feed_url}: {str(e)}")
                continue

        unique_new_urls = list(set(all_new_urls))

        logger.info(
            f"Lambda execution complete: "
            f"{feeds_processed} feeds processed, "
            f"{len(unique_new_urls)} new unique URLs found"
        )

        return success_response({
            "new_urls": unique_new_urls,
            "feeds_processed": feeds_processed,
            "total_new_urls": len(unique_new_urls),
        })

    except Exception as e:
        logger.error(f"Unhandled error in Lambda handler: {str(e)}")
        return error_response(500, f"Internal server error: {str(e)}")


def success_response(body: Dict[str, Any]) -> Dict[str, Any]:
    """Format and return a successful Lambda response"""
    return body


def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Format and return an error Lambda response"""
    return {
        "error": message,
        "statusCode": status_code
    }
