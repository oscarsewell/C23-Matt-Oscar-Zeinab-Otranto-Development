import json
import os
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

from enrichment.enrichment_and_upload import (
    get_llm_client,
    analyze_text,
    validate_enriched_data,
    get_dynamodb_items,
    upload_to_dynamodb,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

VALID_ENRICHED_DATA = {
    "sentiment_analysis": {
        "score": 4.2,
        "classification": "very positive",
        "justification": "The article reports strong financial results."
    },
    "subjects": ["Apple Inc.", "Barry Madeupsman"],
    "keywords": ["apple", "revenue", "technology", "quarterly", "shareholders"]
}

VALID_ARTICLE_DATA = {
    "published_at": "2024-01-01T00:00:00Z",
    "url": "https://example.com/article",
    "title": "Apple's Revenue Soars",
    "authors": ["Jane Doe"],
    "body": "Apple Inc. reported a 20% increase in revenue.",
    "description": "Apple revenue up 20%."
}


# ---------------------------------------------------------------------------
# get_llm_client
# ---------------------------------------------------------------------------

class TestGetLlmClient:

    @patch("chat_gpt_enrichment.oa.OpenAI")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-api-key"})
    def test_returns_openai_client(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        result = get_llm_client()

        mock_openai.assert_called_once_with(api_key="test-api-key")
        assert result is mock_client

    @patch("chat_gpt_enrichment.oa.OpenAI")
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_passes_none(self, mock_openai):
        """os.getenv returns None when key absent; client init receives None."""
        mock_openai.return_value = MagicMock()
        get_llm_client()
        mock_openai.assert_called_once_with(api_key=None)

    @patch("chat_gpt_enrichment.oa.OpenAI", side_effect=Exception("Auth error"))
    @patch.dict(os.environ, {"OPENAI_API_KEY": "bad-key"})
    def test_raises_on_client_init_failure(self, mock_openai):
        with pytest.raises(Exception, match="Auth error"):
            get_llm_client()


# ---------------------------------------------------------------------------
# analyze_text
# ---------------------------------------------------------------------------

class TestAnalyzeText:

    def _make_client(self, output_text: str) -> MagicMock:
        """Build a mock OpenAI client whose responses.create returns output_text."""
        mock_response = MagicMock()
        mock_response.output_text = output_text
        mock_client = MagicMock()
        mock_client.responses.create.return_value = mock_response
        return mock_client

    def test_returns_parsed_dict_on_valid_response(self):
        payload = json.dumps(VALID_ENRICHED_DATA)
        client = self._make_client(payload)

        result = analyze_text(client, "Some article text.")

        assert result == VALID_ENRICHED_DATA

    def test_passes_text_to_api(self):
        payload = json.dumps(VALID_ENRICHED_DATA)
        client = self._make_client(payload)
        text = "Unique article content for test."

        analyze_text(client, text)

        _, kwargs = client.responses.create.call_args
        messages = kwargs.get(
            "input") or client.responses.create.call_args[1]["input"]
        user_message = next(m for m in messages if m["role"] == "user")
        assert text in user_message["content"]

    def test_raises_on_invalid_json_response(self):
        client = self._make_client("This is not JSON at all.")

        with pytest.raises(json.JSONDecodeError):
            analyze_text(client, "Some text.")

    def test_raises_on_api_error(self):
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = Exception("API timeout")

        with pytest.raises(Exception, match="API timeout"):
            analyze_text(mock_client, "Some text.")

    def test_handles_minimal_valid_response(self):
        minimal = {
            "sentiment_analysis": {"score": 2.5, "classification": "neutral", "justification": "Neutral tone."},
            "subjects": [],
            "keywords": []
        }
        client = self._make_client(json.dumps(minimal))
        result = analyze_text(client, "Minimal text.")
        assert result["sentiment_analysis"]["score"] == 2.5

    def test_handles_empty_string_text(self):
        payload = json.dumps(VALID_ENRICHED_DATA)
        client = self._make_client(payload)
        result = analyze_text(client, "")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# validate_enriched_data
# ---------------------------------------------------------------------------

class TestValidateEnrichedData:

    # --- Standard valid cases ---

    def test_valid_data_returns_true(self):
        assert validate_enriched_data(VALID_ENRICHED_DATA) is True

    @pytest.mark.parametrize("classification", [
        "very negative", "negative", "neutral", "positive", "very positive"
    ])
    def test_all_valid_classifications_return_true(self, classification):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {
                **VALID_ENRICHED_DATA["sentiment_analysis"],
                "classification": classification
            }
        }
        assert validate_enriched_data(data) is True

    @pytest.mark.parametrize("score", [0.0, 2.5, 5.0])
    def test_boundary_scores_return_true(self, score):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "score": score}
        }
        assert validate_enriched_data(data) is True

    def test_empty_subjects_list_is_valid(self):
        data = {**VALID_ENRICHED_DATA, "subjects": []}
        assert validate_enriched_data(data) is True

    def test_empty_keywords_list_is_valid(self):
        data = {**VALID_ENRICHED_DATA, "keywords": []}
        assert validate_enriched_data(data) is True

    # --- Score edge cases ---

    def test_score_below_zero_returns_false(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "score": -0.1}
        }
        assert validate_enriched_data(data) is False

    def test_score_above_five_returns_false(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "score": 5.1}
        }
        assert validate_enriched_data(data) is False

    # --- Classification edge cases ---

    def test_invalid_classification_returns_false(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "classification": "great"}
        }
        assert validate_enriched_data(data) is False

    def test_empty_string_classification_returns_false(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "classification": ""}
        }
        assert validate_enriched_data(data) is False

    # --- Justification edge cases ---

    def test_non_string_justification_returns_false(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "justification": 42}
        }
        assert validate_enriched_data(data) is False

    # --- Subjects edge cases ---

    def test_subjects_not_list_returns_false(self):
        data = {**VALID_ENRICHED_DATA, "subjects": "Apple Inc."}
        assert validate_enriched_data(data) is False

    def test_subjects_containing_non_string_returns_false(self):
        data = {**VALID_ENRICHED_DATA, "subjects": ["Apple Inc.", 123]}
        assert validate_enriched_data(data) is False

    # --- Keywords edge cases ---

    def test_keywords_not_list_returns_false(self):
        data = {**VALID_ENRICHED_DATA, "keywords": "apple, revenue"}
        assert validate_enriched_data(data) is False

    def test_keywords_containing_non_string_returns_false(self):
        data = {**VALID_ENRICHED_DATA, "keywords": ["apple", None]}
        assert validate_enriched_data(data) is False

    # --- Missing key edge cases ---

    def test_missing_sentiment_analysis_key_returns_false(self):
        data = {k: v for k, v in VALID_ENRICHED_DATA.items() if k !=
                "sentiment_analysis"}
        assert validate_enriched_data(data) is False

    def test_missing_subjects_key_returns_false(self):
        data = {k: v for k, v in VALID_ENRICHED_DATA.items() if k !=
                "subjects"}
        assert validate_enriched_data(data) is False

    def test_missing_keywords_key_returns_false(self):
        data = {k: v for k, v in VALID_ENRICHED_DATA.items() if k !=
                "keywords"}
        assert validate_enriched_data(data) is False

    def test_missing_score_key_returns_false(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {
                k: v for k, v in VALID_ENRICHED_DATA["sentiment_analysis"].items() if k != "score"
            }
        }
        assert validate_enriched_data(data) is False

    def test_empty_dict_returns_false(self):
        assert validate_enriched_data({}) is False


# ---------------------------------------------------------------------------
# get_dynamodb_items
# ---------------------------------------------------------------------------

class TestGetDynamodbItems:

    def test_returns_one_item_per_subject(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        assert len(result) == len(VALID_ENRICHED_DATA["subjects"])

    def test_item_contains_all_expected_keys(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        expected_keys = {
            "subject", "published_at_article_url", "sentiment_score",
            "sentiment_classification", "justification", "keywords",
            "article_title", "article_url", "authors", "body", "description"
        }
        for item in result:
            assert expected_keys == set(item.keys())

    def test_subject_name_correct(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        subjects = [item["subject"] for item in result]
        assert subjects == VALID_ENRICHED_DATA["subjects"]

    def test_published_at_article_url_is_concatenation(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        expected = VALID_ARTICLE_DATA["published_at"] + \
            VALID_ARTICLE_DATA["url"]
        for item in result:
            assert item["published_at_article_url"] == expected

    def test_sentiment_score_is_decimal(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        for item in result:
            assert isinstance(item["sentiment_score"], Decimal)

    def test_sentiment_score_value_correct(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        for item in result:
            assert item["sentiment_score"] == Decimal("4.2")

    def test_article_metadata_propagated_to_all_items(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        for item in result:
            assert item["article_title"] == VALID_ARTICLE_DATA["title"]
            assert item["article_url"] == VALID_ARTICLE_DATA["url"]
            assert item["authors"] == VALID_ARTICLE_DATA["authors"]
            assert item["body"] == VALID_ARTICLE_DATA["body"]
            assert item["description"] == VALID_ARTICLE_DATA["description"]

    def test_empty_subjects_returns_empty_list(self):
        data = {**VALID_ENRICHED_DATA, "subjects": []}
        result = get_dynamodb_items(data, VALID_ARTICLE_DATA)
        assert result == []

    def test_single_subject_returns_single_item(self):
        data = {**VALID_ENRICHED_DATA, "subjects": ["Apple Inc."]}
        result = get_dynamodb_items(data, VALID_ARTICLE_DATA)
        assert len(result) == 1
        assert result[0]["subject"] == "Apple Inc."

    def test_keywords_propagated_correctly(self):
        result = get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)
        for item in result:
            assert item["keywords"] == VALID_ENRICHED_DATA["keywords"]

    def test_score_precision_preserved(self):
        data = {
            **VALID_ENRICHED_DATA,
            "sentiment_analysis": {**VALID_ENRICHED_DATA["sentiment_analysis"], "score": 3.7}
        }
        result = get_dynamodb_items(data, VALID_ARTICLE_DATA)
        for item in result:
            assert item["sentiment_score"] == Decimal("3.7")


# ---------------------------------------------------------------------------
# upload_to_dynamodb
# ---------------------------------------------------------------------------

class TestUploadToDynamodb:

    def _make_items(self) -> list[dict]:
        return get_dynamodb_items(VALID_ENRICHED_DATA, VALID_ARTICLE_DATA)

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-table"})
    @patch("chat_gpt_enrichment.boto3.resource")
    def test_uploads_all_items(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(
            return_value=False)
        mock_boto3_resource.return_value.Table.return_value = mock_table

        items = self._make_items()
        upload_to_dynamodb(items)

        assert mock_batch.put_item.call_count == len(items)

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-table"})
    @patch("chat_gpt_enrichment.boto3.resource")
    def test_uses_correct_table_name(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=MagicMock())
        mock_table.batch_writer.return_value.__exit__ = MagicMock(
            return_value=False)
        mock_dynamodb = mock_boto3_resource.return_value
        mock_dynamodb.Table.return_value = mock_table

        upload_to_dynamodb(self._make_items())

        mock_dynamodb.Table.assert_called_once_with("test-table")

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-table"})
    @patch("chat_gpt_enrichment.boto3.resource")
    def test_each_item_passed_to_put_item(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(
            return_value=False)
        mock_boto3_resource.return_value.Table.return_value = mock_table

        items = self._make_items()
        upload_to_dynamodb(items)

        put_calls = [c[1]["Item"] for c in mock_batch.put_item.call_args_list]
        for item in items:
            assert item in put_calls

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-table"})
    @patch("chat_gpt_enrichment.boto3.resource")
    def test_empty_items_list_does_not_call_put_item(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(
            return_value=False)
        mock_boto3_resource.return_value.Table.return_value = mock_table

        upload_to_dynamodb([])

        mock_batch.put_item.assert_not_called()

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-table"})
    @patch("chat_gpt_enrichment.boto3.resource", side_effect=Exception("DynamoDB connection error"))
    def test_raises_on_dynamodb_connection_error(self, mock_boto3_resource):
        with pytest.raises(Exception, match="DynamoDB connection error"):
            upload_to_dynamodb(self._make_items())

    @patch.dict(os.environ, {"DYNAMODB_TABLE_NAME": "test-table"})
    @patch("chat_gpt_enrichment.boto3.resource")
    def test_raises_on_put_item_failure(self, mock_boto3_resource):
        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_batch.put_item.side_effect = Exception("Write failed")
        mock_table.batch_writer.return_value.__enter__ = MagicMock(
            return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(
            return_value=False)
        mock_boto3_resource.return_value.Table.return_value = mock_table

        with pytest.raises(Exception, match="Write failed"):
            upload_to_dynamodb(self._make_items())
