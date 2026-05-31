from __future__ import annotations

import re
import subprocess
import sys
import textwrap
import webbrowser
from pathlib import Path


ROOT = Path(__file__).parent.parent
DRAFTS_DIR = ROOT / "drafts"
DEFAULT_MAX_CHARS = 2500


UNICODE_REPLACEMENTS = {
    "\u2014": "-",
    "\u2013": "-",
    "\u2192": "-",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
}


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = text.replace("---", "")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _ascii_safe(text: str) -> str:
    for old, new in UNICODE_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text


def _truncate_at_paragraph(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text

    paragraphs = text.split("\n\n")
    kept: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) > max_chars:
            break
        kept.append(paragraph)
        current = candidate

    if kept:
        return "\n\n".join(kept).strip()
    return text[: max_chars - 3].rstrip() + "..."


def _draft_path(article_id: str) -> Path:
    return DRAFTS_DIR / f"linkedin_{article_id}.txt"


def _build_from_article(article: dict, max_chars: int) -> str:
    title = article["title"]
    url = article.get("url") or article["platforms"]["medium"]["canonical_url"]
    substack = article["platforms"].get("substack", {})
    body = _strip_markdown(substack.get("content", ""))

    intro = f'"{title}"\n\n'
    suffix = f"\n\nFull essay: {url}"
    budget = max_chars - len(intro) - len(suffix)
    body = _truncate_at_paragraph(body, max(200, budget))
    return f"{intro}{body}{suffix}".strip()


def build_post(article: dict, max_chars: int = DEFAULT_MAX_CHARS) -> str:
    article_id = article["id"]
    configured = article.get("platforms", {}).get("linkedin", {}).get("content", "").strip()
    draft_path = _draft_path(article_id)

    if configured:
        text = configured
    elif draft_path.exists():
        text = draft_path.read_text(encoding="utf-8").strip()
    else:
        text = _build_from_article(article, max_chars)

    text = _ascii_safe(text)
    if len(text) > max_chars:
        text = _truncate_at_paragraph(text, max_chars)
    return text.strip()


def _copy_to_clipboard(text: str) -> bool:
    if sys.platform == "darwin":
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return True
    return False


def _open_linkedin() -> None:
    url = "https://www.linkedin.com/feed/"
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", "Google Chrome", url], check=False)
    else:
        webbrowser.open(url)


def prepare_post(article: dict, dry_run: bool = False, open_browser: bool = True) -> str:
    text = build_post(article)
    draft_path = _draft_path(article["id"])
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(text + "\n", encoding="utf-8")

    print(f"  LinkedIn draft: {draft_path}")
    print(f"  Characters: {len(text)}")

    if dry_run:
        print("\n[DRY RUN] LinkedIn post preview:")
        print(text)
        return ""

    copied = _copy_to_clipboard(text)
    if copied:
        print("  Copied LinkedIn draft to clipboard.")
    if open_browser:
        _open_linkedin()
        print("  Opened LinkedIn feed in Chrome.")

    print(
        textwrap.dedent(
            """

            Computer Use posting steps:
              1. Get the Chrome app state and confirm linkedin.com/feed/ is open.
              2. Click "Start a post".
              3. Paste the clipboard into the post editor.
              4. If Unicode looks garbled, replace the editor value with the draft file text.
              5. Remove any unintended media/link preview if LinkedIn attaches one.
              6. Click "Post" and wait for "Post successful."
            """
        ).rstrip()
    )
    return str(draft_path)
