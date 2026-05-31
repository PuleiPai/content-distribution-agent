from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).parent.parent
DRAFTS_DIR = ROOT / "drafts"
ASSET_ROOT = ROOT / "assets" / "video"


YOUTUBE_CATEGORY_IDS = {
    "film": "1",
    "autos": "2",
    "music": "10",
    "pets": "15",
    "sports": "17",
    "gaming": "20",
    "people": "22",
    "comedy": "23",
    "entertainment": "24",
    "news": "25",
    "howto": "26",
    "education": "27",
    "science": "28",
    "travel": "19",
}


def strip_markdown(text: str) -> str:
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    text = text.replace("---", "")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _headings(markdown: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^##\s+(.+)$", markdown, flags=re.MULTILINE)]


def _paragraphs(markdown: str) -> list[str]:
    text = strip_markdown(markdown)
    return [
        p.strip()
        for p in text.split("\n\n")
        if p.strip() and len(p.strip()) > 40 and not p.strip().startswith(">")
    ]


def _sections(markdown: str) -> list[tuple[str, list[str]]]:
    matches = list(re.finditer(r"^##\s+(.+)$", markdown, flags=re.MULTILINE))
    sections: list[tuple[str, list[str]]] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown)
        title = match.group(1).strip()
        section_body = markdown[start:end].strip()
        paragraphs = _paragraphs(section_body)
        if paragraphs:
            sections.append((title, paragraphs))
    return sections


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 25]


def _words(text: str) -> list[str]:
    stopwords = {
        "about", "after", "again", "because", "before", "being", "between",
        "could", "every", "first", "from", "have", "into", "more", "much",
        "only", "other", "people", "really", "should", "their", "there",
        "these", "thing", "those", "through", "where", "which", "while",
        "with", "without", "would", "your",
    }
    seen: set[str] = set()
    result: list[str] = []
    for word in re.findall(r"\b[a-zA-Z][a-zA-Z-]{3,}\b", text.lower()):
        word = word.strip("-")
        if word and word not in stopwords and word not in seen:
            result.append(word)
            seen.add(word)
        if len(result) >= 12:
            break
    return result


def _category(title: str, body: str) -> str:
    text = f"{title} {body}".lower()
    if any(w in text for w in ["startup", "entrepreneur", "founder", "business", "career"]):
        return YOUTUBE_CATEGORY_IDS["education"]
    if any(w in text for w in ["ai", "software", "code", "engineering", "technology"]):
        return YOUTUBE_CATEGORY_IDS["science"]
    return YOUTUBE_CATEGORY_IDS["people"]


def build_video_script(article: dict, target_minutes: int = 5) -> str:
    title = article["title"]
    url = article.get("url", "")
    markdown = article["platforms"]["substack"]["content"]
    paragraphs = _paragraphs(markdown)
    sections = _sections(markdown)
    body = strip_markdown(markdown)

    opening = paragraphs[0] if paragraphs else body[:500]
    total_budget = target_minutes * 900
    used_chars = len(opening)

    transitions = [
        "This matters because once you see the statistic this way, it stops feeling like a verdict.",
        "That changes the emotional meaning of early failure. It becomes evidence of missing training, not fixed personal weakness.",
        "This is the key difference: in entrepreneurship, each attempt changes the next attempt.",
        "So the practical skill is not avoiding failure. It is learning how to convert feedback into better judgment.",
        "That is where the journey shifts from proving demand to building a system that can compound.",
    ]
    section_lines: list[str] = []
    usable_sections = sections[:5] or [("The core idea", paragraphs[1:])]
    per_section_budget = max(450, (total_budget - used_chars) // max(1, len(usable_sections)))

    for i, (heading, section_paragraphs) in enumerate(usable_sections, start=1):
        chosen: list[str] = []
        for paragraph in section_paragraphs:
            candidate = "\n\n".join(chosen + [paragraph])
            if len(candidate) > per_section_budget and chosen:
                break
            chosen.append(paragraph)
            if len(candidate) > per_section_budget:
                break
        support = "\n\n".join(chosen).strip()
        used_chars += len(support)
        transition = transitions[(i - 1) % len(transitions)]
        section_lines.append(
            f"### Part {i}: {heading}\n\n"
            f"{support}\n\n"
            f"{transition}"
        )

    return (
        f"# Video Script: {title}\n\n"
        "## Recording Notes\n\n"
        f"- Target length: {target_minutes}-6 minutes\n"
        "- Delivery: conversational, thoughtful, direct\n"
        "- Pace: leave short pauses after each main claim\n"
        "- Do not read the headings out loud unless they feel natural\n\n"
        "## Hook\n\n"
        f"{opening}\n\n"
        "Here is the distinction I want to unpack.\n\n"
        + "\n\n".join(section_lines)
        + "\n\n## Closing\n\n"
        "So the real question is not whether the average odds look discouraging. "
        "The real question is whether your judgment is improving after each iteration. "
        "If it is, your odds are not fixed. They are moving.\n\n"
        f"Full essay: {url}\n"
    )


def build_video_metadata(article: dict) -> dict:
    title = article["title"]
    url = article.get("url") or article["platforms"]["medium"]["canonical_url"]
    markdown = article["platforms"]["substack"]["content"]
    body = strip_markdown(markdown)
    first_sentences = _sentences(body)[:3]
    summary = " ".join(first_sentences)
    tags = article.get("tags") or _words(f"{title} {body}")
    tags = [str(tag).lower() for tag in tags][:12]

    description = (
        f"{summary}\n\n"
        f"Read the full essay: {url}\n\n"
        "Topics: " + ", ".join(tags)
    )

    short_caption = (
        f"{summary[:500].rstrip()}\n\n"
        f"Full essay: {url}"
    )

    return {
        "article_id": article["id"],
        "source_url": url,
        "title": title,
        "summary": summary,
        "tags": tags,
        "youtube": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "category": _category(title, body),
            "privacy": "unlisted",
        },
        "tiktok": {
            "title": title[:150],
            "description": short_caption[:2200],
            "privacy": "private",
        },
        "xiaohongshu": {
            "title": title[:40],
            "description": short_caption,
        },
        "bilibili": {
            "title": title[:80],
            "description": description,
            "tags": tags[:10],
        },
        "thumbnail": {
            "prompt": f"Thoughtful founder/creator essay thumbnail about: {title}",
            "youtube_path": f"assets/thumbnails/{article['id']}_youtube.jpg",
            "vertical_path": f"assets/thumbnails/{article['id']}_vertical.jpg",
        },
    }


def write_video_assets(article: dict, target_minutes: int = 5) -> dict[str, Path]:
    article_id = article["id"]
    DRAFTS_DIR.mkdir(exist_ok=True)
    asset_dir = ASSET_ROOT / article_id
    asset_dir.mkdir(parents=True, exist_ok=True)

    script = build_video_script(article, target_minutes=target_minutes)
    metadata = build_video_metadata(article)

    paths = {
        "script": DRAFTS_DIR / f"video_script_{article_id}.md",
        "youtube_description": DRAFTS_DIR / f"youtube_description_{article_id}.md",
        "tiktok_caption": DRAFTS_DIR / f"tiktok_caption_{article_id}.txt",
        "xiaohongshu_caption": DRAFTS_DIR / f"xiaohongshu_caption_{article_id}.txt",
        "bilibili_description": DRAFTS_DIR / f"bilibili_description_{article_id}.md",
        "metadata": asset_dir / "metadata.json",
        "upload_info": asset_dir / "upload_info.json",
    }

    paths["script"].write_text(script, encoding="utf-8")
    paths["youtube_description"].write_text(metadata["youtube"]["description"] + "\n", encoding="utf-8")
    paths["tiktok_caption"].write_text(metadata["tiktok"]["description"] + "\n", encoding="utf-8")
    paths["xiaohongshu_caption"].write_text(metadata["xiaohongshu"]["description"] + "\n", encoding="utf-8")
    paths["bilibili_description"].write_text(metadata["bilibili"]["description"] + "\n", encoding="utf-8")
    paths["metadata"].write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["upload_info"].write_text(json.dumps(metadata["youtube"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return paths


def load_metadata(article_id: str) -> dict:
    path = ASSET_ROOT / article_id / "metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing video metadata: {path}. Run `python video.py prepare --article {article_id}` first.")
    return json.loads(path.read_text(encoding="utf-8"))
