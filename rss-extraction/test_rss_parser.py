"""Tests for RSS Feed Parser Module."""

import sys
import os
import json
from unittest.mock import patch, MagicMock
import pytest
import requests
from rss_parser import (
    extract_story_urls,
    extract_feeds,
    get_cached_headers,
    update_cached_headers,
    get_cached_urls,
    update_cached_urls,
    get_new_urls,
    make_conditional_request,
    get_cache_key
)


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def mock_feed_data():
    mock = MagicMock()
    mock.entries = [
        MagicMock(link='http://example.com/story1'),
        MagicMock(link='http://example.com/story2'),
        MagicMock(id='http://example.com/story3')
    ]
    mock.entries[2].link = None
    return mock


class TestExtraction:
    """URL extraction tests."""

    @patch('rss_parser.get_cached_headers')
    @patch('rss_parser.make_conditional_request')
    @patch('feedparser.parse')
    def test_extract_story_urls_single_feed(self, mock_parse, mock_conditional, mock_cache, mock_feed_data):
        mock_cache.return_value = {}
        mock_parse_result = MagicMock()
        mock_parse_result.entries = [
            MagicMock(link='http://example.com/story1'),
            MagicMock(link='http://example.com/story2'),
            MagicMock(id='http://example.com/story3')
        ]
        mock_parse_result.entries[2].link = None
        mock_parse.return_value = mock_parse_result
        mock_conditional.return_value = (
            '<rss>content</rss>', 'etag1', 'Mon, 01 Jan 2024', True)

        urls = extract_story_urls('http://example.com/feed')
        assert len(urls) == 3
        assert 'http://example.com/story1' in urls

    @patch('rss_parser.get_cached_headers')
    @patch('rss_parser.make_conditional_request')
    def test_extract_story_urls_with_error(self, mock_conditional, mock_cache):
        mock_cache.return_value = {}
        mock_conditional.return_value = (None, None, None, False)

        urls = extract_story_urls('http://example.com/feed')
        assert urls == []

    @patch('rss_parser.get_cached_headers')
    @patch('rss_parser.make_conditional_request')
    @patch('feedparser.parse')
    def test_extract_feeds_multiple_feeds(self, mock_parse, mock_conditional, mock_cache):
        mock_cache.return_value = {}

        mock1 = MagicMock()
        mock1.entries = [
            MagicMock(link='http://example.com/story1'),
            MagicMock(link='http://example.com/story2'),
            MagicMock(id='http://example.com/story3')
        ]
        mock1.entries[2].link = None

        mock2 = MagicMock()
        mock2.entries = [
            MagicMock(link='http://example.com/story4'),
            MagicMock(link='http://example.com/story5'),
            MagicMock(id='http://example.com/story6')
        ]
        mock2.entries[2].link = None

        mock_parse.side_effect = [mock1, mock2]
        mock_conditional.side_effect = [
            ('<rss>content1</rss>', 'etag1', 'Mon, 01 Jan 2024', True),
            ('<rss>content2</rss>', 'etag2', 'Tue, 02 Jan 2024', True)
        ]

        urls = extract_feeds([
            'http://example.com/feed1',
            'http://example.com/feed2'
        ])
        assert len(urls) == 6

    @patch('rss_parser.get_cached_headers')
    @patch('rss_parser.make_conditional_request')
    @patch('feedparser.parse')
    def test_extract_feeds_removes_duplicates_within_run(self, mock_parse, mock_conditional, mock_cache):
        mock_cache.return_value = {}

        mock1 = MagicMock()
        mock1.entries = [
            MagicMock(link='http://example.com/story1'),
            MagicMock(link='http://example.com/story2')
        ]

        mock2 = MagicMock()
        mock2.entries = [
            MagicMock(link='http://example.com/story2'),  # Duplicate story
            MagicMock(link='http://example.com/story3')
        ]

        mock_parse.side_effect = [mock1, mock2]
        mock_conditional.side_effect = [
            ('<rss>content1</rss>', 'etag1', 'Mon, 01 Jan 2024', True),
            ('<rss>content2</rss>', 'etag2', 'Tue, 02 Jan 2024', True)
        ]

        urls = extract_feeds([
            'http://example.com/feed1',
            'http://example.com/feed2'
        ])

        assert len(urls) == 3
        assert 'http://example.com/story1' in urls
        assert 'http://example.com/story2' in urls
        assert 'http://example.com/story3' in urls

    def test_extract_feeds_invalid_input_not_list(self):
        with pytest.raises(ValueError, match="feed_urls must be a list"):
            extract_feeds('http://example.com/feed')

    def test_extract_feeds_invalid_input_empty_list(self):
        with pytest.raises(ValueError, match="feed_urls cannot be empty"):
            extract_feeds([])

    def test_extract_feeds_invalid_input_non_string_item(self):
        with pytest.raises(TypeError, match="All items in feed_urls must be strings"):
            extract_feeds(['http://example.com/feed', 123])

    def test_extract_story_urls_invalid_url_empty_string(self):
        with pytest.raises(ValueError, match="feed_url must be a non-empty string"):
            extract_story_urls('')

    def test_extract_story_urls_invalid_url_none(self):
        with pytest.raises(ValueError, match="feed_url must be a non-empty string"):
            extract_story_urls(None)

    def test_extract_story_urls_invalid_url_not_string(self):
        with pytest.raises(ValueError, match="feed_url must be a non-empty string"):
            extract_story_urls(123)


class TestIntegration:
    """Integration tests."""

    @patch('rss_parser.get_cached_headers')
    @patch('rss_parser.make_conditional_request')
    @patch('feedparser.parse')
    def test_entry_without_link_field(self, mock_parse, mock_conditional, mock_cache):
        mock_cache.return_value = {}
        mock = MagicMock()
        mock.entries = [
            MagicMock(link='http://example.com/story1'),
            MagicMock(title='Story without link', link=None),
            MagicMock(id='http://example.com/story2', link=None)
        ]
        mock_parse.return_value = mock
        mock_conditional.return_value = (
            '<rss>content</rss>', 'etag1', 'Mon, 01 Jan 2024', True)

        urls = extract_story_urls('http://example.com/feed')
        assert len(urls) == 2


class TestCaching:
    """S3 caching functionality tests."""

    @patch('rss_parser.s3_client')
    def test_get_cached_headers_cache_hit(self, mock_s3):
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'{"etag": "abc123", "last_modified": "Mon, 01 Jan 2024"}')
        }

        headers = get_cached_headers('http://example.com/feed')

        assert headers['etag'] == 'abc123'
        assert headers['last_modified'] == 'Mon, 01 Jan 2024'
        mock_s3.get_object.assert_called_once()

    @patch('rss_parser.s3_client')
    def test_get_cached_headers_cache_miss(self, mock_s3):
        mock_s3.get_object.side_effect = Exception('NoSuchKey')

        headers = get_cached_headers('http://example.com/feed')

        assert headers == {}

    @patch('rss_parser.s3_client')
    def test_update_cached_headers_success(self, mock_s3):
        mock_s3.put_object.return_value = {}

        result = update_cached_headers(
            'http://example.com/feed',
            'new-etag-123',
            'Tue, 02 Jan 2024'
        )

        assert result is True
        mock_s3.put_object.assert_called_once()

    @patch('rss_parser.s3_client')
    def test_update_cached_headers_s3_error(self, mock_s3):
        mock_s3.put_object.side_effect = Exception('S3 Error')

        result = update_cached_headers(
            'http://example.com/feed',
            'etag',
            'last_modified'
        )

        assert result is False

    @patch('rss_parser.requests.get')
    def test_make_conditional_request_304_not_modified(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 304
        mock_get.return_value = mock_response

        content, etag, last_modified, is_modified = make_conditional_request(
            'http://example.com/feed',
            'old-etag',
            'Mon, 01 Jan 2024'
        )

        assert content is None
        assert etag == 'old-etag'
        assert last_modified == 'Mon, 01 Jan 2024'
        assert is_modified is False

    @patch('rss_parser.requests.get')
    def test_make_conditional_request_200_with_new_content(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<rss><channel><item><link>url</link></item></channel></rss>'
        mock_response.headers = {
            'ETag': 'new-etag-456',
            'Last-Modified': 'Tue, 02 Jan 2024'
        }
        mock_get.return_value = mock_response

        content, etag, last_modified, is_modified = make_conditional_request(
            'http://example.com/feed',
            None,
            None
        )

        assert content is not None
        assert etag == 'new-etag-456'
        assert last_modified == 'Tue, 02 Jan 2024'
        assert is_modified is True

    @patch('rss_parser.requests.get')
    def test_make_conditional_request_network_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException(
            'Network error')

        content, etag, last_modified, is_modified = make_conditional_request(
            'http://example.com/feed',
            'etag',
            'last_modified'
        )

        assert content is None
        assert etag is None
        assert last_modified is None
        assert is_modified is False

    @patch('rss_parser.make_conditional_request')
    @patch('rss_parser.get_cached_headers')
    def test_extract_story_urls_with_cache_hit_304_not_modified(
        self,
        mock_get_cache,
        mock_conditional_req
    ):
        mock_get_cache.return_value = {
            'etag': 'old-etag',
            'last_modified': 'Mon, 01 Jan 2024'
        }

        mock_conditional_req.return_value = (
            None,
            'old-etag',
            'Mon, 01 Jan 2024',
            False
        )

        urls = extract_story_urls('http://example.com/feed')

        assert urls == []

    @patch('rss_parser.make_conditional_request')
    @patch('rss_parser.get_cached_headers')
    def test_extract_story_urls_request_error_returns_empty(
        self,
        mock_get_cache,
        mock_conditional_req
    ):
        mock_get_cache.return_value = {}

        mock_conditional_req.return_value = (
            None,
            None,
            None,
            False
        )

        urls = extract_story_urls('http://example.com/feed')

        assert urls == []

    def test_get_cache_key_consistency(self):
        feed_url = 'http://example.com/feed'
        key1 = get_cache_key(feed_url)
        key2 = get_cache_key(feed_url)

        assert key1 == key2

    def test_get_cache_key_different_urls(self):
        key1 = get_cache_key('http://example.com/feed1')
        key2 = get_cache_key('http://example.com/feed2')

        assert key1 != key2

    @patch('rss_parser.s3_client', None)
    @patch('rss_parser.make_conditional_request')
    def test_offline_mode_when_s3_unavailable(self, mock_conditional_req):
        mock_parse_result = MagicMock()
        mock_parse_result.entries = []

        mock_conditional_req.return_value = (
            '<rss></rss>',
            None,
            None,
            True
        )

        headers = get_cached_headers('http://example.com/feed')
        assert headers == {}

    @patch('rss_parser.s3_client')
    def test_get_cached_headers_malformed_json(self, mock_s3):
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'invalid json')
        }

        headers = get_cached_headers('http://example.com/feed')
        assert headers == {}

    @patch('rss_parser.s3_client')
    def test_get_cached_headers_other_s3_error(self, mock_s3):
        mock_s3.get_object.side_effect = Exception('S3 error')

        headers = get_cached_headers('http://example.com/feed')
        assert headers == {}

    @patch('rss_parser.make_conditional_request')
    @patch('rss_parser.get_cached_headers')
    @patch('feedparser.parse')
    def test_extract_story_urls_cache_update_failure(self, mock_parse, mock_get_cache, mock_conditional):
        mock_get_cache.return_value = {}
        mock_parse_result = MagicMock()
        mock_parse_result.entries = [
            MagicMock(link='http://example.com/story1')]
        mock_parse.return_value = mock_parse_result
        mock_conditional.return_value = (
            '<rss>content</rss>', 'etag', 'last_modified', True)
        with patch('rss_parser.update_cached_headers', return_value=False):
            urls = extract_story_urls('http://example.com/feed')
            assert len(urls) == 1
            assert urls[0] == 'http://example.com/story1'

    @patch('rss_parser.s3_client')
    def test_get_cached_urls_cache_hit(self, mock_s3):
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=lambda: b'{"urls": ["http://example.com/story1", "http://example.com/story2"]}')
        }

        urls = get_cached_urls('http://example.com/feed')

        assert len(urls) == 2
        assert 'http://example.com/story1' in urls
        mock_s3.get_object.assert_called_once()

    @patch('rss_parser.s3_client')
    def test_get_cached_urls_cache_miss(self, mock_s3):
        mock_s3.get_object.side_effect = Exception('NoSuchKey')

        urls = get_cached_urls('http://example.com/feed')

        assert urls == []

    @patch('rss_parser.s3_client')
    def test_update_cached_urls_success(self, mock_s3):
        mock_s3.put_object.return_value = {}

        result = update_cached_urls(
            'http://example.com/feed',
            ['http://example.com/story1', 'http://example.com/story2']
        )

        assert result is True
        mock_s3.put_object.assert_called_once()

    @patch('rss_parser.s3_client')
    def test_update_cached_urls_s3_error(self, mock_s3):
        mock_s3.put_object.side_effect = Exception('S3 Error')

        result = update_cached_urls(
            'http://example.com/feed',
            ['http://example.com/story1']
        )

        assert result is False

    def test_get_new_urls_all_new(self):
        with patch('rss_parser.get_cached_urls', return_value=[]):
            new_urls = get_new_urls(
                'http://example.com/feed',
                ['http://example.com/story1', 'http://example.com/story2']
            )
            assert len(new_urls) == 2

    def test_get_new_urls_some_new(self):
        with patch('rss_parser.get_cached_urls', return_value=['http://example.com/story1']):
            new_urls = get_new_urls(
                'http://example.com/feed',
                ['http://example.com/story1', 'http://example.com/story2']
            )
            assert len(new_urls) == 1
            assert 'http://example.com/story2' in new_urls

    def test_get_new_urls_none_new(self):
        with patch('rss_parser.get_cached_urls', return_value=['http://example.com/story1', 'http://example.com/story2']):
            new_urls = get_new_urls(
                'http://example.com/feed',
                ['http://example.com/story1', 'http://example.com/story2']
            )
            assert new_urls == []
