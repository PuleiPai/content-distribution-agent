"""
Medium publishing via patchright (undetected Playwright) + saved cookies.
Auth: loads medium_cookies.json saved during login flow.
Publishing: navigates to medium.com/p/import, pastes canonical URL, imports and publishes.
"""
from __future__ import annotations
import json
import time
from pathlib import Path

COOKIES_FILE = Path(__file__).parent.parent / "medium_cookies.json"
DEBUG_DIR = Path(__file__).parent.parent / "debug"
W, H = 1280, 800


def _screenshot(page, name: str):
    DEBUG_DIR.mkdir(exist_ok=True)
    page.screenshot(path=str(DEBUG_DIR / f"{name}.png"))


def _import_and_publish(page, article_url: str, article_id: str, tags: list[str]) -> str:
    page.goto("https://medium.com/p/import")
    page.wait_for_load_state("networkidle")
    time.sleep(2)
    _screenshot(page, f"{article_id}_01_import_page")

    if page.locator('text="Sign in"').count() > 0:
        print("  ERROR: Not logged into Medium. Cookies may have expired — re-run login.")
        return ""

    # Click input at 50%, 41.6% and type the URL
    page.mouse.click(W * 0.50, H * 0.416)
    time.sleep(0.5)
    page.keyboard.type(article_url, delay=30)
    _screenshot(page, f"{article_id}_02_url_entered")

    # Click Import button at 50%, 57%
    page.mouse.click(W * 0.50, H * 0.57)
    time.sleep(4)
    _screenshot(page, f"{article_id}_03_after_import")

    # After import overlay — click "See your story" at 50%, 85.6%
    page.mouse.click(W * 0.50, H * 0.856)
    time.sleep(3)
    _screenshot(page, f"{article_id}_04_editor")

    # Dismiss the "Writing on Medium" tutorial overlay (× at 97.7%, 66.3%)
    page.mouse.click(W * 0.977, H * 0.663)
    time.sleep(1)

    # Wait for auto-save to complete — poll until no button says "Saving..."
    for _ in range(20):
        saving = page.evaluate(
            '() => Array.from(document.querySelectorAll("button")).some(b => b.textContent.includes("Saving"))'
        )
        if not saving:
            break
        time.sleep(1)
    time.sleep(1)
    _screenshot(page, f"{article_id}_05_before_publish")

    # Click the green "Publish" toolbar button by coordinate (77.3%, 4.6%)
    page.mouse.click(W * 0.773, H * 0.046)

    # Wait for the Story Preview panel to fully open
    try:
        page.locator('text="Story preview"').wait_for(state="visible", timeout=15000)
        time.sleep(1)
    except Exception:
        print("  WARNING: story preview panel did not open in time")
    _screenshot(page, f"{article_id}_06_story_preview")

    # Add topics — click input once, then use JS to re-focus after each chip is added
    # (the input element moves rightward after each tag, so coordinate clicks miss it)
    page.mouse.click(W * 0.702, H * 0.335)
    time.sleep(0.5)
    for tag in tags[:5]:
        page.evaluate(
            "() => { const el = document.querySelector('input[placeholder=\"Add a topic...\"]')"
            "     || document.querySelector('input[placeholder=\"Add more topics...\"]');"
            "  if (el) el.focus(); }"
        )
        time.sleep(0.3)
        page.keyboard.type(tag)
        time.sleep(1.5)
        first_suggestion = page.locator('[role="option"]').first
        if first_suggestion.is_visible(timeout=2000):
            first_suggestion.click()
        else:
            page.keyboard.press("Enter")
        time.sleep(0.5)
    _screenshot(page, f"{article_id}_07_topics_added")

    # Click the Publish button in the Story Preview panel like a human
    # Use bounding box so position is accurate regardless of how many topic rows are shown
    final_btn = page.locator('button:has-text("Publish")').last
    box = final_btn.bounding_box(timeout=5000)
    if box:
        cx = box["x"] + box["width"] / 2
        cy = box["y"] + box["height"] / 2
        page.mouse.move(cx, cy)
        time.sleep(0.4)
        page.mouse.click(cx, cy)
        print(f"  Clicked Publish in story preview at ({cx:.0f}, {cy:.0f})")
    else:
        # Fallback coordinates if bounding box unavailable
        page.mouse.move(W * 0.557, H * 0.770)
        time.sleep(0.4)
        page.mouse.click(W * 0.557, H * 0.770)
        print("  Clicked Publish in story preview (fallback coordinates)")
    time.sleep(3)

    page.wait_for_load_state("networkidle")
    time.sleep(3)
    url = page.url
    _screenshot(page, f"{article_id}_08_done")
    return url


def post_article(article_id: str, title: str, content: str, tags: list[str], canonical_url: str, dry_run: bool = False) -> str:
    if dry_run:
        print(f"\n[DRY RUN] Medium import preview:")
        print(f"  Will import from: {canonical_url}")
        print(f"  Tags: {tags}")
        print(f"  Title: {title}\n")
        return ""

    if not COOKIES_FILE.exists():
        print("  ERROR: medium_cookies.json not found. Run the login script first.")
        return ""

    from patchright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=[f"--window-size={W},{H}"])
        context = browser.new_context(viewport={"width": W, "height": H})
        context.add_cookies(json.loads(COOKIES_FILE.read_text()))
        page = context.new_page()

        url = _import_and_publish(page, canonical_url, article_id, tags)

        if url:
            print(f"  Published to Medium: {url}", flush=True)
        print("  Browser left open — close it manually when done verifying.", flush=True)
        try:
            time.sleep(600)  # keep process alive so browser stays open (up to 10 min)
        except KeyboardInterrupt:
            pass

    return url
