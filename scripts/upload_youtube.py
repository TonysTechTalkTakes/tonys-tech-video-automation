#!/usr/bin/env python3
"""Upload one reviewed MP4 to the authenticated YouTube channel."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

SCOPE = "https://www.googleapis.com/auth/youtube.upload"
VALID_PRIVACY = {"public", "private", "unlisted"}


def load_credentials(secret: str) -> Credentials:
    try:
        token = json.loads(secret)
        credentials = Credentials.from_authorized_user_info(token, [SCOPE])
    except (ValueError, TypeError, KeyError) as exc:
        raise SystemExit("YOUTUBE_TOKEN_JSON must contain authorized-user OAuth JSON with a refresh token.") from exc
    if not credentials.refresh_token:
        raise SystemExit("YOUTUBE_TOKEN_JSON is missing refresh_token. Re-authorize with offline access.")
    if credentials.expired or not credentials.valid:
        credentials.refresh(Request())
    return credentials


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--tags", default="", help="Comma-separated YouTube tags")
    parser.add_argument("--category-id", default="28", help="YouTube category ID (28 = Science & Technology)")
    parser.add_argument("--privacy-status", choices=sorted(VALID_PRIVACY), required=True)
    args = parser.parse_args()

    video = Path(args.file)
    if not video.is_file() or video.stat().st_size == 0:
        raise SystemExit(f"Video file is missing or empty: {video}")
    if not args.title.strip() or len(args.title) > 100:
        raise SystemExit("Title is required and must be at most 100 characters.")
    if not args.description.strip() or len(args.description.encode("utf-8")) > 5000:
        raise SystemExit("Description is required and must be no more than 5,000 UTF-8 bytes.")

    token_json = os.environ.get("YOUTUBE_TOKEN_JSON", "")
    if not token_json:
        raise SystemExit("Missing GitHub Actions secret YOUTUBE_TOKEN_JSON. See README.md for OAuth setup.")
    credentials = load_credentials(token_json)
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()]
    body = {
        "snippet": {
            "title": args.title.strip(),
            "description": args.description.strip(),
            "tags": tags,
            "categoryId": args.category_id,
        },
        "status": {"privacyStatus": args.privacy_status},
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True),
    )
    response = None
    retries = 0
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"Upload progress: {int(status.progress() * 100)}%", flush=True)
            retries = 0
        except HttpError as exc:
            if exc.resp.status not in (500, 502, 503, 504) or retries >= 5:
                raise
            time.sleep(min(2**retries, 32))
            retries += 1
    video_id = response.get("id")
    if not video_id:
        raise SystemExit("YouTube accepted the upload request but did not return a video ID.")
    print(f"Uploaded to YouTube ({args.privacy_status}): https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()
