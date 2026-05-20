"""RSS Feed Parser script"""

from typing import List
import logging
import feedparser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_story_urls(feed_url: str) -> List[str]:
    """Extract story URLs from a single RSS feed"""
    if not feed_url or not isinstance(feed_url, str):
        raise ValueError("feed_url must be a non-empty string")

    try:
        logger.info(f"Fetching feed: {feed_url}")
        parsed_feed = feedparser.parse(feed_url)

        urls = []
        for entry in parsed_feed.entries:
            url = getattr(entry, 'link', None) or getattr(entry, 'id', None)
            if url and isinstance(url, str):
                urls.append(url)

        logger.info(f"Extracted {len(urls)} URLs from {feed_url}")
        return urls

    except Exception as e:
        logger.error(f"Error fetching feed {feed_url}: {str(e)}")
        return []


def extract_feeds(feed_urls: List[str]) -> List[str]:
    """Extract story URLs from multiple RSS feeds, removing duplicates within this run"""
    if not isinstance(feed_urls, list):
        raise ValueError("feed_urls must be a list")

    if len(feed_urls) == 0:
        raise ValueError("feed_urls cannot be empty")

    if not all(isinstance(url, str) for url in feed_urls):
        raise TypeError("All items in feed_urls must be strings")

    all_urls = []
    for feed_url in feed_urls:
        urls = extract_story_urls(feed_url)
        all_urls.extend(urls)

    unique_urls = list(set(all_urls))
    logger.info(
        f"Extracted {len(unique_urls)} unique URLs from {len(feed_urls)} feeds")

    return unique_urls
