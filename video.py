#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from content import ARTICLES
from video.assets import load_metadata, write_video_assets
from video_platforms import browser_assisted


VIDEO_PLATFORMS = ["youtube", "tiktok", "xiaohongshu", "bilibili"]
ROOT = Path(__file__).parent
THUMBNAILS_DIR = ROOT / "assets" / "thumbnails"
VIDEOS_DIR = ROOT / "assets" / "videos"


def _platforms(value: str) -> list[str]:
    if value == "all":
        return VIDEO_PLATFORMS
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _validate_platforms(platforms: list[str]) -> None:
    unknown = [p for p in platforms if p not in VIDEO_PLATFORMS]
    if unknown:
        raise SystemExit(f"Unknown video platform(s): {', '.join(unknown)}")


def _default_thumbnail(article_id: str, platform: str) -> Path:
    if platform in {"tiktok", "xiaohongshu"}:
        return THUMBNAILS_DIR / f"{article_id}_vertical.jpg"
    return THUMBNAILS_DIR / f"{article_id}_youtube.jpg"


def prepare(args: argparse.Namespace) -> None:
    article = ARTICLES[args.article]
    paths = write_video_assets(article, target_minutes=args.target_minutes)
    print("\nGenerated video assets:")
    for label, path in paths.items():
        print(f"  {label}: {path}")

    if args.thumbnail_base:
        from video.generate_thumbnail import generate_thumbnail

        base = Path(args.thumbnail_base).expanduser()
        if not base.exists():
            raise SystemExit(f"Thumbnail base image not found: {base}")
        THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
        title = article["title"]
        generate_thumbnail(str(base), title, str(_default_thumbnail(article["id"], "youtube")), "youtube")
        generate_thumbnail(str(base), title, str(_default_thumbnail(article["id"], "tiktok")), "vertical")

    print("\nNext step:")
    print(f"  Record using: {paths['script']}")
    print(f"  Put the finished video under {VIDEOS_DIR}/ or pass --video /path/to/video.mov")


def distribute(args: argparse.Namespace) -> None:
    article_id = args.article
    metadata = load_metadata(article_id)
    platforms = _platforms(args.platform)
    _validate_platforms(platforms)

    video_path = Path(args.video).expanduser() if args.video else None
    if not video_path:
        matches = sorted([*VIDEOS_DIR.glob(f"{article_id}*.mp4"), *VIDEOS_DIR.glob(f"{article_id}*.mov")])
        video_path = matches[0] if matches else None
    if not video_path or not video_path.exists():
        raise SystemExit(
            "Video file not found. Put a finished .mp4/.mov in "
            f"{VIDEOS_DIR} with prefix {article_id}, or pass --video /path/to/file."
        )

    results: dict[str, str] = {}
    for platform in platforms:
        print(f"\n[{platform}]")
        if platform == "youtube":
            yt = metadata["youtube"]
            thumbnail = Path(args.thumbnail).expanduser() if args.thumbnail else _default_thumbnail(article_id, platform)
            if not thumbnail.exists():
                raise SystemExit(f"YouTube thumbnail not found: {thumbnail}. Run prepare with --thumbnail-base or pass --thumbnail.")
            if args.dry_run:
                print(json.dumps({"video": str(video_path), "thumbnail": str(thumbnail), **yt}, indent=2))
                results[platform] = "dry-run"
            else:
                from video_platforms import youtube

                results[platform] = youtube.upload_video(
                    video_path=str(video_path),
                    thumbnail_path=str(thumbnail),
                    title=yt["title"],
                    description=yt["description"],
                    tags=yt["tags"],
                    category_id=yt["category"],
                    privacy=yt.get("privacy", "unlisted"),
                )
        else:
            results[platform] = browser_assisted.prepare_browser_handoff(
                platform,
                video_path=video_path,
                metadata=metadata,
                dry_run=args.dry_run,
            )

    print("\nVideo distribution results:")
    for platform, result in results.items():
        print(f"  {platform}: {result}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and distribute video assets from article content.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Generate recording script and platform metadata")
    prepare_parser.add_argument("--article", choices=list(ARTICLES.keys()), required=True)
    prepare_parser.add_argument("--target-minutes", type=int, default=5)
    prepare_parser.add_argument("--thumbnail-base", help="Optional base image to generate YouTube/vertical thumbnails")
    prepare_parser.set_defaults(func=prepare)

    distribute_parser = subparsers.add_parser("distribute", help="Distribute a finished video")
    distribute_parser.add_argument("--article", choices=list(ARTICLES.keys()), required=True)
    distribute_parser.add_argument("--platform", default="youtube", help="youtube,tiktok,xiaohongshu,bilibili,all")
    distribute_parser.add_argument("--video", help="Path to finished .mp4/.mov")
    distribute_parser.add_argument("--thumbnail", help="Path to YouTube thumbnail")
    distribute_parser.add_argument("--dry-run", action="store_true")
    distribute_parser.set_defaults(func=distribute)

    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
