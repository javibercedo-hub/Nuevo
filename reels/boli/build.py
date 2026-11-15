"""Reel animado "el del boli" (Altissia, cotejo de albaranes). 1080x1920, 30 fps, sin voz.

uso: python3 -I build.py VIDEO_ALTISSIA SALIDA.mp4 MUSICA.wav CARPETA_SFX [TIMING.json VOZ.wav]
Sin voz: tiempos por defecto. Con TIMING.json (escenas y marcas sacadas de la locución) y VOZ.wav:
las escenas siguen a la voz, la voz va a -16 LUFS y la música se aparta cuando habla.
Escribe también SALIDA_music.wav, SALIDA_sfx.wav (y SALIDA_voz.wav) y SALIDA.cues.json.
"""
import json, math, os, subprocess, sys
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT, MUSIC, SFX = sys.argv[1:5]
TIMING = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else None
VO = sys.argv[6] if len(sys.argv) > 6 else None
FPS, SR, W, H = 30, 48000, 1080, 1920
FB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
FE = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
NAVY, GREEN, WHITE, RED = (11, 37, 69), (22, 170, 120), (255, 255, 255), (226, 60, 60)
YELLOW, CREAM, CHAOS, CALM = (255, 214, 64), (255, 244, 224), (255, 236, 214), (236, 246, 250)
NOTE = "Casos comunicados por Altissia. Resultados variables."
X0, MAXW = 80, 770                       # zona segura: x 80-850, y 230-1440
TEXT_Y, ART_C = 300, (465, 1060)          # texto arriba, ilustración centrada aquí

# escenas: (inicio, fin, línea de la voz en off, tarjetas [(texto, estilo)], tipo de dibujo)
SCENES = [
    (0.0, 2.9, "Nadie te avisó de los 500 albaranes.", [("Nadie te avisó", "n"), ("de esto", "h")], "tower"),
    (2.9, 4.6, "Cinco años de carrera.", [("5 años", "h"), ("de carrera", "n")], "grad"),
    (4.6, 7.6, "Para acabar comparando precios línea a línea con un boli,", [("Línea a línea", "n"), ("con boli", "h")], "lines"),
    (7.6, 10.4, "un subrayador y un café frío.", [("Y un café", "n"), ("frío", "h")], "coffee"),
    (10.4, 13.4, "Se te escapa un error y adiós margen.", [("Un error y…", "n"), ("adiós margen", "r")], "money"),
    (13.4, 15.0, "Tu compañera usa Altissia.", [("Tu compañera", "n"), ("usa Altissia", "g")], "colleague"),
    (15.0, 18.2, "Más de 500 albaranes en unos 5 segundos.", [("500+ albaranes", "g"), ("en ≈5 segundos", "n")], "laptop"),
    (18.2, 20.3, "Mira solo las diferencias. Café.", [("Solo las diferencias", "n"), ("y a por café", "g")], "diff"),
    (20.3, 22.4, "Tú vas por el 37.", [("Tú vas", "n"), ("por el 37", "r")], "behind"),
    (22.4, 26.0, "Etiqueta a quien sigue cotejando albaranes con boli.", [("Etiqueta al", "n"), ("del boli 🖊", "h")], "cta"),
]
if TIMING:                                # la imagen sigue a la locución
    st = TIMING["scenes"] + [TIMING["end"]]
    SCENES = [(st[i], st[i + 1]) + tuple(s[2:]) for i, s in enumerate(SCENES)]
MARKS = (TIMING or {}).get("marks", {})
TOTAL = SCENES[-1][1]


def rel(key, scene, default):
    """Segundos desde el inicio de la escena hasta la palabra marcada en la voz."""
    return MARKS[key] - SCENES[scene][0] if key in MARKS else default
_fonts, _emoji = {}, {}


def font(path, size):
    return _fonts.setdefault((path, size), ImageFont.truetype(path, size))


def clamp(x):
    return min(max(x, 0.0), 1.0)


def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3


def ease_back(x, s=1.9):
    x = clamp(x); x -= 1; return 1 + (s + 1) * x ** 3 + s * x ** 2


def emoji(ch, size):
    """Emoji en color (Noto se dibuja a 109 px y se escala)."""
    key = (ch, size)
    if key not in _emoji:
        f = font(FE, 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
        im = im.crop(im.getbbox())
        r = size / max(im.size)
        _emoji[key] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _emoji[key]


def paste(base, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def card(text, style, size=96):
    """Tarjeta de texto: n = texto azul, h = caja amarilla, g = caja verde, r = caja roja."""
    has_emoji = "🖊" in text
    t = text.replace("🖊", "").strip()
    f = font(FB, size)
    d = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    tw = d.textlength(t, font=f) + (size + 10 if has_emoji else 0)
    pad = 0 if style == "n" else int(size * 0.22)
    while tw + 2 * pad > MAXW:
        size -= 4; f = font(FB, size); tw = d.textlength(t, font=f) + (size + 10 if has_emoji else 0)
        pad = 0 if style == "n" else int(size * 0.22)
    hh = int(size * 1.3)
    im = Image.new("RGBA", (int(tw + 2 * pad) + 4, hh + 4), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    fg = NAVY
    if style != "n":
        bg = {"h": YELLOW, "g": GREEN, "r": RED}[style]
        dd.rounded_rectangle((0, 0, im.width - 4, hh), int(size * 0.18), fill=bg)
        fg = NAVY if style == "h" else WHITE
    dd.text((pad, hh / 2), t, font=f, fill=fg, anchor="lm")
    if has_emoji:
        e = emoji("🖊", size)
        im.alpha_composite(e, (int(pad + d.textlength(t, font=f) + 10), int((hh - e.height) / 2)))
    return im


def draw_cards(base, cards, t, first):
    y = TEXT_Y
    for i, (text, style) in enumerate(cards):
        im = card(text, style)
        start = 0 if first else 0.06 + i * 0.16
        p = 1.0 if first else ease_back((t - start) / 0.32)   # el gancho, entero desde el fotograma 1
        if p > 0:
            sc = 0.6 + 0.4 * p
            wob = 2.5 * math.sin(t * 5 + i) if style != "n" else 0
            paste(base, im, X0 + im.width / 2, y + im.height / 2, scale=sc, rot=wob * (1 - 0.6 * clamp(t)),
                  alpha=clamp(p * 1.5))
        y += im.height + 18


def doc(w=300, h=380, lines=9, rot=0, done=0, hl=-1, red=-1):
    """Un albarán: hoja con renglones; done = renglones tachados, hl = renglón subrayado, red = error."""
    im = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((8, 10, w + 8, h + 10), 14, fill=(0, 0, 0, 40))
    d.rounded_rectangle((0, 0, w, h), 14, fill=WHITE, outline=(200, 205, 215), width=3)
    d.rectangle((24, 22, w * 0.55, 40), fill=NAVY)
    for i in range(lines):
        y = 70 + i * (h - 90) / lines
        col = (190, 198, 210)
        if i == hl:
            d.rectangle((18, y - 10, w - 18, y + 14), fill=YELLOW + (200,))
        if i == red:
            d.rectangle((18, y - 10, w - 18, y + 14), fill=RED + (90,))
        d.rounded_rectangle((24, y, w * (0.55 + 0.3 * ((i * 37) % 5) / 5), y + 6), 3, fill=col)
        d.rounded_rectangle((w - 80, y, w - 24, y + 6), 3, fill=col)
        if i < done:
            d.line((w - 60, y - 4, w - 50, y + 8, w - 32, y - 10), fill=GREEN, width=5)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    return im


def ground(base, col):
    ImageDraw.Draw(base).ellipse((ART_C[0] - 330, 1370, ART_C[0] + 330, 1420), fill=col)


# ---------- dibujos por escena (t = segundos desde el inicio de la escena) ----------
def art_tower(b, t, d):
    ground(b, (240, 214, 186))
    for i in range(14):                                   # los albaranes caen y se apilan
        land = -0.36 + i * 0.09                          # unas cuantas ya están en el fotograma 1
        p = ease_out((t - land) / 0.25)
        if t < land:
            continue
        y = 1360 - i * 34 - (1 - p) * 320
        if y - 170 < 760:                                 # nunca por encima de la ilustración (el texto va arriba)
            continue
        x = ART_C[0] - 60 + 40 * math.sin(i * 1.7) + 6 * math.sin(t * 9 + i) * (i / 14)
        paste(b, doc(240, 300, lines=6, rot=6 * math.sin(i * 2.3)), x, y)
    sh = 6 * math.sin(t * 40) * clamp(1 - t / 0.5)
    paste(b, emoji("😱", 230), ART_C[0] + 230 + sh, 1250, scale=ease_back(t / 0.3))
    f = font(FB, 120)
    n = int(150 + 350 * ease_out(t / 1.6))
    tag = Image.new("RGBA", (360, 150), (0, 0, 0, 0))
    ImageDraw.Draw(tag).text((180, 75), f"{n}", font=f, fill=RED, anchor="mm")
    paste(b, tag, ART_C[0] - 210, 860, rot=-8)


def art_grad(b, t, d):
    ground(b, (240, 214, 186))
    paste(b, emoji("🎓", 300), ART_C[0], 1080 - 40 * abs(math.sin(t * 6)) * clamp(1 - t / 1.2),
          scale=ease_back(t / 0.35), rot=10 * math.sin(t * 6))
    for i in range(18):                                    # confeti
        a = i * 2.1
        r = 120 + 420 * ease_out(t / 0.9)
        x, y = ART_C[0] + r * math.cos(a), 1080 + r * math.sin(a) * 0.7 + 300 * t * t
        col = [GREEN, YELLOW, RED, (90, 160, 255)][i % 4]
        ImageDraw.Draw(b).rectangle((x, y, x + 18, y + 10), fill=col + (int(255 * clamp(1.4 - t)),))


def art_lines(b, t, d):
    ground(b, (240, 214, 186))
    row = int(t / 0.33) % 9
    paste(b, doc(470, 560, lines=9, done=row, hl=row), ART_C[0], 1080)
    y = 1080 - 280 + 70 + row * (560 - 90) / 9 + 12
    x = ART_C[0] - 200 + 380 * ((t / 0.33) % 1)
    paste(b, emoji("🖊", 150), x + 50, y - 60, rot=-20 + 8 * math.sin(t * 30))
    paste(b, emoji("😩", 170), ART_C[0] + 300, 820, scale=ease_back((t - 0.4) / 0.3))


def art_coffee(b, t, d):
    ground(b, (240, 214, 186))
    paste(b, doc(330, 400, lines=7, done=4, rot=-12), ART_C[0] - 190, 1120)
    shiver = 7 * math.sin(t * 45)
    paste(b, emoji("☕", 280), ART_C[0] + 120 + shiver, 1150, scale=ease_back(t / 0.3))
    for i in range(5):                                     # copos que caen sobre el café
        y = 820 + ((t * 260 + i * 110) % 420)
        paste(b, emoji("❄", 60), ART_C[0] + 20 + i * 55, y, alpha=0.9)
    paste(b, emoji("🥶", 190), ART_C[0] + 260, 830, scale=ease_back((t - rel("frio", 3, 0.6)) / 0.3))


def art_money(b, t, d):
    ground(b, (240, 214, 186))
    paste(b, doc(380, 460, lines=8, red=5), ART_C[0] - 80, 1130)
    stamp = ease_back((t - rel("error", 4, 0.2)) / 0.25, 2.6)
    if stamp > 0:
        tag = Image.new("RGBA", (340, 130), (0, 0, 0, 0))
        dd = ImageDraw.Draw(tag)
        dd.rounded_rectangle((4, 4, 336, 126), 16, outline=RED, width=10)
        dd.text((170, 66), "ERROR", font=font(FB, 84), fill=RED, anchor="mm")
        paste(b, tag, ART_C[0] - 80, 1150, scale=0.6 + 0.4 * stamp, rot=-14)
    for i in range(7):                                     # billetes que se van volando
        s = rel("adios", 4, 0.9) + i * 0.22
        if t < s:
            continue
        p = (t - s) / 1.4
        x = ART_C[0] + 120 + 220 * p + 60 * math.sin(p * 7 + i)
        y = 1200 - 700 * p
        paste(b, emoji("💸", 130), x, y, rot=25 * math.sin(p * 5 + i), alpha=clamp(1.6 - p))


def art_colleague(b, t, d):
    ground(b, (205, 228, 238))
    paste(b, d["logo"], ART_C[0], 1180, scale=0.8 * ease_back((t - 0.25) / 0.35))
    paste(b, emoji("😎", 240), ART_C[0] + 10, 900, scale=ease_back(t / 0.3), rot=8 * math.sin(t * 4))
    for i in range(6):                                     # destellos
        a = i * 1.05 + t * 2
        r = 210 + 15 * math.sin(t * 8 + i)
        paste(b, emoji("✨", 60), ART_C[0] + r * math.cos(a), 900 + r * math.sin(a), alpha=clamp(t * 3))


def laptop(d, screen):
    w, h = 880, 520
    im = Image.new("RGBA", (w + 80, h + 120), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    dd.rounded_rectangle((40, 0, 40 + w, h), 26, fill=(30, 35, 45))
    im.paste(screen.resize((w - 40, h - 40), Image.LANCZOS), (60, 20))
    dd.rounded_rectangle((0, h, w + 80, h + 40), 14, fill=(185, 192, 202))
    return im


def art_laptop(b, t, d):
    ground(b, (205, 228, 238))
    paste(b, d["laptop"], ART_C[0] + 10, 1130, scale=0.98 + 0.02 * ease_out(t / 3))
    n = int(500 * ease_out((t - rel("quinientos", 6, 0.55) + 0.25) / 1.1))
    tag = Image.new("RGBA", (420, 150), (0, 0, 0, 0))
    dd = ImageDraw.Draw(tag)
    dd.rounded_rectangle((0, 0, 416, 146), 30, fill=GREEN)
    dd.text((208, 76), f"{max(n, 0)}{'+' if n >= 500 else ''}", font=font(FB, 100), fill=WHITE, anchor="mm")
    paste(b, tag, ART_C[0] - 180, 800, scale=ease_back(t / 0.3))
    paste(b, emoji("⏱", 140), ART_C[0] + 230, 800, rot=10 * math.sin(t * 20) * clamp(1.4 - t))


def art_diff(b, t, d):
    ground(b, (205, 228, 238))
    paste(b, d["laptop_zoom"], ART_C[0] + 10, 1130)
    pulse = 1 + 0.08 * math.sin(t * 9)
    ImageDraw.Draw(b).ellipse((130, 1050, 320, 1200), outline=RED, width=9)   # rodea la flecha roja de Cotejo
    paste(b, emoji("👉", 110), 75, 1125, scale=pulse)
    s = ease_back((t - rel("cafe", 7, 0.9)) / 0.35)
    paste(b, emoji("☕", 200), ART_C[0] + 270, 860, scale=s, rot=-10 * math.sin(t * 3))
    paste(b, emoji("😎", 150), ART_C[0] + 120, 830, scale=s)


def art_behind(b, t, d):
    ground(b, (240, 214, 186))
    for i in range(9):
        paste(b, doc(240, 300, lines=6, rot=8 * math.sin(i * 2.9)), ART_C[0] - 40 + 50 * math.sin(i * 1.3),
              1360 - i * 40)
    tag = Image.new("RGBA", (420, 150), (0, 0, 0, 0))
    dd = ImageDraw.Draw(tag)
    dd.rounded_rectangle((0, 0, 416, 146), 30, fill=WHITE, outline=RED, width=8)
    dd.text((208, 76), "37 / 500", font=font(FB, 84), fill=RED, anchor="mm")
    paste(b, tag, ART_C[0] - 120, 830, scale=ease_back((t - rel("treinta", 8, 0.15) + 0.15) / 0.3), rot=6)
    paste(b, emoji("😵", 200), ART_C[0] + 270, 1060, rot=12 * math.sin(t * 3))
    paste(b, emoji("💦", 80), ART_C[0] + 360, 960 + 40 * ((t * 1.5) % 1), alpha=clamp(1 - (t * 1.5) % 1))


def art_cta(b, t, d):
    ground(b, (205, 228, 238))
    paste(b, emoji("🖊", 260), ART_C[0] - 150, 1010, scale=ease_back(t / 0.35), rot=-25 + 6 * math.sin(t * 5))
    paste(b, emoji("👇", 130), ART_C[0] + 170, 960 + 18 * math.sin(t * 7), scale=ease_back((t - 0.3) / 0.3))
    paste(b, d["logo"], ART_C[0], 1250, scale=0.62 * ease_back((t - 0.5) / 0.35))


ARTS = {k[4]: globals()["art_" + k[4]] for k in SCENES}


def grab(t, crop, size):
    cx, cy, cw, ch = crop
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", "-vf",
                          f"crop={cw}:{ch}:{cx}:{cy},scale={size[0]}:{size[1]}", "-f", "rawvideo", "-pix_fmt",
                          "rgb24", "-"], check=True, capture_output=True).stdout
    return Image.frombytes("RGB", size, raw)


def assets():
    logo = grab(7.0, (1150, 210, 650, 700), (360, 388)).convert("RGBA")
    card_im = Image.new("RGBA", (440, 500), (0, 0, 0, 0))
    ImageDraw.Draw(card_im).rounded_rectangle((0, 0, 439, 499), 40, fill=WHITE)
    card_im.alpha_composite(logo, (40, 40))
    screen = grab(170, (620, 230, 1280, 720), (1280, 720))
    zoom = grab(170, (760, 520, 960, 540), (1280, 720))
    return {"logo": card_im, "laptop": laptop(None, screen), "laptop_zoom": laptop(None, zoom)}


def bg(scene_type, t, idx):
    chaos = idx < 5 or scene_type == "behind"
    im = Image.new("RGBA", (W, H), CHAOS + (255,) if chaos else CALM + (255,))
    d = ImageDraw.Draw(im)
    col = (250, 222, 190) if chaos else (220, 236, 244)
    for k in range(7):                                   # rayas diagonales que se mueven
        x = (k * 320 + t * (160 if chaos else 50)) % 2240 - 600
        d.polygon([(x, 0), (x + 120, 0), (x + 120 - 900, H), (x - 900, H)], fill=col)
    d.rounded_rectangle((X0, TEXT_Y - 44, X0 + 110, TEXT_Y - 34), 5, fill=RED if chaos else GREEN)
    return im, chaos


def main():
    d = assets()
    note = Image.new("RGBA", (800, 40), (0, 0, 0, 0))
    ImageDraw.Draw(note).text((0, 20), NOTE, font=font(FM, 25), fill=(110, 120, 130), anchor="lm")
    tmp_v = OUT + ".video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                            "-pix_fmt", "yuv420p", tmp_v], stdin=subprocess.PIPE)
    nfr = int(round(TOTAL * FPS))
    for n in range(nfr):
        T = n / FPS
        idx = max(i for i, s in enumerate(SCENES) if s[0] <= T + 1e-9)
        s0, s1, _, cards, kind = SCENES[idx]
        t = T - s0
        im, chaos = bg(kind, T, idx)
        ARTS[kind](im, t, d)
        draw_cards(im, cards, t, idx == 0)
        if idx >= 6:
            im.alpha_composite(note, (X0, 1450 - 40))
        if t < 0.12 and idx > 0:                          # pequeño flash de transición
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(200 * (1 - t / 0.12))))
            im.alpha_composite(fl)
        if chaos and idx in (0, 4) and t < 0.35:          # temblor de cámara en los golpes
            dx = int(14 * math.sin(t * 90) * (1 - t / 0.35))
            im = im.transform(im.size, Image.AFFINE, (1, 0, dx, 0, 1, 0), fillcolor=CHAOS + (255,))
        enc.stdin.write(im.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait()

    # ---------- sonido: música baja + efectos; la voz en off va encima después ----------
    L = int(TOTAL * SR)
    m, sr = sf.read(MUSIC, always_2d=True); assert sr == SR
    music = m.mean(1)[:L]
    music = np.pad(music, (0, L - len(music)))
    fx = np.zeros(L)
    cues = []

    def place(name, at, db, kind):
        x, sr = sf.read(os.path.join(SFX, name + ".wav"), always_2d=True); assert sr == SR
        x = x.mean(1) * 10 ** (db / 20); a = int(at * SR)
        fx[a:a + len(x)] += x[: L - a]
        cues.append({"id": f"boli:{name}:{len(cues)}", "f": round(at * FPS, 2), "kind": kind})

    starts = [s[0] for s in SCENES]
    place("hit", 0.0, -9, "hit")
    for i in (1, 2, 3, 5, 6, 7, 8, 9):
        place("swish", starts[i] - 0.11, -14, "whoosh")    # el pico del swish en el corte
    place("glitch", starts[4] + rel("error", 4, 0.2) + 0.08, -12, "hit")   # el sello de ERROR
    place("pop", starts[1] + 0.06, -12, "pop")
    place("chime", starts[5] + 0.25, -10, "bell")            # entra Altissia
    place("done", starts[6] + rel("quinientos", 6, 0.55) + 0.85, -12, "bell")   # el contador llega a 500
    place("pop", starts[9] + 0.06, -12, "pop")
    fade = int(0.6 * SR); music[-fade:] *= np.linspace(1, 0, fade)
    voice = np.zeros(L)
    if VO:
        import pyloudnorm as pyln
        from scipy.signal import butter, sosfiltfilt
        meter = pyln.Meter(SR)
        v, sr = sf.read(VO, always_2d=True); assert sr == SR, "la voz tiene que estar a 48 kHz"
        v = v.mean(1)[:L]; voice[:len(v)] = v
        voice *= 10 ** ((-16 - meter.integrated_loudness(voice)) / 20)          # voz a -16 LUFS
        # hueco en la música donde vive la voz (1-4 kHz, unos -5 dB)
        mid = sosfiltfilt(butter(2, [1000, 4000], "bandpass", fs=SR, output="sos"), music)
        music = music - 0.45 * mid
        music *= 10 ** ((-30 - meter.integrated_loudness(music)) / 20)          # música 14 LU por debajo
        # la música se aparta mientras habla: -7 dB, entra en 60 ms, vuelve en 400 ms
        hop = int(0.01 * SR)
        rms = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, "same"))
        talk = (20 * np.log10(rms + 1e-9) > 20 * np.log10(np.abs(voice).max()) - 38).astype(float)
        g = np.ones(L); duck = 10 ** (-7 / 20); cur = 1.0
        a_c, r_c = math.exp(-1 / (0.06 * SR)), math.exp(-1 / (0.4 * SR))
        tgt = np.where(talk > 0, duck, 1.0)
        for i in range(0, L, 64):                                              # envolvente por bloques
            c = a_c ** 64 if tgt[i] < cur else r_c ** 64
            cur = tgt[i] + (cur - tgt[i]) * c; g[i:i + 64] = cur
        music *= g
        fx *= np.where(talk > 0, 10 ** (-3 / 20), 1.0)                          # efectos un poco más bajos bajo la voz
    else:
        music *= 10 ** (-31 / 20) / max(1e-9, np.sqrt(np.mean(music ** 2)))   # sin voz: música baja
    mix = music + fx + voice
    if VO:
        mix *= 10 ** ((-15 - meter.integrated_loudness(mix)) / 20); k = 10 ** ((-15 - meter.integrated_loudness(music + fx + voice)) / 20)
        music *= k; fx *= k; voice *= k
    peak = np.abs(mix).max()
    if peak > 10 ** (-1.5 / 20):
        g2 = 10 ** (-1.5 / 20) / peak; mix *= g2; music *= g2; fx *= g2; voice *= g2
    base = os.path.splitext(OUT)[0]
    if VO:
        sf.write(base + "_voz.wav", np.stack([voice, voice], 1), SR)
    sf.write(base + "_music.wav", np.stack([music, music], 1), SR)
    sf.write(base + "_sfx.wav", np.stack([fx, fx], 1), SR)
    wav = OUT + ".audio.wav"
    sf.write(wav, np.stack([mix, mix], 1), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp_v, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v",
                    "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
    os.remove(tmp_v); os.remove(wav)
    json.dump({"fps": FPS, "events": cues}, open(base + ".cues.json", "w"), indent=1)
    print("ok", OUT, f"{TOTAL:.1f}s")


main()
