#!/usr/bin/env python3
"""Burn word-by-word subtitles into video using ffmpeg pipes + Pillow."""
import subprocess
import sys
import re
import time
from PIL import Image, ImageDraw, ImageFont

# ── Config ──────────────────────────────────────────────────────────────────
INPUT_VIDEO  = "/Users/vas/CLAUDECODE/IMG_9075.MOV"
OUTPUT_VIDEO = "/Users/vas/CLAUDECODE/final_with_subtitles.mp4"
SRT_FILE     = "/Users/vas/CLAUDECODE/subtitles_word_by_word.srt"
FONT_PATH    = "/Users/vas/Library/Fonts/BebasNeue-Bold.ttf"
FONT_SIZE    = 90
TEXT_COLOR   = (0, 255, 255)        # cyan
OUTLINE_W    = 5                    # black outline width px
SHADOW_OFF   = 4                    # shadow offset px
SHADOW_COLOR = (0, 0, 0, 150)      # semi-transparent black shadow

# ── Get output frame dimensions (ffmpeg auto-rotates phone video) ───────────
# Use a probe frame to get actual decoded dimensions
probe_cmd = [
    "ffmpeg", "-i", INPUT_VIDEO, "-vframes", "1",
    "-f", "rawvideo", "-pix_fmt", "rgba", "-ss", "1",
    "pipe:1", "-loglevel", "error"
]
# Just get one frame and check its size by getting display width/height via ffprobe
probe = subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0",
     "-show_entries", "stream=width,height,r_frame_rate",
     "-show_entries", "format=duration",
     "-of", "default=nw=1", INPUT_VIDEO],
    capture_output=True, text=True
)
info = {}
for line in probe.stdout.strip().splitlines():
    if '=' in line:
        k, v = line.split('=', 1)
        info[k] = v

stored_w = int(info.get('width', 1920))
stored_h = int(info.get('height', 1080))
fps_str  = info.get('r_frame_rate', '60/1')
fps_n, fps_d = fps_str.split('/')
FPS = float(fps_n) / float(fps_d)
duration = float(info.get('duration', 54))

# ffmpeg auto-applies rotation: if stored is landscape with -90 rotate tag → output is portrait
# verify by checking which dim is larger in stored
if stored_w > stored_h:
    # stored landscape, will be rotated to portrait
    WIDTH, HEIGHT = stored_h, stored_w
else:
    WIDTH, HEIGHT = stored_w, stored_h

print(f"Stored: {stored_w}x{stored_h}, Output frames: {WIDTH}x{HEIGHT} @ {FPS:.2f}fps, {duration:.2f}s")

# ── Parse SRT ────────────────────────────────────────────────────────────────
def parse_srt(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    entries = []
    for block in content.strip().split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) < 3:
            continue
        m = re.match(
            r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)",
            lines[1]
        )
        if not m:
            continue
        h1,m1,s1,ms1, h2,m2,s2,ms2 = (int(x) for x in m.groups())
        start = h1*3600 + m1*60 + s1 + ms1/1000
        end   = h2*3600 + m2*60 + s2 + ms2/1000
        text  = " ".join(lines[2:]).strip().upper()
        entries.append((start, end, text))
    return entries

subs = parse_srt(SRT_FILE)
print(f"Subtitles: {len(subs)} entries")

# ── Subtitle lookup ──────────────────────────────────────────────────────────
def get_sub(t):
    for start, end, text in subs:
        if start <= t <= end:
            return text
    return None

# ── Font & text rendering ────────────────────────────────────────────────────
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

def draw_text_styled(draw, text, W, H):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # vertically center, slightly above center (visual balance)
    x = (W - tw) // 2
    y = (H - th) // 2

    # shadow first (behind everything)
    draw.text((x + SHADOW_OFF, y + SHADOW_OFF), text, font=font, fill=SHADOW_COLOR)

    # outline: 8 directions at OUTLINE_W radius
    for dx in range(-OUTLINE_W, OUTLINE_W + 1):
        for dy in range(-OUTLINE_W, OUTLINE_W + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 255))

    # main text (cyan)
    draw.text((x, y), text, font=font, fill=(*TEXT_COLOR, 255))

# ── ffmpeg reader: decoded RGBA frames (auto-rotated) ───────────────────────
frame_size = WIDTH * HEIGHT * 4  # bytes per frame (RGBA)

reader_cmd = [
    "ffmpeg", "-i", INPUT_VIDEO,
    "-f", "rawvideo", "-pix_fmt", "rgba",
    "pipe:1", "-loglevel", "error"
]
reader = subprocess.Popen(reader_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# ── ffmpeg writer ─────────────────────────────────────────────────────────────
writer_cmd = [
    "ffmpeg", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgba",
    "-s", f"{WIDTH}x{HEIGHT}",
    "-r", str(FPS),
    "-i", "pipe:0",
    "-i", INPUT_VIDEO,       # audio source
    "-map", "0:v",
    "-map", "1:a",
    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    "-shortest",
    OUTPUT_VIDEO,
    "-loglevel", "error"
]
writer = subprocess.Popen(writer_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

# ── Process frames ────────────────────────────────────────────────────────────
frame_num = 0
t0 = time.time()

print("Processing frames...")
try:
    while True:
        raw = reader.stdout.read(frame_size)
        if len(raw) < frame_size:
            break

        timestamp = frame_num / FPS
        img  = Image.frombuffer("RGBA", (WIDTH, HEIGHT), raw, "raw", "RGBA", 0, 1)

        text = get_sub(timestamp)
        if text:
            draw = ImageDraw.Draw(img)
            draw_text_styled(draw, text, WIDTH, HEIGHT)

        writer.stdin.write(img.tobytes())
        frame_num += 1

        if frame_num % 120 == 0:
            elapsed  = time.time() - t0
            progress = timestamp / duration * 100
            fps_proc = frame_num / elapsed
            eta      = (duration - timestamp) / (timestamp / elapsed) if timestamp > 0 else 0
            print(f"  {progress:.1f}% | {timestamp:.1f}s/{duration:.0f}s | {fps_proc:.1f} fps | ETA {eta:.0f}s",
                  flush=True)

finally:
    reader.stdout.close()
    writer.stdin.close()
    err_r = reader.stderr.read().decode()
    err_w = writer.stderr.read().decode()
    reader.wait()
    writer.wait()
    if err_r: print("Reader stderr:", err_r[:500])
    if err_w: print("Writer stderr:", err_w[:500])

elapsed = time.time() - t0
print(f"\nDone! {frame_num} frames in {elapsed:.1f}s ({frame_num/elapsed:.1f} fps avg)")
print(f"Output: {OUTPUT_VIDEO}")
