from __future__ import annotations
import os
import tweepy


def get_client():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_KEY_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )


def post_thread(tweets: list[str], dry_run: bool = False) -> list[str]:
    """Post a list of tweets as a thread. Returns list of tweet URLs."""
    if dry_run:
        print("\n[DRY RUN] Twitter thread preview:")
        for i, tweet in enumerate(tweets, 1):
            print(f"  [{i}/{len(tweets)}] {tweet}\n")
        return []

    client = get_client()
    tweet_ids = []
    reply_to = None

    for tweet in tweets:
        kwargs = {"text": tweet}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = reply_to
        response = client.create_tweet(**kwargs)
        tweet_id = response.data["id"]
        tweet_ids.append(tweet_id)
        reply_to = tweet_id

    urls = [f"https://twitter.com/i/web/status/{tid}" for tid in tweet_ids]
    print(f"  Posted {len(tweets)}-tweet thread. First tweet: {urls[0]}")
    return urls
