import openai as oa
import os
import json
from dotenv import load_dotenv
import logging
from decimal import Decimal
import boto3

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

prompt = """
You are an expert data analyst specializing in Natural Language Processing (NLP), sentiment analysis, and data enrichment.

Analyze the text provided at the end of this prompt and return the results strictly as a valid JSON object. Do not include any conversational intro or outro text. Use the exact JSON structure defined below:

{
  "sentiment_analysis": {
    "score": 0.0, 
    "classification": "string",
    "justification": "string"
  },
  "subjects": ["string"],
  "keywords": ["string"]
}

Strictly adhere to the following rules for the data fields:
1. **score**: A float value from 0.0 to 5.0 rounded to 1 decimal place.(0.0 = extremely negative, 5.0 = extremely positive).
2. **classification**: Map the score using these precise boundaries:
   - 0.0 to 0.99: "very negative"
   - 1.0 to 1.99: "negative"
   - 2.0 to 2.99: "neutral"
   - 3.0 to 3.99: "positive"
   - 4.0 to 5.00: "very positive"
3. **justification**: A single, concise sentence explaining why this sentiment score was chosen.
4. **subjects**: Extract all people and companies. 
   - For individuals: Must include both first and last name. If the text only provides a surname (e.g., "Mr. Smith"), use context to find the first name, or omit if it cannot be verified.
   - For companies: Must use full legal or trade names (e.g., "Apple Inc." or "Microsoft", no acronyms like "MSFT").
5. **keywords**: A flat array of 5 to 20 lowercase keywords capturing general topics, locations, and overarching themes to assist in future aggregation.
"""


def get_llm_client(api_key: str) -> oa.OpenAI:
    """Initialize and return the OpenAI client with the provided API key."""
    logger.info("Initializing OpenAI client.")
    try:
        if not api_key:
            raise ValueError("API key is required to initialize OpenAI client")
        client = oa.OpenAI(api_key=api_key)
        logger.info("OpenAI client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
        raise


def analyze_text(client: oa.OpenAI, text: str) -> dict:
    """Analyze the given text using the OpenAI client and return the results as a dictionary."""

    try:
        logger.info("Analyzing article with OpenAI client.")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": f"This is your text to analyze: {text}"
                }
            ],
            max_tokens=1000
        )
        logger.info("Article analysis completed successfully.")
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Failed to analyze text: {e}")
        raise


def validate_enriched_data(enriched_data: dict) -> bool:
    """Validate the enriched data against the expected structure and types."""
    try:
        sa = enriched_data["sentiment_analysis"]
        if not (0.0 <= sa["score"] <= 5.0):
            return False
        if sa["classification"] not in ["very negative", "negative", "neutral", "positive", "very positive"]:
            return False
        if not isinstance(sa["justification"], str):
            return False

        if not isinstance(enriched_data["subjects"], list) or not all(isinstance(s, str) for s in enriched_data["subjects"]):
            return False

        if not isinstance(enriched_data["keywords"], list) or not all(isinstance(k, str) for k in enriched_data["keywords"]):
            return False

        return True
    except KeyError:
        return False


def get_dynamodb_items(enriched_data: dict, article_data: dict) -> list[dict]:
    """Combine enriched data and article data into a format suitable for DynamoDB insertion."""
    items = []
    for subject in enriched_data["subjects"]:
        item = {
            "subject_name": subject,
            "published_at_article_url": article_data["published_at"]+'_'+article_data["url"],
            "sentiment_score": Decimal(str(enriched_data["sentiment_analysis"]["score"])),
            "sentiment_classification": enriched_data["sentiment_analysis"]["classification"],
            "justification": enriched_data["sentiment_analysis"]["justification"],
            "keywords": enriched_data.get("keywords"),
            "article_title": article_data["title"],
            "article_url": article_data["url"],
            "authors": article_data["authors"],
            "published_at": article_data["published_at"]

        }
        items.append(item)
    return items


def upload_to_dynamodb(articles_data: list[dict]):
    """Upload the given items to DynamoDB."""
    try:
        logger.info("Uploading data to DynamoDB.")
        dynamodb = boto3.resource('dynamodb')
        table_name = os.getenv("DYNAMODB_TABLE")
        if not table_name:
            raise ValueError("DYNAMODB_TABLE environment variable not set")
        table = dynamodb.Table(table_name)
        with table.batch_writer() as batch:
            for item in articles_data:
                batch.put_item(Item=item)
        logger.info("Data uploaded to DynamoDB successfully.")
    except Exception as e:
        logger.error(f"Failed to upload data to DynamoDB: {e}")
        raise
