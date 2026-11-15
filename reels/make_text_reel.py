#!/usr/bin/env python3
"""
make_text_reel.py - render a text-only Instagram Reel (1080x1920, 30 fps, MP4)
from a beats.json file. No camera, no voice: animated on-screen text in the
upper half and a small animation about what the beat says in the lower half.
Add the music inside Instagram when posting.

beats.json
  {
    "label": "FARMACIA DE LA ESPERANZA · SANTANDER",   # small line at the top
    "logo": "../assets/logo-esperanza.png",           # used by the "logo" animation
    "hold_last": 1.5,                                  # extra seconds on the last beat
    "beats": [
      {"text": "Me piden *10* antibióticos sin receta por semana.", "anim": "pills10"},
      {"text": "A los 10, *no.*", "dur": 2.0, "anim": "pills10_no"}
    ]
  }

  *word* or *several words* are drawn in the accent colour; join words with a
  non-breaking space ("Ni\u00a0yo.") to keep them on one line. Without "dur", a
  beat lasts max(2.2s, words / 2.75 + 0.6s): the speaking rate of beats.py
  plus reading time. "anim" is one of ANIMATIONS below, or omitted.

Usage
  python3 make_text_reel.py beats.json out.mp4
  python3 make_text_reel.py beats.json out.mp4 --preview sheet.png
"""

import argparse
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
# Instagram safe zone: nothing above y=230 or below y=1440, right 230 px clear.
SAFE_TOP, SAFE_BOTTOM, SAFE_RIGHT = 230, 1440, 230
LEFT = 90
TEXT_W = W - SAFE_RIGHT - LEFT
TEXT_TOP, TEXT_BOTTOM = SAFE_TOP + 150, 960        # upper half: the words
ANIM_BOX = (LEFT, 1000, LEFT + TEXT_W, 1420)        # lower half: the animation
SS = 2                                              # animation supersampling
AW, AH = (ANIM_BOX[2] - ANIM_BOX[0]) * SS, (ANIM_BOX[3] - ANIM_BOX[1]) * SS

FONT_DIR = "/usr/share/fonts/opentype/inter/"
FONT_BOLD = FONT_DIR + "InterDisplay-ExtraBold.otf"
FONT_LABEL = FONT_DIR + "Inter-SemiBold.otf"

BG_TOP = (9, 52, 39)
BG_BOTTOM = (16, 96, 70)
WHITE = (255, 255, 255)
ACCENT = (124, 242, 176)
BLUE = (3, 100, 255)          # logo blue (mortar)
GREEN = (21, 159, 107)        # logo green (lettering)
LED = (70, 235, 100)
BACTERIA = (160, 225, 90)
VIRUS = (255, 128, 110)
RED = (255, 85, 85)
PAPER = (248, 250, 248)
GREY = (190, 200, 196)


# ---------------------------------------------------------------- text

def beat_duration(beat):
    if "dur" in beat:
        return float(beat["dur"])
    n = len(beat["text"].replace("*", "").split())
    return max(2.2, n / 2.75 + 0.6)


def tokens(text):
    """'dijo: *«El jefe me lo da».*' -> [(word, accented), ...]; spans may cross words."""
    out, on = [], False
    for raw in text.split(" "):          # a non-breaking space keeps words together
        if not raw:
            continue
        n = raw.count("*")
        out.append((raw.replace("*", ""), on or n > 0))
        if n % 2:                        # a *span* opens or closes in this word
            on = not on
    return out


def layout(text, max_h):
    """Wrap words into lines, shrinking the font until the block fits."""
    toks = tokens(text)
    for size in range(100, 50, -4):
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
            break
    return font, space, lines, line_h


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def inv_ease_in_out(y):
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if ease_in_out(mid) < y:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- shapes
# All drawn on the supersampled animation layer (AW x AH). `a` is 0..1 opacity.

def rgba(c, a):
    return c + (int(255 * max(0.0, min(1.0, a))),)


def _xf(pts, cx, cy, ang):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    return [(cx + x * ca - y * sa, cy + x * sa + y * ca) for x, y in pts]


def stadium(cx, cy, L, Wd, ang, part="full"):
    r = Wd / 2
    half = L / 2 - r
    right = [(half + r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
             for a in range(-90, 91, 6)]
    left = [(-half + r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))
            for a in range(90, 271, 6)]
    if part == "right":
        pts = right + [(0, r), (0, -r)]
    elif part == "left":
        pts = left + [(0, -r), (0, r)]
    else:
        pts = right + left
    return _xf(pts, cx, cy, ang)


def capsule(d, cx, cy, L, Wd, ang, a=1.0, scale=1.0):
    L, Wd = L * scale, Wd * scale
    if L < 4:
        return
    d.polygon(stadium(cx, cy, L, Wd, ang, "left"), fill=rgba(BLUE, a))
    d.polygon(stadium(cx, cy, L, Wd, ang, "right"), fill=rgba(WHITE, a))
    d.line(_xf([(-L * 0.3, -Wd * 0.22), (-L * 0.08, -Wd * 0.22)], cx, cy, ang),
           fill=rgba(WHITE, a * 0.55), width=max(2, int(Wd * 0.09)))


def bacterium(d, cx, cy, L, Wd, ang, a=1.0, wiggle=0.0, scale=1.0):
    L, Wd = L * scale, Wd * scale
    if L < 4:
        return
    tail = [(-L / 2 - k * Wd * 0.18, math.sin(k * 0.9 + wiggle) * Wd * 0.18) for k in range(9)]
    d.line(_xf(tail, cx, cy, ang), fill=rgba(BACTERIA, a * 0.8), width=max(2, int(Wd * 0.07)))
    d.polygon(stadium(cx, cy, L, Wd, ang), fill=rgba(BACTERIA, a))
    for px, py in [(-L * 0.18, -Wd * 0.12), (L * 0.12, Wd * 0.1), (L * 0.28, -Wd * 0.08)]:
        (x, y), = _xf([(px, py)], cx, cy, ang)
        rr = Wd * 0.09
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rgba((90, 160, 50), a))


def virus(d, cx, cy, r, rot, a=1.0):
    for k in range(10):
        ang = math.radians(rot + k * 36)
        x1, y1 = cx + math.cos(ang) * r, cy + math.sin(ang) * r
        x2, y2 = cx + math.cos(ang) * r * 1.38, cy + math.sin(ang) * r * 1.38
        d.line((x1, y1, x2, y2), fill=rgba(VIRUS, a), width=max(2, int(r * 0.1)))
        kr = r * 0.13
        d.ellipse((x2 - kr, y2 - kr, x2 + kr, y2 + kr), fill=rgba(VIRUS, a))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(VIRUS, a))
    d.ellipse((cx - r * 0.55, cy - r * 0.55, cx + r * 0.1, cy + r * 0.1),
              fill=rgba((255, 170, 158), a))


def burst(d, cx, cy, p, size=120, a=1.0, colour=WHITE):
    if p <= 0 or p >= 1:
        return
    for k in range(8):
        ang = math.radians(k * 45 + 22)
        r1, r2 = size * (0.3 + 0.6 * p), size * (0.55 + 0.8 * p)
        d.line((cx + math.cos(ang) * r1, cy + math.sin(ang) * r1,
                cx + math.cos(ang) * r2, cy + math.sin(ang) * r2),
               fill=rgba(colour, a * (1 - p)), width=10)


def ring(d, cx, cy, r, a=1.0, colour=BLUE, width=16):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=rgba(colour, a), width=width)


def cross_x(d, cx, cy, size, p, a=1.0):
    """Red X drawn stroke by stroke as p goes 0 -> 1."""
    s = size / 2
    p1, p2 = min(1, p * 2), max(0, p * 2 - 1)
    if p1 > 0:
        d.line((cx - s, cy - s, cx - s + 2 * s * p1, cy - s + 2 * s * p1),
               fill=rgba(RED, a), width=int(size * 0.13))
    if p2 > 0:
        d.line((cx + s, cy - s, cx + s - 2 * s * p2, cy - s + 2 * s * p2),
               fill=rgba(RED, a), width=int(size * 0.13))


def pharmacy_cross(d, cx, cy, size, colour, a=1.0):
    t = size / 3
    d.rectangle((cx - t / 2, cy - size / 2, cx + t / 2, cy + size / 2), fill=rgba(colour, a))
    d.rectangle((cx - size / 2, cy - t / 2, cx + size / 2, cy + t / 2), fill=rgba(colour, a))


# ---------------------------------------------------------------- animations
# Each one: f(d, t, dur, a, ctx) drawing on the AW x AH layer.

def _grid10(i):
    row, col = divmod(i, 5)
    return 190 + col * 285, 240 + row * 360


def anim_pills10(d, t, dur, a, ctx):
    for i in range(10):
        cx, cy = _grid10(i)
        p = ease_out((t - 0.12 * i) / 0.3)
        capsule(d, cx, cy + math.sin(t * 3 + i) * 8, 210, 84, -32, a * p, scale=0.6 + 0.4 * p)


def anim_pills10_no(d, t, dur, a, ctx):
    for i in range(10):
        cx, cy = _grid10(i)
        capsule(d, cx, cy, 210, 84, -32, a * 0.85)
        cross_x(d, cx, cy, 170, ease_out((t - 0.08 * i) / 0.25), a)


def anim_bubble(d, t, dur, a, ctx):
    p = ease_out(t / 0.35)
    x0, y0, x1, y1 = 160, 110 + (1 - p) * 60, 1360, 620 + (1 - p) * 60
    d.rounded_rectangle((x0, y0, x1, y1), 70, fill=rgba(PAPER, a * p))
    d.polygon([(330, y1 - 2), (300, y1 + 150), (470, y1 - 2)], fill=rgba(PAPER, a * p))
    cy = (y0 + y1) / 2
    if t < 0.9:                                    # typing dots
        for k in range(3):
            on = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 9 - k * 0.9))
            cx, r = 640 + k * 120, 26
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(GREY, a * p * on))
    else:                                          # asking for the pill
        q = ease_out((t - 0.9) / 0.3)
        capsule(d, 610, cy, 300, 120, -25, a * q, scale=0.7 + 0.3 * q)
        d.text((900, cy), "?", font=ctx["font_anim"], fill=rgba(BLUE, a * q), anchor="mm")


def anim_lock(d, t, dur, a, ctx):
    cx, cy = AW / 2 - 120, 400
    d.rounded_rectangle((cx - 360, cy - 150, cx + 360, cy + 300), 40, fill=rgba(PAPER, a))
    pharmacy_cross(d, cx - 210, cy + 75, 150, GREEN, a)
    for k in range(3):
        d.rounded_rectangle((cx - 60, cy - 10 + k * 80, cx + 280, cy + 30 + k * 80), 20,
                            fill=rgba(GREY, a))
    # padlock: the shackle drops shut
    drop = ease_in_out((t - 0.4) / 0.35)
    lx, ly = cx + 400, cy + 40
    sh = 80 * (1 - drop)
    d.arc((lx - 95, ly - 200 - sh, lx + 95, ly - 10 - sh), 180, 360, fill=rgba(BLUE, a), width=34)
    d.line((lx - 78, ly - 105 - sh, lx - 78, ly + 10), fill=rgba(BLUE, a), width=34)
    d.line((lx + 78, ly - 105 - sh, lx + 78, ly - 30 * (1 - drop) + 10), fill=rgba(BLUE, a), width=34)
    d.rounded_rectangle((lx - 140, ly - 10, lx + 140, ly + 200), 30, fill=rgba(BLUE, a))
    d.ellipse((lx - 26, ly + 55, lx + 26, ly + 107), fill=rgba(WHITE, a))
    d.rectangle((lx - 10, ly + 95, lx + 10, ly + 150), fill=rgba(WHITE, a))
    burst(d, lx, ly - 60, (t - 0.75) / 0.4, size=200, a=a)


def _row_positions(n=5):
    return [(170 + i * 295, 420 + (70 if i % 2 else -70)) for i in range(n)]


def _capsule_x(t, dur):
    return -200 + (AW + 400) * ease_in_out(t / (dur * 0.9))


def anim_kill_bacteria(d, t, dur, a, ctx):
    for i, (bx, by) in enumerate(_row_positions()):
        t_hit = dur * 0.9 * inv_ease_in_out((bx + 200) / (AW + 400))
        by += math.sin(t * 2.5 + i) * 12
        if t < t_hit:
            bacterium(d, bx, by, 200, 90, 15 + i * 30, a, wiggle=t * 8)
        else:
            q = (t - t_hit) / 0.35
            if q < 1:
                bacterium(d, bx, by, 200, 90, 15 + i * 30, a * (1 - q), scale=1 - 0.6 * q)
            burst(d, bx, by, q, size=150, a=a, colour=ACCENT)
    capsule(d, _capsule_x(t, dur), 420, 300, 120, 0, a)


def anim_virus_pass(d, t, dur, a, ctx):
    for i, (vx, vy) in enumerate(_row_positions()):
        virus(d, vx, vy + math.sin(t * 2 + i) * 14, 70, t * 40 + i * 20, a)
    capsule(d, _capsule_x(t, dur), 420, 300, 120, 0, a * 0.9)


def anim_resist(d, t, dur, a, ctx):
    for i, (bx, by) in enumerate(_row_positions()):
        by += math.sin(t * 2.5 + i) * 12
        bacterium(d, bx, by, 200, 90, 15 + i * 30, a, wiggle=t * 8)
        p = ease_out((t - 0.4 - 0.3 * i) / 0.35)
        if p > 0:
            ring(d, bx, by, 140 * (0.6 + 0.4 * p), a * p, BLUE, 18)
            ring(d, bx, by, 160 * (0.6 + 0.4 * p), a * p * 0.35, BLUE, 10)


def anim_bounce(d, t, dur, a, ctx):
    bx, by = 1150, 420
    bacterium(d, bx, by, 330, 150, -10, a, wiggle=t * 8)
    ring(d, bx, by, 250, a, BLUE, 22)
    ring(d, bx, by, 280, a * 0.35, BLUE, 12)
    t_hit = dur * 0.4
    if t < t_hit:
        x = -150 + (bx - 450 + 150) * ease_in_out(t / t_hit)
        capsule(d, x, by, 300, 120, 0, a)
    else:
        q = (t - t_hit) / (dur - t_hit)
        x = bx - 450 - 480 * ease_out(q)
        capsule(d, x, by + 160 * ease_out(q), 300, 120, -120 * ease_out(q), a)
        burst(d, bx - 270, by, (t - t_hit) / 0.4, size=150, a=a)


def anim_prescription(d, t, dur, a, ctx):
    p = ease_out(t / 0.4)
    x0, y0 = 400, 50 + (1 - p) * 300
    x1, y1 = 1060, y0 + 720
    d.rounded_rectangle((x0, y0, x1, y1), 30, fill=rgba(PAPER, a * p))
    d.text((x0 + 60, y0 + 40), "Rx", font=ctx["font_anim"], fill=rgba(BLUE, a * p))
    for k in range(4):
        q = ease_out((t - 0.4 - 0.18 * k) / 0.3)
        y = y0 + 300 + k * 85
        if q > 0:
            d.rounded_rectangle((x0 + 60, y, x0 + 60 + (520 - k * 70) * q, y + 26), 13,
                                fill=rgba(GREY, a * p))
    s = ease_out((t - 1.3) / 0.3)
    if s > 0:
        sx, sy, r = x1 - 30, y1 - 80, 120 * (1.6 - 0.6 * s)
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=rgba(GREEN, a * s))
        d.line([(sx - r * 0.45, sy), (sx - r * 0.1, sy + r * 0.38), (sx + r * 0.5, sy - r * 0.35)],
               fill=rgba(WHITE, a * s), width=int(r * 0.17), joint="curve")


LED_CELLS = [(c, r) for r in range(7) for c in range(7) if 2 <= c <= 4 or 2 <= r <= 4]


def anim_led_cross(d, t, dur, a, ctx):
    cell, gap = 100, 16
    size = 7 * cell
    x0, y0 = AW / 2 - size / 2, AH / 2 - size / 2
    blink = 1.0 if t < 1.4 else 0.55 + 0.45 * (0.5 + 0.5 * math.cos((t - 1.4) * 7))
    for c, r in LED_CELLS:
        on = ease_out((t - math.hypot(c - 3, r - 3) * 0.12) / 0.2) * blink
        x, y = x0 + c * cell, y0 + r * cell
        d.rounded_rectangle((x - 6, y - 6, x + cell - gap + 6, y + cell - gap + 6), 16,
                            fill=rgba(LED, a * on * 0.25))
        d.rounded_rectangle((x, y, x + cell - gap, y + cell - gap), 12,
                            fill=rgba(LED, a * (0.12 + 0.88 * on)))


def anim_no_sign(d, t, dur, a, ctx):
    cx, cy = AW / 2, AH / 2
    capsule(d, cx, cy, 460, 180, -30, a)
    r = 340
    p = ease_out(t / 0.6)
    if p > 0:
        d.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * p, fill=rgba(RED, a), width=46)
    q = ease_out((t - 0.55) / 0.3)
    if q > 0:
        s = r * 0.707
        d.line((cx - s, cy - s, cx - s + 2 * s * q, cy - s + 2 * s * q), fill=rgba(RED, a), width=46)


def anim_logo(d, t, dur, a, ctx):
    p = ease_out(t / 0.5)
    r = 400 * (0.75 + 0.25 * p)
    cx, cy = AW / 2, AH / 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=rgba(WHITE, a * p))
    logo = ctx.get("logo")
    if logo is not None:
        side = int(2 * r * 0.98)
        lg = logo.resize((side, int(side * logo.height / logo.width)), Image.LANCZOS)
        if a * p < 1:
            lg.putalpha(lg.getchannel("A").point(lambda v: int(v * a * p)))
        ctx["layer"].alpha_composite(lg, (int(cx - lg.width / 2), int(cy - lg.height / 2)))


ANIMATIONS = {
    "pills10": anim_pills10, "pills10_no": anim_pills10_no, "bubble": anim_bubble,
    "lock": anim_lock, "kill_bacteria": anim_kill_bacteria, "virus_pass": anim_virus_pass,
    "resist": anim_resist, "bounce": anim_bounce, "prescription": anim_prescription,
    "led_cross": anim_led_cross, "no_sign": anim_no_sign, "logo": anim_logo,
}


# ---------------------------------------------------------------- frames

def make_background():
    col = Image.new("RGB", (1, H))
    for y in range(H):
        t = y / (H - 1)
        col.putpixel((0, y), tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)))
    return col.resize((W, H))


def render_frame(bg, ctx, beat, beat_layout, t_local, dur, t_global, total, label):
    frame = bg.copy().convert("RGBA")
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)

    # Top label and progress bar, inside the safe zone.
    d.text((LEFT, SAFE_TOP + 20), label, font=ctx["font_label"], fill=(255, 255, 255, 170))
    bar_y = SAFE_TOP + 80
    d.rounded_rectangle((LEFT, bar_y, LEFT + TEXT_W, bar_y + 8), 4, fill=(255, 255, 255, 50))
    d.rounded_rectangle((LEFT, bar_y, LEFT + int(TEXT_W * min(1, t_global / total)), bar_y + 8),
                        4, fill=ACCENT + (230,))

    fade_out = 1.0 - ease_out((t_local - (dur - 0.22)) / 0.22) if t_local > dur - 0.22 else 1.0

    font, space, lines, line_h = beat_layout
    i = 0
    for li, line in enumerate(lines):
        x = LEFT
        for word, acc, w in line:
            p = ease_out((t_local - i * 0.07) / 0.28)       # words come in one by one
            colour = (ACCENT if acc else WHITE) + (int(255 * p * fade_out),)
            d.text((x, TEXT_TOP + li * line_h + (1 - p) * 36), word, font=font, fill=colour)
            x += w + space
            i += 1
    frame.alpha_composite(over)

    anim = ANIMATIONS.get(beat.get("anim", ""))
    if anim:
        layer = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
        ctx["layer"] = layer
        a = ease_out(t_local / 0.25) * fade_out
        anim(ImageDraw.Draw(layer), t_local, dur, a, ctx)
        small = layer.resize((AW // SS, AH // SS), Image.LANCZOS)
        frame.alpha_composite(small, (ANIM_BOX[0], ANIM_BOX[1]))
    return frame.convert("RGB")


def main():
    ap = argparse.ArgumentParser(description="Render a text-only Reel from beats.json.")
    ap.add_argument("beats")
    ap.add_argument("out")
    ap.add_argument("--preview", help="also write a contact sheet PNG")
    args = ap.parse_args()

    spec = json.load(open(args.beats, encoding="utf-8"))
    beats = spec["beats"]
    unknown = [b["anim"] for b in beats if b.get("anim") and b["anim"] not in ANIMATIONS]
    if unknown:
        sys.exit(f"unknown animation(s): {', '.join(unknown)}. Known: {', '.join(ANIMATIONS)}")

    durs = [beat_duration(b) for b in beats]
    durs[-1] += float(spec.get("hold_last", 1.5))
    total = sum(durs)
    label = spec.get("label", "")

    ctx = {"font_anim": ImageFont.truetype(FONT_BOLD, 190)}
    size = 34
    while True:
        ctx["font_label"] = ImageFont.truetype(FONT_LABEL, size)
        if ctx["font_label"].getlength(label) <= TEXT_W or size <= 22:
            break
        size -= 2
    if spec.get("logo"):
        path = os.path.join(os.path.dirname(os.path.abspath(args.beats)), spec["logo"])
        logo = Image.open(path).convert("RGBA")
        ctx["logo"] = logo.crop(logo.getbbox())

    bg = make_background()
    layouts = [layout(b["text"], TEXT_BOTTOM - TEXT_TOP) for b in beats]

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
        img = render_frame(bg, ctx, beats[k], layouts[k], t_local, durs[k], t, total, label)
        ff.stdin.write(img.tobytes())
        if args.preview and len(thumbs) == k and t_local >= min(1.6, durs[k] - 0.3):
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
