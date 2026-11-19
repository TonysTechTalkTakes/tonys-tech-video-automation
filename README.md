# Tony's Tech Talk Takes video automation

This repository renders review-ready videos through GitHub Actions. The workflow is manual by design: it creates an MP4 artifact and never uploads or publishes to YouTube.

## Create a video

1. Open **Actions** and select **Tony's Tech Video**.
2. Choose **Run workflow**, then enter the title and narration script.
3. Choose **short** for a vertical 720×1280 video or **long** for a 1920×1080 video.
4. Download the artifact after the workflow succeeds and review it before any upload.

Both formats use the approved natural American English voice en-US-GuyNeural from Edge TTS, synchronized animated captions, branded motion graphics, an intro wipe, and a sliding branded ending. Short scripts are limited to 450 words (about 3 minutes); long scripts to 2,400 words (roughly 12–16 minutes, depending on delivery speed).

## Current scope and next steps

The workflow accepts a reviewed title and script. It does not yet research trends, draft or fact-check scripts, or publish to YouTube. Those stages should be added as separate, reviewable steps. YouTube publishing will require an authorized channel connection or API credentials, and public publishing must stay behind an explicit approval step.

The renderer needs Python, FFmpeg with drawtext and libass, DejaVu Sans, and the edge-tts package. GitHub Actions installs these for each run.
