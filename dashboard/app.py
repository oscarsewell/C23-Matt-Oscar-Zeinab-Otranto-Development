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

st.sidebar.header("Search")

search_term = st.sidebar.text_input("Search for a person or business")

if search_term:
    search_term_lower = search_term.lower()

    filtered_df = df[
        df.apply(
            lambda row: search_term_lower in " ".join(
                [
                    str(row.get("subject", "")),
                ]
            ).lower(),
            axis=1
        )
    ]
else:
    filtered_df = df


if not search_term:
    st.info("Search for a person or business to view detailed insights")

    st.subheader("Overall Article Overview")
    st.metric("Total Unique Articles",
              df.drop_duplicates(subset=["url"]).shape[0])

    st.subheader("Sentiment Distribution")
    st.dataframe(
        df.drop_duplicates(subset=["url"])
        .sort_values("publish_date", ascending=False)
        .head(10)
    )

    st.stop()


st.subheader("Summary")

if not filtered_df.empty:
    avg_sentiment = filtered_df["sentiment_score"].mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("Matching Articles", len(filtered_df))
    col2.metric("Average Sentiment Score", round(avg_sentiment, 2))
    col3.metric("Most Common Sentiment",
                filtered_df["sentiment"].mode()[0])

else:
    st.warning("No articles found in the database.")
    st.stop()

positive_count = len(filtered_df[filtered_df["sentiment"] == "positive"])
negative_count = len(filtered_df[filtered_df["sentiment"] == "negative"])
neutral_count = len(filtered_df[filtered_df["sentiment"] == "neutral"])

col1, col2, col3 = st.columns(3)

col1.metric("Positive Articles", positive_count)
col2.metric("Negative Articles", negative_count)
col3.metric("Neutral Articles", neutral_count)


st.subheader("Sentiment Breakdown")
sentiment_counts = filtered_df["sentiment"].value_counts()
st.bar_chart(sentiment_counts)

filtered_df["publish_date"] = pd.to_datetime(
    filtered_df["publish_date"], errors="coerce")

filtered_df["publish_day"] = (filtered_df["publish_date"].dt.date)

sentiment_over_time = (
    filtered_df
    .dropna(subset=["publish_day"])
    .sort_values("publish_day")
    .groupby("publish_day")["sentiment_score"]
    .mean()
    .round(2)
)

st.subheader("Average Sentiment Over Time")
st.line_chart(sentiment_over_time)

st.subheader("Top Keywords")
all_keywords = []

for keywords in filtered_df["keywords"]:
    if isinstance(keywords, list):
        all_keywords.extend(keywords)

keyword_series = pd.Series(all_keywords).value_counts().head(10)
st.bar_chart(keyword_series)

unique_filtered_df = filtered_df.drop_duplicates(
    subset=["url"], keep="first").reset_index(drop=True)

st.subheader("Most Positive Headlines")

positive_headlines = (
    unique_filtered_df
    .sort_values("sentiment_score", ascending=False)
    .head(5)
)

for _, row in positive_headlines.iterrows():
    st.markdown(
        f"**[{row['title']}]({row['url']})** \n"
        f"Score: `{row['sentiment_score']}` \n"
        f"Sentiment: `{row['sentiment']}`"
    )

st.subheader("Most Negative Headlines")

negative_headlines = (
    unique_filtered_df
    .sort_values("sentiment_score", ascending=True)
    .head(5)
)

for _, row in negative_headlines.iterrows():
    st.markdown(
        f"**[{row['title']}]({row['url']})** \n"
        f"Score: `{row['sentiment_score']}` \n"
        f"Sentiment: `{row['sentiment']}`"
    )

st.sidebar.header("Filter Articles")
sentiment_filter = st.sidebar.multiselect(
    "Sentiment",
    options=filtered_df["sentiment"].dropna().unique(),
    default=filtered_df["sentiment"].dropna().unique()
)

filtered_df = filtered_df[filtered_df["sentiment"].isin(sentiment_filter)]

st.subheader("Relevant Articles")
st.dataframe(filtered_df)
