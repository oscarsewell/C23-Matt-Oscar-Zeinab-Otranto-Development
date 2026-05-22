def normalise_article(article):
    return {
        "title": article.get("article_title"),
        "url": article.get("article_url"),
        "authors": article.get("authors", []),
        "sentiment": article.get("sentiment_classification"),
        "sentiment_score": float(article.get("sentiment_score", 0)),
        "keywords": article.get("keywords", []),
        "justification": article.get("justification", ""),
    }


def normalise_articles(articles):
    return [normalise_article(article) for article in articles]
