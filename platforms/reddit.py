from __future__ import annotations
import os
import praw


def get_reddit():
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent="ContentDistributor/1.0 (by u/{})".format(os.environ["REDDIT_USERNAME"]),
    )


def post_link(subreddits: list[str], title: str, url: str, dry_run: bool = False) -> list[str]:
    """Submit a link post to each subreddit. Returns list of post URLs."""
    if dry_run:
        print(f"\n[DRY RUN] Reddit link post preview:")
        print(f"  Subreddits: {subreddits}")
        print(f"  Title: {title}")
        print(f"  URL: {url}\n")
        return []

    reddit = get_reddit()
    urls = []
    for sub in subreddits:
        submission = reddit.subreddit(sub).submit(title=title, url=url)
        post_url = f"https://www.reddit.com{submission.permalink}"
        urls.append(post_url)
        print(f"  Posted to r/{sub}: {post_url}")
    return urls


def post_text(subreddits: list[str], title: str, text: str, dry_run: bool = False) -> list[str]:
    """Submit a text/self post to each subreddit. Returns list of post URLs."""
    if dry_run:
        print(f"\n[DRY RUN] Reddit text post preview:")
        print(f"  Subreddits: {subreddits}")
        print(f"  Title: {title}")
        print(f"  Body: {text[:200]}...\n")
        return []

    reddit = get_reddit()
    urls = []
    for sub in subreddits:
        submission = reddit.subreddit(sub).submit(title=title, selftext=text)
        post_url = f"https://www.reddit.com{submission.permalink}"
        urls.append(post_url)
        print(f"  Posted to r/{sub}: {post_url}")
    return urls
