# pylint: disable=logging-fstring-interpolation
"""RSS Feed Parser script with S3-based caching"""

from typing import List, Dict, Optional, Tuple
import logging
import json
import hashlib
import os
from dotenv import load_dotenv
import feedparser
import requests
import boto3
from botocore.exceptions import ClientError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AWS_REGION = os.getenv('AWS_REGION', 'eu-west-2')
S3_BUCKET = os.getenv('S3_CACHING_BUCKET', 'c23-smearbot-caching-bucket')
S3_CACHE_PREFIX = os.getenv('S3_CACHE_PREFIX', 'rss_feed_cache/')

try:
    s3_client = boto3.client('s3', region_name=AWS_REGION)
except Exception as e:
    logger.warning(
        f"Failed to initialize S3 client: {str(e)}. Running in offline mode.")
    s3_client = None


def get_cache_key(feed_url: str) -> str:
    """Generate a cache key for the feed URL"""
    url_hash = hashlib.md5(feed_url.encode()).hexdigest()
    return f"{S3_CACHE_PREFIX}{url_hash}.json"


def get_cached_headers(feed_url: str) -> Dict[str, Optional[str]]:
    """Retrieve cached ETag and Last-Modified headers from S3"""
    if not s3_client:
        return {}

    cache_key = get_cache_key(feed_url)

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=cache_key)
        cache_data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"Retrieved cached headers for {feed_url}")
        return {
            'etag': cache_data.get('etag'),
            'last_modified': cache_data.get('last_modified')
        }
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.debug(f"No cache found for {feed_url}")
        else:
            logger.warning(f"Error retrieving cache for {feed_url}: {str(e)}")
        return {}
    except Exception as e:
        logger.warning(f"Error parsing cache for {feed_url}: {str(e)}")
        return {}


def update_cached_headers(feed_url: str, etag: Optional[str], last_modified: Optional[str]) -> bool:
    """Store ETag and Last-Modified headers in S3"""
    if not s3_client:
        return False

    cache_key = get_cache_key(feed_url)
    cache_data = {
        'feed_url': feed_url,
        'etag': etag,
        'last_modified': last_modified
    }

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=cache_key,
            Body=json.dumps(cache_data),
            ContentType='application/json'
        )
        logger.info(f"Updated cached headers for {feed_url}")
        return True
    except Exception as e:
        logger.error(f"Error updating cache for {feed_url}: {str(e)}")
        return False


def get_cached_urls(feed_url: str) -> List[str]:
    """Retrieve cached URLs from S3"""
    if not s3_client:
        return []

    cache_key = f"{S3_CACHE_PREFIX}urls/{hashlib.md5(feed_url.encode()).hexdigest()}.json"

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET, Key=cache_key)
        cache_data = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"Retrieved cached URLs for {feed_url}")
        return cache_data.get('urls', [])
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            logger.debug(f"No cached URLs found for {feed_url}")
        else:
            logger.warning(
                f"Error retrieving cached URLs for {feed_url}: {str(e)}"
            )
        return []
    except Exception as e:
        logger.warning(f"Error parsing cached URLs for {feed_url}: {str(e)}")
        return []


def update_cached_urls(feed_url: str, urls: List[str]) -> bool:
    """Store extracted URLs in S3"""
    if not s3_client:
        return False

    url_hash = hashlib.md5(feed_url.encode()).hexdigest()
    cache_key = f"{S3_CACHE_PREFIX}urls/{url_hash}.json"
    cache_data = {
        'feed_url': feed_url,
        'urls': urls,
        'timestamp': str(json.dumps(json.loads(json.dumps({'t': 1}))))
    }

    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=cache_key,
            Body=json.dumps(cache_data),
            ContentType='application/json'
        )
        logger.info(f"Cached {len(urls)} URLs for {feed_url}")
        return True
    except Exception as e:
        logger.error(f"Error updating cached URLs for {feed_url}: {str(e)}")
        return False


def get_new_urls(feed_url: str, current_urls: List[str]) -> List[str]:
    """Compare current URLs against cached URLs and return only new ones"""
    cached_urls = get_cached_urls(feed_url)
    cached_set = set(cached_urls)
    new_urls = [url for url in current_urls if url not in cached_set]
    logger.info(
        f"Found {len(new_urls)} new URLs out of {len(current_urls)} total for {feed_url}")
    return new_urls


def make_conditional_request(feed_url: str, etag: Optional[str], last_modified: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], bool]:
    """Make HTTP request with ETag/Last-Modified headers and return content if modified"""
    headers = {
        'User-Agent': 'C23-SmearBot/1.0'
    }

    if etag:
        headers['If-None-Match'] = etag

    if last_modified:
        headers['If-Modified-Since'] = last_modified

    try:
        response = requests.get(feed_url, headers=headers, timeout=10)

        if response.status_code == 304:
            logger.info(f"Feed not modified: {feed_url}")
            return None, etag, last_modified, False

        response.raise_for_status()

        new_etag = response.headers.get('ETag')
        new_last_modified = response.headers.get('Last-Modified')

        logger.info(f"Feed updated: {feed_url}")
        return response.text, new_etag, new_last_modified, True

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching feed {feed_url}: {str(e)}")
        return None, None, None, False


def extract_story_urls(feed_url: str) -> List[str]:
    """Extract story URLs from a single RSS feed with S3-based caching of headers"""
    if not feed_url or not isinstance(feed_url, str):
        raise ValueError("feed_url must be a non-empty string")

    try:
        logger.info(f"Fetching feed: {feed_url}")

        cached_headers = get_cached_headers(feed_url)
        etag = cached_headers.get('etag')
        last_modified = cached_headers.get('last_modified')

        content, new_etag, new_last_modified, is_modified = (
            make_conditional_request(feed_url, etag, last_modified)
        )

        if not is_modified:
            logger.info(f"Feed not modified, skipping parsing: {feed_url}")
            return []

        if content:
            parsed_feed = feedparser.parse(content)

            if new_etag or new_last_modified:
                update_cached_headers(feed_url, new_etag, new_last_modified)

            urls = []
            for entry in parsed_feed.entries:
                url = getattr(entry, 'link', None) or getattr(
                    entry, 'id', None)
                if url and isinstance(url, str):
                    urls.append(url)

            logger.info(f"Extracted {len(urls)} URLs from {feed_url}")
            return urls

        return []

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
