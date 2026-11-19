#!/usr/bin/env python3
"""Create a refresh token for GitHub Actions after the channel owner consents."""
import argparse
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("client_secrets", help="OAuth Desktop client JSON downloaded from Google Cloud")
    parser.add_argument("--output", default="youtube_token.json", help="Local token file (never commit this file)")
    args = parser.parse_args()
    flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, [SCOPE])
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    output = Path(args.output)
    output.write_text(credentials.to_json(), encoding="utf-8")
    output.chmod(0o600)
    print(f"OAuth token saved to {output}. Add its complete JSON as the GitHub Actions secret YOUTUBE_TOKEN_JSON.")
    print("Do not commit or send the token file. Revoke access in your Google Account if it is exposed.")


if __name__ == "__main__":
    main()
