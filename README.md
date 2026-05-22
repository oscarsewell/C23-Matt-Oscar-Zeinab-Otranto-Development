# Otranto Development News Feed Project

## Environment Variables Template

run ```cp .env.example .env``` and then fill in the values locally


## Scraper

Pass list of strings of urls to scrape_articles()

Input: List of strings (links to pages to scrape)
Output: List of dictionaries

## DynamoDB

### Schema 

- Primary key:
    Consisting of:
        Hash Key
            "subject_name": string type
        Range Key
            "published_at_article_url": string type
- These are the only mandatory Attributes

- Optional Attributes:
    Consisting of:
        "sentiment_score": decimal type
        "sentiment_classification": string type
        "justification": string type
        "keywords": [string types]
        "article_title": string
        "article_url": string
        "authors": [string types]
        "published_at": string

Querying in this schema:
- This schema allows for queries specifying subject_name and range of dates. 
    Further refinement can be completed using pandas or other data analysis tools after extraction.