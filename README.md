# Otranto Development News Feed Project

An automated AI-powered media intelligence platform built using AWS, Docker, Terraform, and Streamlit.

The system ingests RSS feeds, scrapes news articles, enriches them using AI analysis, stores structured data in DynamoDB, visualises insights through a dashboard, and generates automated social media posts.

## Features

- RSS feed ingestion
- Article scraping
- AI sentiment analysis
- Keyword and entity extraction
- DynamoDB storage
- Streamlit analytics dashboard
- Automated BlueSky posting
- Dockerised services
- Terraform infrastructure

## Project Structure

```
text
dashboard/
enrichment/
rss-extraction/
scraping/
social-posting/
Terraform/
tests/
```

## Project Structure

Run "cp .env.example .env"
Fill in the required environment variables locally

## Documentation

Each service contains it's own README with detailed setup and usage instructions.


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
        "sentiment_score"
        "sentiment_classification"
        "justification"
        "keywords"
        "article_title"
        "article_url"
        "authors"
        "published_at"

Querying in this schema:
- This schema allows for queries specifying subject_name and range of dates. 
    Further refinement can be completed using pandas or other data analysis tools after extraction.