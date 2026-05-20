import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


def scrape_articles(urls):
    articles = []
    for url in urls:
        article_data = scrape_article(url)
        articles.append(article_data)
    return articles


def fetch_html(url):

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def extract_title(soup):
    title = soup.find("meta", property="og:title")

    if title:
        return title.get("content")

    if soup.title:
        return soup.title.text.strip()

    return None


def extract_description(soup):
    description = soup.find("meta", property="og:description")

    if description:
        return description.get("content")

    meta_description = soup.find("meta", attrs={"name": "description"})

    if meta_description:
        return meta_description.get("content")

    return None


def extract_author(soup, source):

    if source == "BBC News":
        byline = soup.find(
            "div",
            attrs={"data-testid": "single-byline"}
        )

        if byline:

            spans = byline.find_all("span")

            for span in spans:
                text = span.get_text(strip=True)

                if (text and text.lower() != "by" and "reporter" not in text.lower()):
                    return [text]

    elif source == "The Guardian":
        authors = soup.find_all("a", rel="author")

        if authors:
            return [
                author.get_text(strip=True)
                for author in authors
                if author.get_text(strip=True)
            ]

    return []


def extract_publish_date(soup, source):
    if source == "BBC News":
        timestamp = soup.find("time", attrs={"data-testid": "timestamp"})

        if timestamp:
            return timestamp.get("datetime")

    elif source == "The Guardian":
        dateline = soup.find("details", attrs={"data-gu-name": "dateline"})

        if dateline:
            span = dateline.find("span")
            if span:
                raw_date = span.get_text(strip=True)

                try:
                    formatted_date = datetime.strptime(
                        raw_date, "%a %d %b %Y %H.%M BST")
                    return formatted_date.isoformat()
                except ValueError:
                    return raw_date

    return None


def extract_body_text(soup):
    article = soup.find("article")

    if not article:
        return None

    paragraphs = article.find_all("p")

    text_parts = []

    for paragraph in paragraphs:
        text = paragraph.get_text(" ", strip=True)
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)

        if text:
            text_parts.append(text)

    return "\n\n".join(text_parts)


def scrape_article(url):
    soup = fetch_html(url)
    source = detect_source(url)

    article_data = {
        "title": extract_title(soup),
        "description": extract_description(soup),
        "authors": extract_author(soup, source),
        "published_at": extract_publish_date(soup, source),
        "body_text": extract_body_text(soup),
        "source": source,
        "url": url,
    }

    return article_data


def detect_source(url):
    if "bbc.co.uk" in url or "bbc.com" in url:
        return "BBC News"
    if "theguardian.com" in url:
        return "The Guardian"
    return "Unknown"
