from scraping.scraper import scrape_articles
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Starting scraping Lambda")
    urls = event.get("urls", [])

    if not urls:
        logger.warning("No URLs provided")
        return {
            "articles": [],
            "error": "No URLs provided"
        }

    articles = scrape_articles(urls)
    logger.info("Scraping Lambda completed")

    return {
        "articles": articles,
    }
