from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


PLATFORM_URLS = {
    "tiktok": "https://www.tiktok.com/upload",
    "xiaohongshu": "https://creator.xiaohongshu.com/publish/publish",
    "bilibili": "https://member.bilibili.com/platform/upload/video/frame",
}


def copy_text(text: str) -> bool:
    if sys.platform == "darwin":
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return True
    return False


def open_platform(platform: str) -> None:
    url = PLATFORM_URLS[platform]
    if sys.platform == "darwin":
        subprocess.run(["open", "-a", "Google Chrome", url], check=False)
    else:
        import webbrowser

        webbrowser.open(url)


def prepare_browser_handoff(platform: str, video_path: Path, metadata: dict, dry_run: bool = False) -> str:
    if platform not in PLATFORM_URLS:
        raise ValueError(f"Unsupported browser-assisted video platform: {platform}")

    data = metadata[platform]
    title = data.get("title", metadata["title"])
    description = data.get("description", metadata.get("summary", ""))
    clipboard_text = f"{title}\n\n{description}".strip()

    print(f"  Platform: {platform}")
    print(f"  Upload URL: {PLATFORM_URLS[platform]}")
    print(f"  Video file: {video_path}")
    print(f"  Title: {title}")

    if dry_run:
        print("\n[DRY RUN] Browser-assisted caption:")
        print(clipboard_text)
        return "dry-run"

    if copy_text(clipboard_text):
        print("  Copied title/description to clipboard.")
    open_platform(platform)
    print(f"  Opened {platform} upload page in Chrome.")

    print(
        textwrap.dedent(
            f"""

            Computer Use posting steps for {platform}:
              1. Confirm Chrome is on {PLATFORM_URLS[platform]} and you are logged in.
              2. Upload the video file:
                 {video_path}
              3. Paste the copied title/description into the platform fields.
              4. Add/select thumbnail if the platform supports it.
              5. Keep privacy conservative first: private/unlisted/draft.
              6. Publish only after visually checking title, caption, cover, and account.
            """
        ).rstrip()
    )
    return PLATFORM_URLS[platform]
