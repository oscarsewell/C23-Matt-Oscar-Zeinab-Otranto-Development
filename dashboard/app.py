import streamlit as st
import pandas as pd

from data_access import get_all_articles
from transformations import normalise_articles

st.set_page_config(
    page_title="Article Dashboard",
    layout="wide"
)

st.title("Article Dashboard")

raw_articles = get_all_articles()
articles = normalise_articles(raw_articles)

df = pd.DataFrame(articles)

positive_count = len(df[df["sentiment"] == "positive"])
negative_count = len(df[df["sentiment"] == "negative"])
neutral_count = len(df[df["sentiment"] == "neutral"])

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Articles", len(df))
col2.metric("Positive Articles", positive_count)
col3.metric("Negative Articles", negative_count)
col4.metric("Neutral Articles", neutral_count)

if df.empty:
    st.warning("No articles found in the database.")
    st.stop()

st.subheader("Article Data")
st.dataframe(df)

st.subheader("Sentiment Breakdown")
sentiment_counts = df["sentiment"].value_counts()
st.bar_chart(sentiment_counts)

st.subheader("Top Keywords")
all_keywords = []

for keywords in df["keywords"]:
    if isinstance(keywords, list):
        all_keywords.extend(keywords)

keyword_series = pd.Series(all_keywords).value_counts().head(10)
st.bar_chart(keyword_series)

st.sidebar.header("Filter Articles")
sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=df["sentiment"].dropna().unique(),
    default=df["sentiment"].dropna().unique()
)

filtered_df = df[df["sentiment"].isin(sentiment_filter)]

st.subheader("Filtered Articles")
st.dataframe(filtered_df)
