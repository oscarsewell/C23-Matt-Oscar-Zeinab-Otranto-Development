from scraping.lambda_function import lambda_handler


def test_lambda_handler_returns_400_when_no_urls_provided():
    result = lambda_handler({}, None)

    assert result["error"] == "No URLs provided"
    assert result["s3_bucket"] == "c23-smearbot-caching-bucket"
    assert result["articles_count"] == 0


def test_lambda_handler_returns_articles(monkeypatch):
    def mock_scrape_articles(urls):
        return [
            {"title": "Test Article", "url": urls[0]}
        ]

    def mock_put_object(**kwargs):
        pass

    monkeypatch.setattr(
        "scraping.lambda_function.scrape_articles", mock_scrape_articles)
    monkeypatch.setattr(
        "scraping.lambda_function.s3_client.put_object", mock_put_object)

    result = lambda_handler(
        {"urls": ["https://www.bbc.co.uk/news/articles/test"]}, None)

    assert result["articles_count"] == 1
    assert result["s3_bucket"] == "c23-smearbot-caching-bucket"
    assert "s3_key" in result


def test_lambda_handler_returns_error_when_url_list_empty():
    event = {"urls": []}

    result = lambda_handler(event, None)

    assert result["error"] == "No URLs provided"
    assert result["articles_count"] == 0


def test_lambda_handler_calls_scrape_articles_with_urls(monkeypatch):
    called_with = {}

    def mock_scrape_articles(urls):
        called_with["urls"] = urls
        return []

    monkeypatch.setattr(
        "scraping.lambda_function.scrape_articles", mock_scrape_articles)

    urls = [
        "https://www.bbc.co.uk/news/articles/test",
        "https://www.theguardian.com/politics/test",
    ]

    event = {"urls": urls}

    lambda_handler(event, None)

    assert called_with["urls"] == urls


def test_lambda_handler_returns_multiple_articles(monkeypatch):
    def mock_scrape_articles(urls):
        return [
            {"title": "Article 1", "url": urls[0]},
            {"title": "Article 2", "url": urls[1]},
        ]

    def mock_put_object(**kwargs):
        pass

    monkeypatch.setattr(
        "scraping.lambda_function.scrape_articles",
        mock_scrape_articles
    )
    monkeypatch.setattr(
        "scraping.lambda_function.s3_client.put_object", mock_put_object)

    result = lambda_handler({"urls": ["url-1", "url-2"]}, None)

    assert result["articles_count"] == 2
    assert result["s3_bucket"] == "c23-smearbot-caching-bucket"
    assert "s3_key" in result
