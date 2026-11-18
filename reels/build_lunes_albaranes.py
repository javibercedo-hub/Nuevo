"""Reel del lunes: cotejo de albaranes. 1080x1920, texto animado, sin voz, efectos de earshot.

uso: python3 -I build_lunes_albaranes.py VIDEO_ORIGEN SALIDA.mp4 CARPETA_SFX
CARPETA_SFX tiene los WAV renderizados con `earshot sfx render` (ver render_sfx.sh).
"""
import os, subprocess, sys, math
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT, SFX = sys.argv[1], sys.argv[2], sys.argv[3]
FB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FR = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
BG, NAVY, GREEN, GREY, WHITE = (245, 248, 251), (11, 37, 69), (22, 170, 120), (120, 130, 140), (255, 255, 255)
FPS, SR = 30, 48000
X0, MAXW, TEXT_TOP = 80, 770, 290          # zona segura: y 230-1440, 230 px libres a la derecha
CARD = (60, 830, 960, 540)                  # x, y, w, h del vídeo
NOTE = "Casos comunicados por Altissia. Resultados variables."
N, H = "n", "h"                              # texto normal / resaltado en caja verde

# duración, líneas [(texto, estilo, tamaño)], segundo del vídeo, recorte 16:9 (x,y,w,h), zoom final, sonido del resaltado
SEGS = [
    (2.8, [[("Hasta", N, 96)], [("4.000 €", H, 140)], [("en errores en", N, 74)], [("tus albaranes.", N, 74)]],
     160, (1120, 380, 800, 450), 1.10, None),
    (1.9, [[("Un precio", N, 92)], [("mal facturado.", H, 92)]], 160, (900, 420, 1020, 574), 1.07, "pop0"),
    (1.9, [[("Una entrada", N, 92)], [("que no cuadra.", H, 92)]], 160, (60, 500, 900, 506), 1.07, "pop1"),
    (2.2, [[("Cientos de", N, 92)], [("albaranes", N, 92)], [("al mes.", H, 92)]], 160, (30, 170, 1240, 698), 1.07, "pop2"),
    (2.4, [[("Nadie tiene tiempo", N, 80)], [("de revisarlos", N, 80)], [("línea a línea.", H, 80)]],
     170, (620, 230, 1280, 720), 1.06, "pop3"),
    (2.6, [[("Altissia coteja", N, 84)], [("500+", H, 124)], [("en ≈5 segundos.", N, 84)]], 160, (60, 420, 1100, 619), 1.08, "pop4"),
    (2.6, [[("Tú solo revisas", N, 88)], [("las diferencias.", H, 88)]], 170, (720, 420, 1040, 585), 1.12, "pop5"),
    (2.0, [[("El resto,", N, 100)], [("cotejado.", H, 100)]], 170, (0, 0, 1920, 1080), 1.05, "bell"),
    (3.4, [[("¿Cuántos albaranes", N, 80)], [("revisáis al mes?", N, 80)], [("Te leo en comentarios", H, 54)]],
     218, (0, 0, 1920, 1080), 1.05, "cta"),
]
STAGGER, IN_T, OUT_T = 0.07, 0.24, 0.10
LEVELS = {"hit": -3, "swish": -7, "bell": -6, "cta": -5}   # dB; los pops van a -7
fonts = {}


def font(sz):
    return fonts.setdefault(sz, ImageFont.truetype(FB, sz))


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def layout(lines):
    """Coloca cada unidad animable (palabra suelta o caja resaltada) con su orden de entrada."""
    d = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    units, y, k = [], TEXT_TOP, 0
    for line in lines:
        x, lh = X0, 0
        for text, style, size in line:
            f = font(size)
            # encoge si no cabe en el ancho seguro
            pad = int(size * 0.18) if style == H else 0
            while d.textlength(text, font=f) + 2 * pad > MAXW:
                size -= 2; f = font(size); pad = int(size * 0.18) if style == H else 0
            pieces = [text] if style == H else text.split(" ")
            for p in pieces:
                w = d.textlength(p, font=f)
                units.append(dict(t=p, s=style, f=f, x=x, y=y + (int(size * 0.12) if style == H else 0), w=w, pad=pad, size=size, k=k))
                x += w + 2 * pad + d.textlength(" ", font=f); k += 1
            lh = max(lh, int(size * (1.42 if style == H else 1.12)))
        y += lh + 10
    assert y < CARD[1] - 20, f"el texto invade el vídeo ({y})"
    return units


def stills():
    out = []
    for i, (_, _, t, (cx, cy, cw, ch), _, _) in enumerate(SEGS):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1",
                              "-vf", f"crop={cw}:{ch}:{cx}:{cy},scale=1920:1080", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
        out.append(Image.frombytes("RGB", (1920, 1080), raw))
    return out


def footage(img, z):
    w, h = 1920 / z, 1080 / z
    box = ((1920 - w) / 2, (1080 - h) / 2, (1920 + w) / 2, (1080 + h) / 2)
    return img.resize((CARD[2], CARD[3]), Image.LANCZOS, box=box)


def base_frame():
    im = Image.new("RGB", (1080, 1920), BG)
    sh = Image.new("L", (1080, 1920), 0)
    x, y, w, h = CARD
    ImageDraw.Draw(sh).rounded_rectangle((x + 4, y + 18, x + w - 4, y + h + 18), 30, fill=70)
    sh = sh.filter(ImageFilter.GaussianBlur(22))
    im.paste(Image.new("RGB", im.size, (20, 40, 70)), mask=sh)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((X0, TEXT_TOP - 44, X0 + 110, TEXT_TOP - 34), 5, fill=GREEN)
    d.text((X0, y + h + 34), NOTE, font=ImageFont.truetype(FR, 25), fill=GREY)
    return im


def draw_text(im, units, t, t_end, first):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    out_a = 1.0 if t_end is None else ease((t_end - t) / OUT_T)
    for u in units:
        if first:                                  # el gancho está entero en el fotograma 1
            a, dy, sc = 1.0, 0, 1 + 0.18 * (1 - ease(t / 0.22)) if u["s"] == H else 1.0
        else:
            p = ease((t - u["k"] * STAGGER) / IN_T)
            a, dy, sc = p, int(36 * (1 - p)), 1.0
        a *= out_a
        if a <= 0:
            continue
        al = int(255 * a)
        if u["s"] == H:
            pad, f = u["pad"], u["f"]
            bx0, by0 = u["x"], u["y"] + dy
            bw, bh = u["w"] + 2 * pad, int(u["size"] * 1.22)
            grow = 1.0 if first else ease((t - u["k"] * STAGGER) / (IN_T * 1.3))
            cx, cy = bx0 + bw / 2, by0 + bh / 2
            bw2, bh2 = bw * sc, bh * sc
            d.rounded_rectangle((bx0 + (bw - bw2) / 2, cy - bh2 / 2, bx0 + (bw - bw2) / 2 + bw2 * grow, cy + bh2 / 2),
                                int(u["size"] * 0.16), fill=GREEN + (al,))
            if sc != 1.0:
                f = font(max(8, int(u["size"] * sc)))
            tw = d.textlength(u["t"], font=f)
            d.text((cx - tw / 2, cy), u["t"], font=f, fill=WHITE + (al,), anchor="lm")
        else:
            d.text((u["x"], u["y"] + dy), u["t"], font=u["f"], fill=NAVY + (al,))
    im.paste(layer, (0, 0), layer)


def main():
    caps, base = stills(), base_frame()
    mask = Image.new("L", CARD[2:], 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, CARD[2] - 1, CARD[3] - 1), 30, fill=255)
    starts = np.cumsum([0] + [s[0] for s in SEGS])
    total = starts[-1]
    nfr = int(round(total * FPS))
    seg_units = [layout(s[1]) for s in SEGS]
    tmp_v = OUT + ".video.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17", "-preset", "medium",
                            "-pix_fmt", "yuv420p", tmp_v], stdin=subprocess.PIPE)
    prev_card = None
    for n in range(nfr):
        T = n / FPS
        i = int(np.searchsorted(starts, T, side="right") - 1)
        dur, _, _, _, z, _ = SEGS[i]
        t = T - starts[i]
        card = footage(caps[i], 1 + (z - 1) * t / dur)
        if i > 0 and t < 0.2:                      # fundido corto entre planos
            old = footage(caps[i - 1], SEGS[i - 1][4])
            card = Image.blend(old, card, ease(t / 0.2))
        im = base.copy()
        im.paste(card, CARD[:2], mask)
        last = i == len(SEGS) - 1
        draw_text(im, seg_units[i], t, None if last else dur, i == 0)
        enc.stdin.write(im.tobytes())
    enc.stdin.close(); enc.wait()

    # sonido: golpe en el gancho, un pop que sube de tono en cada resaltado, swish al pasar a la pantalla de Cotejo
    mix = np.zeros(int(total * SR) + SR, dtype=np.float64)

    def place(name, at, db):
        x, sr = sf.read(os.path.join(SFX, name + ".wav"), always_2d=True)
        assert sr == SR, (name, sr)
        x = x.mean(axis=1) * 10 ** (db / 20)
        a = max(0, int(at * SR)); mix[a:a + len(x)] += x[: len(mix) - a]

    cues = [("hit", 0.0)]
    place("hit", 0.0, LEVELS["hit"])
    for i, seg in enumerate(SEGS):
        snd = seg[5]
        if not snd:
            continue
        k = next(u["k"] for u in seg_units[i] if u["s"] == H)
        at = starts[i] + k * STAGGER - 0.01         # los toques se adelantan un pelín a la imagen
        place(snd, at, LEVELS.get(snd, -7)); cues.append((snd, round(at + 0.01, 3)))
    sw = starts[4] - 0.111                          # el pico del swish cae en el cambio de plano
    place("swish", sw, LEVELS["swish"]); cues.append(("swish", round(starts[4], 3)))
    mix = mix[: int(total * SR)]
    mix *= 10 ** (-3 / 20) / max(1e-9, np.abs(mix).max())   # pico a -3 dBFS
    wav = OUT + ".audio.wav"
    sf.write(wav, np.stack([mix, mix], 1), SR)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp_v, "-i", wav, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                   check=True)
    os.remove(tmp_v)
    import json
    kinds = {"hit": "hit", "swish": "whoosh", "bell": "bell", "cta": "bell"}
    json.dump({"fps": FPS, "events": [{"id": f"reel:{c}:{j}", "f": round(t * FPS, 2), "kind": kinds.get(c, "pop")}
                                      for j, (c, t) in enumerate(cues)]},
              open(OUT + ".cues.json", "w"), indent=1)
    print("ok", OUT, f"{total:.1f}s", len(cues), "efectos")


main()
