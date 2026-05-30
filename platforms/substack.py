from __future__ import annotations
import os
import json
from pathlib import Path
from substack import Api
from substack.post import Post

COOKIES_FILE = Path(__file__).parent.parent / "substack_cookies.json"


def _get_api() -> Api:
    pub_url = os.environ["SUBSTACK_PUBLICATION_URL"]

    # 1. Try cookie string from .env (safest — no keychain access)
    cookie_string = os.environ.get("SUBSTACK_COOKIE_STRING", "").strip()
    if cookie_string:
        return Api(cookies_string=cookie_string, publication_url=pub_url)

    # 2. Try saved cookies JSON file
    if COOKIES_FILE.exists():
        cookies = json.loads(COOKIES_FILE.read_text())
        cookie_string = "; ".join(
            f"{c['name']}={c['value']}" for c in cookies
            if ".substack.com" in c.get("domain", "")
        )
        if cookie_string:
            print("  Loaded Substack cookies from substack_cookies.json")
            return Api(cookies_string=cookie_string, publication_url=pub_url)

    # 3. Fall back to email/password
    print("  Using email/password login...")
    return Api(
        email=os.environ["SUBSTACK_EMAIL"],
        password=os.environ["SUBSTACK_PASSWORD"],
        publication_url=pub_url,
    )


def publish_post(title: str, subtitle: str, body_markdown: str, dry_run: bool = False) -> str:
    if dry_run:
        preview = body_markdown[:150].replace("\n", " ")
        print(f"\n[DRY RUN] Substack post preview:")
        print(f"  Title: {title}")
        print(f"  Subtitle: {subtitle}")
        print(f"  Preview: {preview}...\n")
        return ""

    api = _get_api()
    user_id = api.get_user_id()

    post = Post(title=title, subtitle=subtitle, user_id=user_id)
    post.from_markdown(body_markdown)

    draft = api.post_draft(post.get_draft())
    draft_id = draft.get("id")
    api.prepublish_draft(draft_id)
    published = api.publish_draft(draft_id)

    slug = (published or draft).get("slug") or (published or draft).get("canonical_url", "").split("/p/")[-1]
    pub_url = os.environ["SUBSTACK_PUBLICATION_URL"].rstrip("/")
    url = f"{pub_url}/p/{slug}" if slug else pub_url
    print(f"  Published to Substack: {url}")
    return url
