"""Tests for Lambda handler"""

import json
import pytest
from unittest.mock import patch, MagicMock

from lambda_function import lambda_handler, success_response, error_response


class TestLambdaHandler:
    """Tests for Lambda handler entry point"""

    @patch('lambda_function.update_cached_urls')
    @patch('lambda_function.get_new_urls')
    @patch('lambda_function.extract_story_urls')
    def test_handler_valid_input_single_feed(
        self,
        mock_extract,
        mock_get_new,
        mock_update
    ):
        """Test handler with valid single feed"""
        mock_extract.return_value = [
            'http://example.com/story1',
            'http://example.com/story2'
        ]
        mock_get_new.return_value = [
            'http://example.com/story1'
        ]
        mock_update.return_value = True

        event = {
            'feed_urls': ['https://example.com/feed.xml']
        }

        response = lambda_handler(event, None)

        assert response['new_urls'] == ['http://example.com/story1']
        assert response['total_new_urls'] == 1
        assert response['feeds_processed'] == 1

    @patch('lambda_function.update_cached_urls')
    @patch('lambda_function.get_new_urls')
    @patch('lambda_function.extract_story_urls')
    def test_handler_multiple_feeds(
        self,
        mock_extract,
        mock_get_new,
        mock_update
    ):
        """Test handler with multiple feeds"""
        mock_extract.side_effect = [
            ['http://example.com/story1', 'http://example.com/story2'],
            ['http://example.com/story3', 'http://example.com/story4']
        ]
        mock_get_new.side_effect = [
            ['http://example.com/story1'],
            ['http://example.com/story3', 'http://example.com/story4']
        ]
        mock_update.return_value = True

        event = {
            'feed_urls': [
                'https://example.com/feed1.xml',
                'https://example.com/feed2.xml'
            ]
        }

        response = lambda_handler(event, None)

        assert response['feeds_processed'] == 2
        assert response['total_new_urls'] == 3

    def test_handler_missing_feed_urls(self):
        """Test handler with missing feed_urls field"""
        event = {}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        assert 'error' in response
        assert 'feed_urls' in response['error']

    def test_handler_empty_feed_urls(self):
        """Test handler with empty feed_urls list"""
        event = {'feed_urls': []}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        assert 'error' in response

    def test_handler_invalid_feed_urls_type_string(self):
        """Test handler with feed_urls as string instead of list"""
        event = {'feed_urls': 'https://example.com/feed.xml'}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400
        assert 'error' in response

    def test_handler_invalid_feed_urls_type_int(self):
        """Test handler with feed_urls as integer"""
        event = {'feed_urls': 123}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400

    def test_handler_non_string_url_in_list(self):
        """Test handler with non-string URL in feed_urls list"""
        event = {'feed_urls': ['https://example.com/feed.xml', 123]}

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400

    def test_handler_invalid_event_not_dict(self):
        """Test handler with event that is not a dictionary"""
        event = ['not', 'a', 'dict']

        response = lambda_handler(event, None)

        assert response['statusCode'] == 400

    @patch('lambda_function.update_cached_urls')
    @patch('lambda_function.get_new_urls')
    @patch('lambda_function.extract_story_urls')
    def test_handler_one_feed_fails_continues(
        self,
        mock_extract,
        mock_get_new,
        mock_update
    ):
        """Test handler continues when one feed fails"""
        mock_extract.side_effect = [
            Exception("Network error"),
            ['http://example.com/story1']
        ]
        mock_get_new.return_value = ['http://example.com/story1']
        mock_update.return_value = True

        event = {
            'feed_urls': [
                'https://example.com/feed1.xml',
                'https://example.com/feed2.xml'
            ]
        }

        response = lambda_handler(event, None)

        assert response['feeds_processed'] == 1
        assert response['total_new_urls'] == 1

    @patch('lambda_function.update_cached_urls')
    @patch('lambda_function.get_new_urls')
    @patch('lambda_function.extract_story_urls')
    def test_handler_deduplicates_new_urls(
        self,
        mock_extract,
        mock_get_new,
        mock_update
    ):
        """Test handler deduplicates new URLs across feeds"""
        url = 'http://example.com/shared-story'
        mock_extract.side_effect = [
            [url],
            [url]
        ]
        mock_get_new.side_effect = [
            [url],
            [url]
        ]
        mock_update.return_value = True

        event = {
            'feed_urls': [
                'https://example.com/feed1.xml',
                'https://example.com/feed2.xml'
            ]
        }

        response = lambda_handler(event, None)

        assert response['total_new_urls'] == 1

    @patch('lambda_function.update_cached_urls')
    @patch('lambda_function.get_new_urls')
    @patch('lambda_function.extract_story_urls')
    def test_handler_no_new_urls(
        self,
        mock_extract,
        mock_get_new,
        mock_update
    ):
        """Test handler when no new URLs are found"""
        mock_extract.return_value = ['http://example.com/story1']
        mock_get_new.return_value = []
        mock_update.return_value = True

        event = {'feed_urls': ['https://example.com/feed.xml']}

        response = lambda_handler(event, None)

        assert response['total_new_urls'] == 0
        assert response['new_urls'] == []


class TestResponseHelpers:
    """Tests for response helper functions"""

    def test_success_response(self):
        """Test success response formatting"""
        body = {'key': 'value', 'count': 42}

        response = success_response(body)

        assert response == body

    def test_error_response(self):
        """Test error response formatting"""
        response = error_response(404, 'Not found')

        assert response['statusCode'] == 404
        assert response['error'] == 'Not found'

    def test_error_response_500(self):
        """Test error response with 500 status"""
        response = error_response(500, 'Internal server error')

        assert response['statusCode'] == 500
        assert 'error' in response
