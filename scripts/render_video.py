#!/usr/bin/env python3
"""Render branded, captioned Tony's Tech Talk Takes videos with Edge TTS and FFmpeg."""
from __future__ import annotations
import argparse
import re
import subprocess
import sys
import textwrap
from pathlib import Path

VOICE = "en-US-GuyNeural"

def parse_time(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds.replace(",", "."))

def ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, rem = divmod(centiseconds, 360000)
    minutes, rem = divmod(rem, 6000)
    whole, fraction = divmod(rem, 100)
    return f"{hours}:{minutes:02d}:{whole:02d}.{fraction:02d}"

def vtt_cues(vtt: str) -> list[tuple[float, float, str]]:
    cues = []
    for block in re.split(r"\n\s*\n", vtt.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing = next((line for line in lines if "-->" in line), None)
        if not timing:
            continue
        start, end = timing.split("-->", 1)
        end = end.strip().split()[0]
        text = " ".join(line for line in lines[lines.index(timing) + 1:] if not line.startswith(("NOTE", "STYLE")))
        text = re.sub(r"<[^>]+>", "", text).replace("{", "").replace("}", "").strip()
        if text:
            cues.append((parse_time(start.strip()), parse_time(end), text))
    return cues

def write_ass(vtt_path: Path, ass_path: Path, width: int, height: int) -> None:
    margin_v = 270 if height > width else 150
    font_size = 48 if height > width else 50
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,DejaVu Sans,{font_size},&H00FFFFFF,&H0000FFFF,&H00101828,&HAA101828,-1,0,0,0,100,100,0,0,3,3,1,2,48,48,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    rows = []
    for start, end, text in vtt_cues(vtt_path.read_text(encoding="utf-8")):
        chunks = textwrap.wrap(text, width=25 if height > width else 54, break_long_words=False) or [text]
        total = sum(len(chunk) for chunk in chunks)
        elapsed = 0.0
        for chunk in chunks:
            share = (end - start) * len(chunk) / max(1, total)
            rows.append(f"Dialogue: 0,{ass_time(start + elapsed)},{ass_time(start + elapsed + share)},Caption,,0,0,0,,{chunk}")
            elapsed += share
    ass_path.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")

def run(command: list[str]) -> None:
    subprocess.run(command, check=True)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="3 Phone Battery Tips")
    parser.add_argument("--script", default="Three simple phone battery tips. First, avoid extreme heat. Second, turn on optimized charging if your phone supports it. Third, reduce screen brightness when possible. Subscribe to Tony's Tech Talk Takes for more tech tips!")
    parser.add_argument("--format", choices=("short", "long"), default="short")
    parser.add_argument("--audio-file", help="Use existing narration audio (for renderer smoke tests)")
    parser.add_argument("--captions-file", help="Use existing VTT captions (for renderer smoke tests)")
    args = parser.parse_args()
    title = args.title.strip()
    script = args.script.strip()
    if not title or not script:
        raise SystemExit("Title and narration script must not be empty.")
    if len(script.split()) > (450 if args.format == "short" else 2400):
        raise SystemExit("Narration is too long for the selected format; shorten the script.")
    audio = Path(args.audio_file or "voice.mp3")
    vtt = Path(args.captions_file or "voice.vtt")
    if not args.audio_file or not args.captions_file:
        run([sys.executable, "-m", "edge_tts", "--voice", VOICE, "--rate=-5%", "--text", script, "--write-media", str(audio), "--write-subtitles", str(vtt)])
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(audio)], check=True, capture_output=True, text=True)
    duration = max(1.0, float(probe.stdout.strip()))
    if args.format == "short":
        width, height, fps = 720, 1280, 30
        title_y, brand_y, font, title_size = 290, 95, 29, 53
    else:
        width, height, fps = 1920, 1080, 30
        title_y, brand_y, font, title_size = 245, 80, 36, 82
    write_ass(vtt, Path("captions.ass"), width, height)
    Path("title.txt").write_text(textwrap.fill(title, width=22 if height > width else 42), encoding="utf-8")
    Path("brand.txt").write_text("TONY'S TECH TALK TAKES", encoding="utf-8")
    Path("outro.txt").write_text("FOLLOW FOR SMARTER TECH", encoding="utf-8")
    Path("_render").mkdir(exist_ok=True)
    vf = (
        f"drawbox=x=0:y=0:w=iw:h=14:color=0x20D9F3@0.95:t=fill,"
        f"drawbox=x='t*100-trunc(t*100/iw)*iw':y=0:w=iw/3:h=14:color=0xFFFFFF@0.18:t=fill,"
        f"drawbox=x=36:y={brand_y+38}:w=iw-72:h=2:color=0x20D9F3@0.60:t=fill,"
        f"drawbox=x=0:y=ih-46:w='(iw-72)*t/{duration:.3f}':h=8:color=0x20D9F3@0.95:t=fill,"
        f"drawbox=x=0:y={title_y-18}:w='iw*(0.45-t)/0.45':h={title_size+36}:color=0x20D9F3@0.18:t=fill:enable='lt(t,0.45)',"
        f"drawtext=textfile=brand.txt:font='DejaVu Sans':fontsize={font}:fontcolor=white:x=(w-text_w)/2:y={brand_y},"
        f"drawtext=textfile=title.txt:font='DejaVu Sans':fontsize={title_size}:fontcolor=0x20D9F3:borderw=2:bordercolor=0x081426:x=(w-text_w)/2:y={title_y},ass=captions.ass"
    )
    main_output = "_render/tonys-tech-main.mp4"
    output = "tonys-tech-short.mp4" if args.format == "short" else "tonys-tech-long.mp4"
    run(["ffmpeg", "-hide_banner", "-y", "-f", "lavfi", "-i", f"color=c=0x081426:s={width}x{height}:r={fps}:d={duration:.3f}", "-i", str(audio), "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", main_output])
    outro_duration = 2.6
    outro_vf = (
        "drawbox=x=0:y=0:w=iw:h=14:color=0x20D9F3@0.95:t=fill,"
        "drawbox=x='t*150-trunc(t*150/iw)*iw':y=0:w=iw/3:h=14:color=0xFFFFFF@0.20:t=fill,"
        f"drawbox=x=72:y=h/2-8:w=iw-144:h=2:color=0x20D9F3@0.8:t=fill,"
        f"drawtext=textfile=brand.txt:font='DejaVu Sans':fontsize={font}:fontcolor=white:x=(w-text_w)/2:y=h/2-92,"
        f"drawtext=textfile=outro.txt:font='DejaVu Sans':fontsize={font}:fontcolor=0xFFE066:x=(w-text_w)/2:y=h/2+36"
    )
    run(["ffmpeg", "-hide_banner", "-y", "-f", "lavfi", "-i", f"color=c=0x081426:s={width}x{height}:r={fps}:d={outro_duration}", "-vf", outro_vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-an", "_render/tonys-tech-outro.mp4"])
    run(["ffmpeg", "-hide_banner", "-y", "-i", main_output, "-i", "_render/tonys-tech-outro.mp4", "-filter_complex", f"[0:v]settb=AVTB,setpts=PTS-STARTPTS,fps={fps},format=yuv420p[v0];[1:v]settb=AVTB,setpts=PTS-STARTPTS,fps={fps},format=yuv420p[v1];[v0][v1]xfade=transition=slideleft:duration=0.55:offset={max(0,duration-0.55):.3f}[v];[0:a]afade=t=out:st={max(0,duration-0.8):.3f}:d=0.8,apad=pad_dur={outro_duration}[a]", "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", output])
    print(f"Rendered {output} ({width}x{height}, narration {duration:.1f}s plus branded ending, {VOICE})")

if __name__ == "__main__":
    main()
