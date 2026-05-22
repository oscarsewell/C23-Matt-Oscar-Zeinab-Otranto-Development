import atproto


def login_to_bluesky(b_sky_username: str, b_sky_password: str) -> atproto.Client:
    client = atproto.Client()
    # TODO: Use app password instead of main password
    client.login(b_sky_username, b_sky_password)
    return client


def post_to_bluesky(client: atproto.Client, content: str) -> None:
    client.send_post(content)


def create_positive_sentiment_post(url: str) -> atproto.client_utils.TextBuilder:
    fanciful_text = atproto.client_utils.TextBuilder()
    fanciful_text.text("Just read the amazing news, ")
    fanciful_text.link("check it out!", url)
    fanciful_text.text(" #PositiveVibes")
    return fanciful_text


def create_negative_sentiment_post(url: str, enemy: str) -> atproto.client_utils.TextBuilder:
    fanciful_text = atproto.client_utils.TextBuilder()
    fanciful_text.text("Wow, sucks to be you, " +
                       enemy + ". Can you believe it? ")
    fanciful_text.link("check it out!", url)
    fanciful_text.text(" #EPICFAIL")
    return fanciful_text


def read_bio(client: atproto.Client, username: str) -> str:
    profile = client.get_profile(username)
    return profile.description


def is_sentiment_score_valid(score: float, threshold: float) -> bool:
    return isinstance(score, (int, float)) and 0 <= score <= 5 and score >= threshold


if __name__ == "__main__":
    # Example usage
    client = login_to_bluesky(
        "importantcelebrity.bsky.social", "fvqy-363s-xlpd-urqd")
    post_to_bluesky(client, create_positive_sentiment_post(
        "https://example.com/good-news"))
    post_to_bluesky(client, create_negative_sentiment_post(
        "https://example.com/bad-news", read_bio(client, "importantcelebrity.bsky.social")))
    bio = read_bio(client, "importantcelebrity.bsky.social")
