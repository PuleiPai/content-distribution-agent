#!/usr/bin/env python3
from __future__ import annotations
"""
Content distribution agent for peiluai.netlify.app articles.

Usage:
  python distribute.py                          # distribute all articles to all platforms
  python distribute.py --article ai_native      # specific article
  python distribute.py --platform twitter       # specific platform
  python distribute.py --dry-run                # preview without posting
"""
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from content import ARTICLES
from platforms import linkedin, medium, reddit, substack, twitter

SUPPORTED_PLATFORMS = ["twitter", "linkedin", "medium", "reddit", "substack"]
DEFAULT_PLATFORMS = ["twitter", "linkedin", "medium", "substack"]


def distribute_article(article: dict, platforms: list[str], dry_run: bool):
    article_id = article["id"]
    title = article["title"]
    print(f"\n{'='*60}")
    print(f"Article: {title}")
    print(f"{'='*60}")

    results = {}

    if "twitter" in platforms:
        print("\n[Twitter]")
        tweets = article["platforms"]["twitter"]
        urls = twitter.post_thread(tweets, dry_run=dry_run)
        results["twitter"] = urls

    if "medium" in platforms:
        print("\n[Medium]")
        m = article["platforms"]["medium"]
        url = medium.post_article(
            article_id=article_id,
            title=m["title"],
            content=m["content"],
            tags=m["tags"],
            canonical_url=m["canonical_url"],
            dry_run=dry_run,
        )
        results["medium"] = url

    if "linkedin" in platforms:
        print("\n[LinkedIn]")
        path = linkedin.prepare_post(article, dry_run=dry_run)
        results["linkedin"] = path

    if "reddit" in platforms:
        print("\n[Reddit]")
        r = article["platforms"]["reddit"]
        urls = reddit.post_link(
            subreddits=article["reddit_subreddits"],
            title=r["title"],
            url=r["url"],
            dry_run=dry_run,
        )
        results["reddit"] = urls

    if "substack" in platforms:
        print("\n[Substack]")
        s = article["platforms"]["substack"]
        path = substack.publish_post(
            title=s["title"],
            subtitle=s["subtitle"],
            body_markdown=s["content"],
            dry_run=dry_run,
        )
        results["substack"] = path

    return results


def main():
    parser = argparse.ArgumentParser(description="Distribute blog articles to social platforms.")
    parser.add_argument(
        "--article",
        choices=list(ARTICLES.keys()) + ["all"],
        default="all",
        help="Which article to distribute (default: all)",
    )
    parser.add_argument(
        "--platform",
        choices=SUPPORTED_PLATFORMS + ["all"],
        default="all",
        help="Which platform to post to (default: all working platforms: twitter, linkedin, medium, substack)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview content without actually posting",
    )
    args = parser.parse_args()

    articles = list(ARTICLES.values()) if args.article == "all" else [ARTICLES[args.article]]
    platforms = DEFAULT_PLATFORMS if args.platform == "all" else [args.platform]

    if args.dry_run:
        print("DRY RUN MODE — no posts will be made\n")

    all_results = {}
    for article in articles:
        results = distribute_article(article, platforms, dry_run=args.dry_run)
        all_results[article["id"]] = results

    print(f"\n{'='*60}")
    print("Done.")
    if not args.dry_run:
        print("\nSummary of posted URLs:")
        for article_id, results in all_results.items():
            print(f"\n  {ARTICLES[article_id]['title']}")
            for platform, urls in results.items():
                if isinstance(urls, list):
                    for url in urls:
                        print(f"    [{platform}] {url}")
                elif urls:
                    print(f"    [{platform}] {urls}")


if __name__ == "__main__":
    main()
