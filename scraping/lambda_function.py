from scraping.scraper import scrape_articles


def lambda_handler(event, context):
    urls = event.get("urls", [])

    if not urls:
        return {
            "articles": [],
            "error": "No URLs provided"
        }

    articles = scrape_articles(urls)

    return {
        "articles": articles,
    }
