from __future__ import annotations

import sys
from pathlib import Path

import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


ROOT = Path(__file__).parent.parent
SECRETS_DIR = ROOT / "secrets"
CLIENT_SECRETS = SECRETS_DIR / "youtube_client_secrets.json"
LEGACY_CLIENT_SECRETS = ROOT / "client_secrets.json"
TOKEN_FILE = SECRETS_DIR / "youtube_token.json"

CATEGORY_IDS = {
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

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def _client_secrets_path() -> Path:
    if CLIENT_SECRETS.exists():
        return CLIENT_SECRETS
    if LEGACY_CLIENT_SECRETS.exists():
        return LEGACY_CLIENT_SECRETS
    raise FileNotFoundError(
        "Missing YouTube OAuth client secrets. Put them at "
        f"{CLIENT_SECRETS} (preferred) or {LEGACY_CLIENT_SECRETS}."
    )


def get_authenticated_service():
    SECRETS_DIR.mkdir(exist_ok=True)
    creds = None

    if TOKEN_FILE.exists():
        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                str(_client_secrets_path()),
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    thumbnail_path: str | None,
    title: str,
    description: str,
    tags: list[str],
    category_id: str,
    privacy: str = "private",
) -> str:
    video_file = Path(video_path).expanduser()
    if not video_file.exists():
        raise FileNotFoundError(f"YouTube video file not found: {video_file}")

    thumbnail_file = Path(thumbnail_path).expanduser() if thumbnail_path else None
    if thumbnail_file and not thumbnail_file.exists():
        raise FileNotFoundError(f"YouTube thumbnail file not found: {thumbnail_file}")

    category_id = CATEGORY_IDS.get(category_id, category_id)

    youtube = get_authenticated_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_file), mimetype="video/*", resumable=True, chunksize=10 * 1024 * 1024)
    print(f"Uploading to YouTube as {privacy}: {video_file}")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%", end="\r")

    video_id = response["id"]
    print(f"\nUpload complete. Video ID: {video_id}")

    if thumbnail_file:
        print("Setting thumbnail...")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumbnail_file), mimetype="image/jpeg"),
        ).execute()
        print("Thumbnail set.")

    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"Video URL: {url}")
    print(f"Studio URL: https://studio.youtube.com/video/{video_id}/edit")
    return url


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--thumbnail", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--tags", default="")
    parser.add_argument("--category", default="22")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    args = parser.parse_args()

    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    try:
        upload_video(args.video, args.thumbnail, args.title, args.description, tags, args.category, args.privacy)
    except (FileNotFoundError, HttpError) as exc:
        print(f"YouTube upload failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
