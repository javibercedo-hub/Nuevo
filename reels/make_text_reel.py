#!/usr/bin/env python3
"""
make_text_reel.py - render a text-only Instagram Reel (1080x1920, 30 fps, MP4)
from a beats.json file. No camera, no voice: animated on-screen text over a
moving pharmacy-green background. Add the music inside Instagram when posting.

beats.json
  {
    "label": "FARMACIA · SANTANDER",          # small line at the top
    "hold_last": 1.5,                          # extra seconds on the last beat
    "beats": [
      {"text": "Me piden *10* antibióticos sin receta por semana."},
      {"text": "A los 10, *no.*", "dur": 2.0}  # optional fixed duration
    ]
  }
  *word* is drawn in the accent colour. Without "dur", a beat lasts
  max(2.2s, words / 2.75 + 0.6s): the speaking rate of beats.py plus reading time.

Usage
  python3 make_text_reel.py beats.json out.mp4
  python3 make_text_reel.py beats.json out.mp4 --preview sheet.png   # also a contact sheet
"""

import argparse
import json
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
# Instagram safe zone: nothing above y=230 or below y=1440, right 230 px clear.
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 230, 1440, 230
LEFT = 90
TEXT_W = W - SAFE_RIGHT - LEFT

FONT_DIR = "/usr/share/fonts/opentype/inter/"
FONT_BOLD = FONT_DIR + "InterDisplay-ExtraBold.otf"
FONT_LABEL = FONT_DIR + "Inter-SemiBold.otf"

BG_TOP = (9, 52, 39)
BG_BOTTOM = (16, 96, 70)
WHITE = (255, 255, 255)
ACCENT = (124, 242, 176)


def beat_duration(beat):
    if "dur" in beat:
        return float(beat["dur"])
    n = len(beat["text"].replace("*", "").split())
    return max(2.2, n / 2.75 + 0.6)


def tokens(text):
    """'Me piden *10* ...' -> [('Me', False), ('piden', False), ('10', True), ...]"""
    out, on = [], False
    for raw in text.split():
        n = raw.count("*")
        out.append((raw.replace("*", ""), on or n > 0))
        if n % 2:                        # a *span* opens or closes in this word
            on = not on
    return out


def layout(text, max_h):
    """Wrap words into lines, shrinking the font until the block fits."""
    toks = tokens(text)
    for size in range(104, 50, -4):
        font = ImageFont.truetype(FONT_BOLD, size)
        space = font.getlength(" ")
        lines, cur, cur_w = [], [], 0.0
        for word, acc in toks:
            w = font.getlength(word)
            if cur and cur_w + space + w > TEXT_W:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur.append((word, acc, w))
            cur_w += (space if len(cur) > 1 else 0) + w
        if cur:
            lines.append(cur)
        line_h = int(size * 1.18)
        if len(lines) * line_h <= max_h and all(
                sum(w for _, _, w in ln) + space * (len(ln) - 1) <= TEXT_W for ln in lines):
            return font, space, lines, line_h
    return font, space, lines, line_h


def make_background():
    bg = Image.new("RGB", (W, H))
    px = bg.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = c
    return bg


def make_cross(size=900, arm=0.32):
    """Outline of a pharmacy cross on a transparent layer, padded so it can
    rotate without its arms being clipped."""
    pad = int(size * 0.25)
    layer = Image.new("RGBA", (size + 2 * pad, size + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a, b = size * (0.5 - arm / 2), size * (0.5 + arm / 2)
    pts = [(x + pad, y + pad) for x, y in
           [(a, 0), (b, 0), (b, a), (size, a), (size, b), (b, b), (b, size),
            (a, size), (a, b), (0, b), (0, a), (a, a)]]
    d.polygon(pts, outline=(255, 255, 255, 34), width=18)
    return layer


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def render_frame(bg, cross, label_font, beat_layout, t_local, dur, t_global, total, label):
    frame = bg.copy().convert("RGBA")

    # Moving first frame: the cross turns slowly the whole time.
    rot = cross.rotate(t_global * 7, resample=Image.BICUBIC, expand=False)
    frame.alpha_composite(rot, (int(W * 0.42) - 225, int(H * 0.62) - 225))

    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    # Top label and progress bar, inside the safe zone.
    d.text((LEFT, SAFE_TOP + 20), label, font=label_font, fill=(255, 255, 255, 170))
    bar_y = SAFE_TOP + 80
    d.rounded_rectangle((LEFT, bar_y, LEFT + TEXT_W, bar_y + 8), 4, fill=(255, 255, 255, 50))
    d.rounded_rectangle((LEFT, bar_y, LEFT + int(TEXT_W * min(1, t_global / total)), bar_y + 8),
                        4, fill=ACCENT + (230,))

    font, space, lines, line_h = beat_layout
    block_h = len(lines) * line_h
    area_top, area_bot = SAFE_TOP + 140, SAFE_BOTTOM - 40
    y0 = area_top + (area_bot - area_top - block_h) / 2

    fade_out = 1.0 - ease_out((t_local - (dur - 0.22)) / 0.22) if t_local > dur - 0.22 else 1.0
    i = 0
    for li, line in enumerate(lines):
        x = LEFT
        for word, acc, w in line:
            p = ease_out((t_local - i * 0.07) / 0.28)       # words come in one by one
            alpha = int(255 * p * fade_out)
            dy = (1 - p) * 36
            colour = (ACCENT if acc else WHITE) + (alpha,)
            d.text((x, y0 + li * line_h + dy), word, font=font, fill=colour)
            x += w + space
            i += 1

    frame.alpha_composite(over)
    return frame.convert("RGB")


def main():
    ap = argparse.ArgumentParser(description="Render a text-only Reel from beats.json.")
    ap.add_argument("beats")
    ap.add_argument("out")
    ap.add_argument("--preview", help="also write a contact sheet PNG")
    args = ap.parse_args()

    spec = json.load(open(args.beats, encoding="utf-8"))
    beats = spec["beats"]
    durs = [beat_duration(b) for b in beats]
    durs[-1] += float(spec.get("hold_last", 1.5))
    total = sum(durs)
    label = spec.get("label", "")

    bg = make_background()
    cross = make_cross()
    label_font = ImageFont.truetype(FONT_LABEL, 34)
    layouts = [layout(b["text"], SAFE_BOTTOM - SAFE_TOP - 260) for b in beats]

    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", args.out],
        stdin=subprocess.PIPE)

    thumbs = []
    n_frames = int(round(total * FPS))
    starts = [sum(durs[:i]) for i in range(len(durs))]
    for f in range(n_frames):
        t = f / FPS
        k = max(i for i, s in enumerate(starts) if s <= t)
        t_local = t - starts[k]
        img = render_frame(bg, cross, label_font, layouts[k], t_local, durs[k], t, total, label)
        ff.stdin.write(img.tobytes())
        if args.preview and len(thumbs) == k and t_local >= min(1.4, durs[k] - 0.3):
            thumbs.append(img.resize((270, 480)))
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg failed")

    if args.preview:
        cols = 6
        rows = math.ceil(len(thumbs) / cols)
        sheet = Image.new("RGB", (cols * 270, rows * 480), (0, 0, 0))
        for i, th in enumerate(thumbs):
            sheet.paste(th, ((i % cols) * 270, (i // cols) * 480))
        sheet.save(args.preview)

    print(f"{args.out}: {len(beats)} beats, {total:.1f}s, {n_frames} frames")


if __name__ == "__main__":
    main()
