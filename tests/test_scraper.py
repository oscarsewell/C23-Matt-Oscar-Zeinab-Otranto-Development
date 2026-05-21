from bs4 import BeautifulSoup
from scraping.scraper import (
    detect_source,
    extract_title,
    extract_description,
    extract_author,
    extract_publish_date,
    extract_body_text,
    scrape_article,
    scrape_articles
)

BBC_HTML = """
<html>
  <head>
    <meta property="og:title" content="BBC Test Headline">
    <meta name="description" content="BBC test description">
  </head>
  <body>
    <article>
      <div data-testid="single-byline">
        <span>By</span>
        <span>Rachel Clun</span>
        <span>Business reporter</span>
      </div>

      <time data-testid="timestamp" datetime="2026-05-20T06:13:26.521Z">
        20 May 2026
      </time>

      <div data-block="text">
        <p>First BBC paragraph.</p>
        <p>Second BBC paragraph with <b>bold text</b>.</p>
      </div>
    </article>
  </body>
</html>
"""

GUARDIAN_HTML = """
<html>
  <head>
    <meta property="og:title" content="Guardian Test Headline">
    <meta name="description" content="Guardian test description">
  </head>
  <body>
    <article>
      <address data-component="meta-byline">
        <a rel="author">Caroline Davies</a>
        <a rel="author">Jillian Ambrose</a>
      </address>

      <details data-gu-name="dateline">
        <summary>
          <span>Wed 20 May 2026 14.20 BST</span>
        </summary>
      </details>

      <div data-gu-name="body">
        <p>First Guardian paragraph.</p>
        <p>Second Guardian paragraph.</p>
      </div>
    </article>
  </body>
</html>
"""


def test_detect_source_returns_bbc_for_bbc_url():
    assert detect_source(
        "https://www.bbc.co.uk/news/articles/test") == "BBC News"


def test_detect_source_returns_guardian_for_guardian_url():
    assert detect_source(
        "https://www.theguardian.com/politics/test") == "The Guardian"


def test_extract_bbc_title():
    soup = BeautifulSoup(BBC_HTML, "html.parser")

    assert extract_title(soup) == "BBC Test Headline"


def test_extract_guardian_title():
    soup = BeautifulSoup(GUARDIAN_HTML, "html.parser")

    assert extract_title(soup) == "Guardian Test Headline"


def test_extract_bbc_authors_returns_author_list():
    soup = BeautifulSoup(BBC_HTML, "html.parser")

    assert extract_author(soup, "BBC News") == ["Rachel Clun"]


def test_extract_guardian_authors_returns_multiple_authors():
    soup = BeautifulSoup(GUARDIAN_HTML, "html.parser")

    assert extract_author(soup, "The Guardian") == [
        "Caroline Davies",
        "Jillian Ambrose",
    ]


def test_extract_bbc_publish_date_returns_iso_string():
    soup = BeautifulSoup(BBC_HTML, "html.parser")

    assert extract_publish_date(soup, "BBC News") == "2026-05-20T06:13:26.521Z"


def test_extract_guardian_publish_date_returns_iso_string():
    soup = BeautifulSoup(GUARDIAN_HTML, "html.parser")

    assert extract_publish_date(soup, "The Guardian") == "2026-05-20T14:20:00"


def test_extract_bbc_body_text():
    soup = BeautifulSoup(BBC_HTML, "html.parser")

    result = extract_body_text(soup)

    assert "First BBC paragraph." in result
    assert "Second BBC paragraph with bold text." in result


def test_extract_guardian_body_text():
    soup = BeautifulSoup(GUARDIAN_HTML, "html.parser")

    result = extract_body_text(soup)

    assert "First Guardian paragraph." in result
    assert "Second Guardian paragraph." in result


def test_scrape_article_returns_expected_dictionary_for_bbc(monkeypatch):
    def mock_fetch_html(url):
        return BeautifulSoup(BBC_HTML, "html.parser")

    monkeypatch.setattr("scraping.scraper.fetch_html", mock_fetch_html)

    result = scrape_article("https://www.bbc.co.uk/news/articles/test")

    assert result["url"] == "https://www.bbc.co.uk/news/articles/test"
    assert result["source"] == "BBC News"
    assert result["title"] == "BBC Test Headline"
    assert result["authors"] == ["Rachel Clun"]
    assert result["published_at"] == "2026-05-20T06:13:26.521Z"
    assert "First BBC paragraph." in result["body_text"]


def test_scrape_article_returns_expected_dictionary_for_guardian(monkeypatch):
    def mock_fetch_html(url):
        return BeautifulSoup(GUARDIAN_HTML, "html.parser")

    monkeypatch.setattr("scraping.scraper.fetch_html", mock_fetch_html)

    result = scrape_article("https://www.theguardian.com/politics/test")

    assert result["url"] == "https://www.theguardian.com/politics/test"
    assert result["source"] == "The Guardian"
    assert result["title"] == "Guardian Test Headline"
    assert result["authors"] == ["Caroline Davies", "Jillian Ambrose"]
    assert result["published_at"] == "2026-05-20T14:20:00"
    assert "First Guardian paragraph." in result["body_text"]


def test_extract_description_for_bbc():
    soup = BeautifulSoup(BBC_HTML, "html.parser")

    assert extract_description(soup) == "BBC test description"


def test_extract_description_for_guardian():
    soup = BeautifulSoup(GUARDIAN_HTML, "html.parser")

    assert extract_description(soup) == "Guardian test description"


def test_scrape_articles_returns_list_of_scraped_articles(monkeypatch):
    def mock_fetch_html(url):
        if "bbc.co.uk" in url:
            return BeautifulSoup(BBC_HTML, "html.parser")

        if "theguardian.com" in url:
            return BeautifulSoup(GUARDIAN_HTML, "html.parser")

    monkeypatch.setattr("scraping.scraper.fetch_html", mock_fetch_html)

    urls = [
        "https://www.bbc.co.uk/news/articles/test",
        "https://www.theguardian.com/politics/test",
    ]

    result = scrape_articles(urls)

    assert len(result) == 2

    assert result[0]["source"] == "BBC News"
    assert result[0]["title"] == "BBC Test Headline"
    assert result[0]["description"] == "BBC test description"

    assert result[1]["source"] == "The Guardian"
    assert result[1]["title"] == "Guardian Test Headline"
    assert result[1]["description"] == "Guardian test description"
