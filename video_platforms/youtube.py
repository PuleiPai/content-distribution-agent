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
    thumbnail_path: str,
    title: str,
    description: str,
    tags: list[str],
    category_id: str,
    privacy: str = "unlisted",
) -> str:
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

    media = MediaFileUpload(video_path, mimetype="video/*", resumable=True, chunksize=10 * 1024 * 1024)
    print(f"Uploading to YouTube: {video_path}")
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  Upload progress: {int(status.progress() * 100)}%", end="\r")

    video_id = response["id"]
    print(f"\nUpload complete. Video ID: {video_id}")

    if thumbnail_path:
        print("Setting thumbnail...")
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg"),
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
    parser.add_argument("--privacy", default="unlisted")
    args = parser.parse_args()

    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    try:
        upload_video(args.video, args.thumbnail, args.title, args.description, tags, args.category, args.privacy)
    except (FileNotFoundError, HttpError) as exc:
        print(f"YouTube upload failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
