import unittest
from unittest.mock import Mock, patch, MagicMock
import atproto
from bluesky_functions import (
    login_to_bluesky,
    post_to_bluesky,
    create_positive_sentiment_post,
    create_negative_sentiment_post,
    read_bio,
    is_sentiment_score_valid
)


class TestLoginToBluesky(unittest.TestCase):
    """Test login_to_bluesky function - credential handling and client creation"""

    @patch('bluesky_functions.atproto.Client')
    def test_login_with_valid_credentials(self, mock_client_class):
        """Standard case: Valid credentials should create client and call login"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        result = login_to_bluesky("user@bsky.social", "password123")

        mock_client_class.assert_called_once()
        mock_client_instance.login.assert_called_once_with(
            "user@bsky.social", "password123")
        self.assertEqual(result, mock_client_instance)

    @patch('bluesky_functions.atproto.Client')
    def test_login_with_empty_username(self, mock_client_class):
        """Edge case: Empty username should still attempt login"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        result = login_to_bluesky("", "password123")

        mock_client_instance.login.assert_called_once_with("", "password123")
        self.assertEqual(result, mock_client_instance)

    @patch('bluesky_functions.atproto.Client')
    def test_login_with_empty_password(self, mock_client_class):
        """Edge case: Empty password should still attempt login"""
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance

        result = login_to_bluesky("user@bsky.social", "")

        mock_client_instance.login.assert_called_once_with(
            "user@bsky.social", "")
        self.assertEqual(result, mock_client_instance)

    @patch('bluesky_functions.atproto.Client')
    def test_login_with_network_error(self, mock_client_class):
        """Error case: Network error during login should raise exception"""
        mock_client_instance = Mock()
        mock_client_instance.login.side_effect = ConnectionError(
            "Network unreachable")
        mock_client_class.return_value = mock_client_instance

        with self.assertRaises(ConnectionError):
            login_to_bluesky("user@bsky.social", "password123")


class TestPostToBluesky(unittest.TestCase):
    """Test post_to_bluesky function - content posting"""

    def test_post_with_valid_client_and_content(self):
        """Standard case: Valid client and content should call send_post"""
        mock_client = Mock()
        content = "Hello, Bluesky!"

        post_to_bluesky(mock_client, content)

        mock_client.send_post.assert_called_once_with(content)

    def test_post_with_empty_content(self):
        """Edge case: Empty content string should still attempt to post"""
        mock_client = Mock()

        post_to_bluesky(mock_client, "")

        mock_client.send_post.assert_called_once_with("")

    def test_post_with_very_long_content(self):
        """Edge case: Very long content should still post"""
        mock_client = Mock()
        long_content = "a" * 1000  # 1000 characters

        post_to_bluesky(mock_client, long_content)

        mock_client.send_post.assert_called_once_with(long_content)

    def test_post_with_special_characters(self):
        """Edge case: Content with special characters should post correctly"""
        mock_client = Mock()
        special_content = "Test 🎉 émojis & symbols @user #hashtag"

        post_to_bluesky(mock_client, special_content)

        mock_client.send_post.assert_called_once_with(special_content)

    def test_post_when_client_send_fails(self):
        """Error case: Client send_post failure should raise exception"""
        mock_client = Mock()
        mock_client.send_post.side_effect = Exception("Post failed")

        with self.assertRaises(Exception):
            post_to_bluesky(mock_client, "Hello")

    def test_post_with_none_client(self):
        """Error case: None client should raise AttributeError"""
        with self.assertRaises(AttributeError):
            post_to_bluesky(None, "Hello")


class TestCreatePositiveSentimentPost(unittest.TestCase):
    """Test create_positive_sentiment_post function - positive post formatting"""

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_positive_post_with_valid_url(self, mock_textbuilder_class):
        """Standard case: Valid URL should create formatted positive post"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        result = create_positive_sentiment_post("https://example.com/article")

        mock_textbuilder_class.assert_called_once()
        # Verify sequence of calls
        calls = mock_builder.method_calls
        self.assertEqual(len(calls), 3)  # text, link, text
        self.assertIn("text", str(calls[0]))
        self.assertIn("link", str(calls[1]))
        self.assertIn("text", str(calls[2]))
        self.assertEqual(result, mock_builder)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_positive_post_with_empty_url(self, mock_textbuilder_class):
        """Edge case: Empty URL should still create post"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        result = create_positive_sentiment_post("")

        mock_textbuilder_class.assert_called_once()
        self.assertEqual(result, mock_builder)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_positive_post_with_url_containing_special_characters(self, mock_textbuilder_class):
        """Edge case: URL with special characters should be included"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder
        complex_url = "https://example.com/article?id=123&ref=test#section"

        result = create_positive_sentiment_post(complex_url)

        mock_builder.link.assert_called_with("check it out!", complex_url)
        self.assertEqual(result, mock_builder)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_positive_post_includes_hashtag(self, mock_textbuilder_class):
        """Standard case: Post should include #PositiveVibes hashtag"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        create_positive_sentiment_post("https://example.com")

        # Check that #PositiveVibes is in the final text call
        calls = [str(call) for call in mock_builder.text.call_args_list]
        hashtag_found = any("#PositiveVibes" in call for call in calls)
        self.assertTrue(hashtag_found)


class TestCreateNegativeSentimentPost(unittest.TestCase):
    """Test create_negative_sentiment_post function - negative post formatting"""

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_negative_post_with_valid_inputs(self, mock_textbuilder_class):
        """Standard case: Valid URL and enemy should create formatted negative post"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        result = create_negative_sentiment_post(
            "https://example.com/article", "John Doe")

        mock_textbuilder_class.assert_called_once()
        calls = mock_builder.method_calls
        self.assertEqual(len(calls), 3)  # text, link, text
        self.assertEqual(result, mock_builder)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_negative_post_includes_enemy_name(self, mock_textbuilder_class):
        """Standard case: Enemy name should be included in post text"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder
        enemy = "Elon Musk"

        create_negative_sentiment_post("https://example.com", enemy)

        # Check that enemy name is included in text calls
        text_calls = mock_builder.text.call_args_list
        enemy_found = any(enemy in str(call) for call in text_calls)
        self.assertTrue(enemy_found)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_negative_post_with_empty_enemy(self, mock_textbuilder_class):
        """Edge case: Empty enemy name should still create post"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        result = create_negative_sentiment_post("https://example.com", "")

        mock_textbuilder_class.assert_called_once()
        self.assertEqual(result, mock_builder)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_negative_post_with_empty_url(self, mock_textbuilder_class):
        """Edge case: Empty URL should still create post"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        result = create_negative_sentiment_post("", "John Doe")

        mock_builder.link.assert_called_with("check it out!", "")
        self.assertEqual(result, mock_builder)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_negative_post_includes_epicfail_hashtag(self, mock_textbuilder_class):
        """Standard case: Post should include #EPICFAIL hashtag"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder

        create_negative_sentiment_post("https://example.com", "Enemy")

        calls = [str(call) for call in mock_builder.text.call_args_list]
        hashtag_found = any("#EPICFAIL" in call for call in calls)
        self.assertTrue(hashtag_found)

    @patch('bluesky_functions.atproto.client_utils.TextBuilder')
    def test_negative_post_with_special_characters_in_enemy(self, mock_textbuilder_class):
        """Edge case: Special characters in enemy name should be included"""
        mock_builder = Mock()
        mock_textbuilder_class.return_value = mock_builder
        enemy = "O'Reilly & Associates"

        create_negative_sentiment_post("https://example.com", enemy)

        text_calls = mock_builder.text.call_args_list
        enemy_found = any(enemy in str(call) for call in text_calls)
        self.assertTrue(enemy_found)


class TestReadBio(unittest.TestCase):
    """Test read_bio function - profile bio retrieval"""

    def test_read_bio_with_valid_username(self):
        """Standard case: Valid username should return profile description"""
        mock_client = Mock()
        mock_profile = Mock()
        mock_profile.description = "This is my bio"
        mock_client.get_profile.return_value = mock_profile

        result = read_bio(mock_client, "user.bsky.social")

        mock_client.get_profile.assert_called_once_with("user.bsky.social")
        self.assertEqual(result, "This is my bio")

    def test_read_bio_with_empty_description(self):
        """Edge case: Profile with empty bio should return empty string"""
        mock_client = Mock()
        mock_profile = Mock()
        mock_profile.description = ""
        mock_client.get_profile.return_value = mock_profile

        result = read_bio(mock_client, "user.bsky.social")

        self.assertEqual(result, "")

    def test_read_bio_with_very_long_bio(self):
        """Edge case: Very long bio should be returned as-is"""
        mock_client = Mock()
        mock_profile = Mock()
        long_bio = "x" * 500
        mock_profile.description = long_bio
        mock_client.get_profile.return_value = mock_profile

        result = read_bio(mock_client, "user.bsky.social")

        self.assertEqual(result, long_bio)

    def test_read_bio_with_special_characters(self):
        """Edge case: Bio with special characters and emoji should be returned"""
        mock_client = Mock()
        mock_profile = Mock()
        special_bio = "Hi! 👋 I'm @user. Follow me #blockchain 🚀"
        mock_profile.description = special_bio
        mock_client.get_profile.return_value = mock_profile

        result = read_bio(mock_client, "user.bsky.social")

        self.assertEqual(result, special_bio)

    def test_read_bio_with_network_error(self):
        """Error case: Network error should raise exception"""
        mock_client = Mock()
        mock_client.get_profile.side_effect = ConnectionError("Network error")

        with self.assertRaises(ConnectionError):
            read_bio(mock_client, "user.bsky.social")

    def test_read_bio_with_none_description(self):
        """Edge case: Profile with None description should return None"""
        mock_client = Mock()
        mock_profile = Mock()
        mock_profile.description = None
        mock_client.get_profile.return_value = mock_profile

        result = read_bio(mock_client, "user.bsky.social")

        self.assertIsNone(result)


class TestIsSentimentScoreValid(unittest.TestCase):
    """Test is_sentiment_score_valid function - score validation"""

    def test_valid_score_above_threshold(self):
        """Standard case: Valid score above threshold"""
        self.assertTrue(is_sentiment_score_valid(4.5, 4.0))

    def test_valid_score_at_threshold(self):
        """Edge case: Score exactly at threshold"""
        self.assertTrue(is_sentiment_score_valid(4.0, 4.0))

    def test_valid_score_at_max(self):
        """Edge case: Score at maximum (5.0)"""
        self.assertTrue(is_sentiment_score_valid(5.0, 0.0))

    def test_valid_score_at_min(self):
        """Edge case: Score at minimum (0.0)"""
        self.assertTrue(is_sentiment_score_valid(0.0, 0.0))

    def test_valid_integer_score(self):
        """Edge case: Integer score should be valid"""
        self.assertTrue(is_sentiment_score_valid(4, 4.0))

    def test_score_below_threshold(self):
        """Standard case: Score below threshold"""
        self.assertFalse(is_sentiment_score_valid(3.5, 4.0))

    def test_score_below_min_range(self):
        """Edge case: Score below 0"""
        self.assertFalse(is_sentiment_score_valid(-0.1, 0.0))

    def test_score_above_max_range(self):
        """Edge case: Score above 5"""
        self.assertFalse(is_sentiment_score_valid(5.1, 0.0))

    def test_score_is_not_numeric(self):
        """Error case: Non-numeric score should be invalid"""
        self.assertFalse(is_sentiment_score_valid("4.5", 4.0))

    def test_score_is_none(self):
        """Error case: None score should be invalid"""
        self.assertFalse(is_sentiment_score_valid(None, 4.0))


if __name__ == '__main__':
    unittest.main()
