"""Tests for RSS Feed Parser Module."""

import sys
import os
from unittest.mock import patch, MagicMock
import pytest
from rss_parser import extract_story_urls, extract_feeds


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

    @patch('feedparser.parse')
    def test_extract_story_urls_single_feed(self, mock_parse, mock_feed_data):
        mock_parse.return_value = mock_feed_data
        urls = extract_story_urls('http://example.com/feed')
        assert len(urls) == 3
        assert 'http://example.com/story1' in urls

    @patch('feedparser.parse')
    def test_extract_story_urls_with_error(self, mock_parse):
        mock_parse.side_effect = Exception("Feed error")
        urls = extract_story_urls('http://example.com/feed')
        assert urls == []

    @patch('feedparser.parse')
    def test_extract_feeds_single_feed(self, mock_parse, mock_feed_data):
        mock_parse.return_value = mock_feed_data
        urls = extract_feeds(['http://example.com/feed'])
        assert len(urls) == 3

    @patch('feedparser.parse')
    def test_extract_feeds_multiple_feeds(self, mock_parse):
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
        urls = extract_feeds([
            'http://example.com/feed1',
            'http://example.com/feed2'
        ])
        assert len(urls) == 6

    @patch('feedparser.parse')
    def test_extract_feeds_removes_duplicates_within_run(self, mock_parse):
        """Test that duplicates are removed within a single run"""
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

    @patch('feedparser.parse')
    def test_multi_feed_extraction(self, mock_parse):
        def mock_parse_side_effect(url):
            mock = MagicMock()
            mock.entries = []
            if 'bbc' in url:
                mock.entries = [
                    MagicMock(link='http://bbc.com/story1'),
                    MagicMock(link='http://bbc.com/story2')
                ]
            elif 'sky' in url:
                mock.entries = [
                    MagicMock(link='http://sky.com/story1'),
                    MagicMock(link='http://sky.com/story2')
                ]
            return mock

        mock_parse.side_effect = mock_parse_side_effect
        urls = extract_feeds([
            'http://bbc.com/feed',
            'http://sky.com/feed'
        ])
        assert len(urls) == 4

    @patch('feedparser.parse')
    def test_entry_without_link_field(self, mock_parse):
        mock = MagicMock()
        mock.entries = [
            MagicMock(link='http://example.com/story1'),
            MagicMock(title='Story without link', link=None),
            MagicMock(id='http://example.com/story2', link=None)
        ]
        mock_parse.return_value = mock
        urls = extract_story_urls('http://example.com/feed')
        assert len(urls) == 2
