# Tony's Tech Talk Takes video automation

This repository renders review-ready videos through GitHub Actions. Rendering and YouTube uploading are separate manual workflows. A render never uploads anything. The upload workflow downloads a previously reviewed artifact and makes the selected visibility explicit before it sends the video to YouTube.

## Create a video

1. Open **Actions** and select **Tony's Tech Video**.
2. Choose **Run workflow**, then enter the title and narration script.
3. Choose **short** for a vertical 720×1280 video or **long** for a 1920×1080 video.
4. Download the artifact after the workflow succeeds and review it before any upload.

Both formats use the approved natural American English voice en-US-GuyNeural from Edge TTS, synchronized animated captions, branded motion graphics, an intro wipe, and a sliding branded ending. Short scripts are limited to 450 words (about 3 minutes); long scripts to 2,400 words (roughly 12–16 minutes, depending on delivery speed).

## Publish a reviewed video

Publishing is a separate, manually started workflow. It does not run automatically after rendering.

1. Review the MP4 from a successful **Tony's Tech Video** run. Copy that run's numeric run ID from its URL and the exact artifact name shown on the run summary (for example, `tonys-tech-video-short-3`).
2. Open **Actions → Publish reviewed video to YouTube → Run workflow**.
3. Enter the source run ID, artifact name, format, YouTube title and description, and optional tags.
4. Choose **Public**, **Unlisted**, or **Private**. Public is the default. For Public, also check **Confirm public**. Check the policy review box for every upload.
5. Start the workflow. It downloads the selected artifact, verifies its dimensions and complete decode, then uploads it to the channel authorized by the saved OAuth token. The run prints the resulting YouTube link.

### One-time YouTube authorization

The channel owner must configure OAuth and add a GitHub Actions secret. Never paste OAuth files or tokens into chat, issues, or repository files.

1. In Google Cloud, create the dedicated YouTube upload API project required by YouTube's developer policies. The policy currently says to prefix the project ID with `mfk110`. Enable **YouTube Data API v3** and create an OAuth client for a desktop app. Use the narrow `youtube.upload` scope.
2. Download the OAuth client JSON as `client_secrets.json` in a trusted local copy of this repository. From that folder, run:

   ```sh
   python -m pip install -r requirements-youtube.txt
   python scripts/authorize_youtube.py client_secrets.json
   ```

   A browser opens for the channel owner to grant consent. The script saves `youtube_token.json` locally with restricted file permissions.
3. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**. Name it `YOUTUBE_TOKEN_JSON` and paste the complete contents of `youtube_token.json` as the secret value. Do not commit either JSON file; both are covered by `.gitignore`.

An OAuth app left in Google's external **Testing** status issues refresh tokens that expire after seven days. For recurring use, configure an eligible personal OAuth app or complete the Google publishing and verification requirements before relying on the workflow long term. Reauthorize and replace the GitHub secret if Google access is revoked or the token expires.

## Current scope and next steps

Topic research, script drafting and fact-checking, channel analytics, and scheduling are not automated yet. The upload workflow can publish a reviewed render, but every upload requires a manual run and an explicit visibility choice. Public uploads require a separate confirmation and policy review. YouTube's current default `videos.insert` quota is 100 uploads per day per API project; the channel's own upload limit and YouTube policies may be lower, so this workflow does not promise 100 public videos each day.

The renderer needs Python, FFmpeg with drawtext and libass, DejaVu Sans, and the edge-tts package. GitHub Actions installs these for each run.
