"""Carrusel "Tu pedido diario, en 5 pasos" (Altissia). 9 diapositivas 1080x1350 PNG.

uso: python3 -I build.py VIDEO_PRESENTACION_ALTISSIA CARPETA_SALIDA
Las capturas salen del vídeo de presentación de Altissia (pantallas reales del programa).
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
W, H, M = 1080, 1350, 120                        # margen: la portada cabe en cualquier recorte de la cuadrícula
FB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
FE = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
NAVY, GREEN, YELLOW, RED = (11, 37, 69), (22, 170, 120), (255, 214, 64), (226, 60, 60)
BG, GREY, WHITE, SOFT = (244, 248, 251), (110, 122, 135), (255, 255, 255), (226, 238, 245)
HANDLE = "altissia"                              # TODO: el usuario real de Instagram
N = 9
NOTE = "*Ahorro estimado comunicado por Altissia. Resultados variables según la farmacia."
_f = {}


def font(p, s):
    return _f.setdefault((p, s), ImageFont.truetype(p, s))


def emoji(ch, size):
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((80, 80), ch, font=font(FE, 109), embedded_color=True, anchor="mm")
    im = im.crop(im.getbbox()); r = size / max(im.size)
    return im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)


def grab(t, crop):
    x, y, w, h = crop
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", SRC, "-frames:v", "1", "-vf",
                          f"crop={w}:{h}:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         check=True, capture_output=True).stdout
    return Image.frombytes("RGB", (w, h), raw)


def card(img, width, radius=28, rot=0):
    """Captura en tarjeta blanca con esquinas redondeadas y sombra."""
    r = width / img.width
    img = img.resize((width, int(img.height * r)), Image.LANCZOS).convert("RGBA")
    pad = 18
    c = Image.new("RGBA", (img.width + 2 * pad, img.height + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, c.width - 1, c.height - 1), radius, fill=WHITE)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius - 8, fill=255)
    c.paste(img, (pad, pad), mask)
    sh = Image.new("RGBA", (c.width + 80, c.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((40, 56, 40 + c.width, 56 + c.height), radius, fill=(20, 40, 70, 70))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    sh.alpha_composite(c, (40, 40))
    return sh.rotate(rot, resample=Image.BICUBIC, expand=True) if rot else sh


def put(base, im, cx, cy):
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    return out + [cur]


def text(d, xy, s, f, fill, maxw, lh=1.18):
    x, y = xy
    for ln in wrap(d, s, f, maxw):
        d.text((x, y), ln, font=f, fill=fill); y += int(f.size * lh)
    return y


def frame(i, dark=False):
    im = Image.new("RGBA", (W, H), (NAVY if dark else BG) + (255,))
    d = ImageDraw.Draw(im)
    # rombos de marca, muy suaves, en las esquinas
    col = (24, 52, 90) if dark else SOFT
    d.polygon([(W - 150, -40), (W + 40, 150), (W - 150, 340), (W - 340, 150)], fill=col)
    d.polygon([(-60, H - 230), (80, H - 90), (-60, H + 50), (-200, H - 90)], fill=col)
    put(im, ASSETS["logo_dark" if dark else "logo"], M + 10, 88)
    pill = f"{i}/{N}"
    f = font(FS, 32); tw = d.textlength(pill, font=f)
    d.rounded_rectangle((W - M - tw - 36, 66, W - M, 118), 26, fill=GREEN)
    d.text((W - M - tw / 2 - 18, 92), pill, font=f, fill=WHITE, anchor="mm")
    d.text((M - 40, H - 70), "@" + HANDLE, font=font(FS, 32), fill=(170, 185, 200) if dark else GREY, anchor="lm")
    return im, d


def step(i, num, title, body, art):
    im, d = frame(i)
    d.rounded_rectangle((M - 40, 175, M + 60, 275), 24, fill=YELLOW)
    d.text((M + 10, 226), str(num), font=font(FB, 72), fill=NAVY, anchor="mm")
    y = text(d, (M + 90, 178), title, font(FB, 60), NAVY, W - 2 * M - 90, 1.12)
    y = max(y, 290) + 14
    text(d, (M - 40, y), body, font(FM, 40), (45, 60, 80), W - 2 * M + 40, 1.3)
    art(im, d)
    return im


ASSETS = {}


def load_assets():
    logo = grab(7.0, (1150, 210, 650, 700)).convert("RGBA")

    def clean(im, dark):
        """Fondo blanco transparente; en fondo oscuro, las letras azul marino pasan a blanco."""
        im = im.copy(); px = im.load()
        for yy in range(im.height):
            for xx in range(im.width):
                r, g, b, a = px[xx, yy]
                lum = (r + g + b) / 3
                if lum > 235:
                    px[xx, yy] = (r, g, b, 0)
                elif lum > 200:                              # borde suave
                    px[xx, yy] = (r, g, b, int(255 * (235 - lum) / 35))
                elif dark and r < 60 and g < 70 and b < 100:
                    px[xx, yy] = (255, 255, 255, a)
        return im
    small = logo.resize((106, 114), Image.LANCZOS)
    ASSETS["logo"] = clean(small, False)
    ASSETS["logo_dark"] = clean(small, True)
    ASSETS["logo_big"] = clean(logo.resize((300, 323), Image.LANCZOS), False)
    ASSETS["pedido"] = grab(108, (1100, 280, 730, 590))          # pantalla real: resultado del pedido
    ASSETS["ritmo"] = grab(116, (40, 470, 1020, 580))            # lo que vendes -> lo que compras -> menos sobrestock
    ASSETS["acuerdos"] = grab(124, (90, 520, 1740, 360))         # tus acuerdos -> cada artículo -> mejor mayorista
    ASSETS["stock"] = grab(140, (90, 394, 760, 526))             # 10-20 mil € (casos comunicados)


def s1():
    im, d = frame(1)
    d.text((W / 2, 300), "Tu pedido diario,", font=font(FB, 84), fill=NAVY, anchor="mm")
    f = font(FB, 96); t = "en 5 pasos"
    tw = d.textlength(t, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 26, 352, W / 2 + tw / 2 + 26, 470), 22, fill=YELLOW)
    d.text((W / 2, 412), t, font=f, fill=NAVY, anchor="mm")
    d.text((W / 2, 530), "El método para no perder la mañana", font=font(FM, 40), fill=GREY, anchor="mm")
    d.text((W / 2, 580), "entre pedidos.", font=font(FM, 40), fill=GREY, anchor="mm")
    put(im, card(ASSETS["pedido"], 700, rot=-4), W / 2 + 30, 930)
    put(im, emoji("📦", 170), 205, 1080)
    put(im, emoji("☕", 140), 880, 1150)
    return im


def s2():
    im, d = frame(2)
    text(d, (M - 40, 190), "Si pides lo de siempre…", font(FB, 64), NAVY, W - 2 * M + 40)
    text(d, (M - 40, 290), "acabas comprando lo que no vendes y quedándote sin lo que tus clientes vienen a buscar "
                           "al mostrador.", font(FM, 42), (45, 60, 80), W - 2 * M + 40, 1.3)
    for k, (title, col, emo, x) in enumerate([("Te sobra", RED, "📦", 300), ("Te falta", RED, "🤷", 780)]):
        d.rounded_rectangle((x - 210, 640, x + 210, 1160), 36, fill=WHITE, outline=(220, 228, 236), width=3)
        d.text((x, 710), title, font=font(FB, 52), fill=col, anchor="mm")
        if k == 0:
            for j, (dx, dy) in enumerate([(-80, 0), (80, 0), (0, -120), (-80, 120), (80, 120)]):
                put(im, emoji("📦", 120), x + dx, 930 + dy)
        else:
            put(im, emoji("🤷", 200), x, 900)
            d.text((x, 1080), "«¿No os queda?»", font=font(FS, 36), fill=GREY, anchor="mm")
    return im


def s3():
    def art(im, d):
        put(im, card(ASSETS["ritmo"], 800), W / 2, 900)
        put(im, emoji("📈", 140), 860, 640)
    return step(3, 1, "Pide por venta, no por costumbre",
                "Mira cuántas unidades salen de verdad cada semana antes de pedir.", art)


def s4():
    def art(im, d):
        x0, x1, y = M, W - M, 880
        d.rounded_rectangle((x0 - 30, 640, x1 + 30, 1150), 36, fill=WHITE, outline=(220, 228, 236), width=3)
        put(im, emoji("💊", 90), x0 + 40, 710)
        d.text((x0 + 100, 712), "Ejemplo: sales 6 cajas a la semana", font=font(FS, 36), fill=NAVY, anchor="lm")
        scale = lambda v: x0 + 30 + (x1 - x0 - 60) * v / 10
        d.rounded_rectangle((scale(0), y - 26, scale(10), y + 26), 26, fill=(230, 236, 242))
        d.rounded_rectangle((scale(3), y - 26, scale(8), y + 26), 0, fill=(200, 236, 220))
        d.rounded_rectangle((scale(0), y - 26, scale(3), y + 26), 26, fill=(250, 210, 210))
        for v, lab, col in [(3, "MÍNIMO 3", RED), (8, "MÁXIMO 8", GREEN)]:
            d.line((scale(v), y - 60, scale(v), y + 60), fill=col, width=8)
            d.text((scale(v), y + 100), lab, font=font(FB, 38), fill=col, anchor="mm")
        d.text((scale(1.5), y - 90), "pide", font=font(FS, 32), fill=RED, anchor="mm")
        d.text((scale(5.5), y - 90), "ok", font=font(FS, 32), fill=GREEN, anchor="mm")
        d.text((scale(9.1), y - 90), "no pidas", font=font(FS, 32), fill=GREY, anchor="mm")
        put(im, emoji("📦", 80), scale(6), y)
        d.text((W / 2, 1090), "Por referencia, con foco en medicamentos.", font=font(FM, 34), fill=GREY, anchor="mm")
    return step(4, 2, "Pon mínimos y máximos",
                "Si baja del mínimo, entra en el pedido. Si pasa del máximo, no.", art)


def s5():
    def art(im, d):
        put(im, card(ASSETS["stock"], 560, rot=3), 360, 930)
        put(im, emoji("📦", 170), 820, 860)
        put(im, emoji("🕸", 120), 880, 770)
        d.text((W - M + 20, 1210), "Casos comunicados por Altissia. Resultados variables.", font=font(FM, 26),
               fill=GREY, anchor="rm")
    return step(5, 3, "Deja fuera lo que no rota",
                "Si lleva 2 meses sin salir, no se repone por inercia. Es dinero parado.", art)


def s6():
    def art(im, d):
        boxes = [("01", "Tus acuerdos", "Condiciones que ya tienes pactadas", False),
                 ("02", "Cada artículo", "Compara dónde te sale mejor comprar", False),
                 ("03", "Mejor mayorista", "Una decisión más rápida en el pedido diario", True)]
        y = 620
        for k, (n, t, sub, hi) in enumerate(boxes):
            x0, x1 = M - 40, W - M + 40
            fill = (0, 157, 224) if hi else WHITE
            d.rounded_rectangle((x0, y, x1, y + 150), 30, fill=fill, outline=None if hi else (150, 175, 200),
                                width=0 if hi else 4)
            fg, fg2 = (WHITE, (225, 242, 252)) if hi else (NAVY, GREY)
            d.text((x0 + 40, y + 48), n, font=font(FB, 30), fill=(225, 242, 252) if hi else (0, 157, 224), anchor="lm")
            d.text((x0 + 110, y + 50), t, font=font(FB, 46), fill=fg, anchor="lm")
            d.text((x0 + 110, y + 105), sub, font=font(FM, 32), fill=fg2, anchor="lm")
            if k < 2:
                d.polygon([(W / 2 - 22, y + 162), (W / 2 + 22, y + 162), (W / 2, y + 190)], fill=(150, 175, 200))
            y += 200
        put(im, emoji("🤝", 120), W - M - 20, 520)
    return step(6, 4, "Aplica tus acuerdos",
                "Las condiciones que ya tienes pactadas deciden a quién le compras.", art)


def s7():
    def art(im, d):
        put(im, card(ASSETS["pedido"], 720, rot=2), W / 2 - 20, 930)
        put(im, emoji("🏆", 140), 870, 700)
    return step(7, 5, "Compara mayorista por artículo",
                "No por pedido entero: cada referencia, donde mejor te sale.", art)


def s8():
    im, d = frame(8, dark=True)
    d.text((M - 40, 230), "El pedido diario,", font=font(FB, 66), fill=WHITE, anchor="lm")
    d.text((M - 40, 310), "en 5 pasos", font=font(FB, 66), fill=YELLOW, anchor="lm")
    rows = [("📈", "Pide por venta"), ("📏", "Mínimos y máximos"), ("🕸", "Fuera lo que no rota"),
            ("🤝", "Aplica tus acuerdos"), ("🏆", "Mejor mayorista por artículo")]
    y = 430
    for k, (e, t) in enumerate(rows):
        d.rounded_rectangle((M - 40, y, W - M + 40, y + 120), 30, fill=(24, 52, 90))
        d.text((M + 20, y + 60), str(k + 1), font=font(FB, 54), fill=YELLOW, anchor="mm")
        put(im, emoji(e, 70), M + 110, y + 60)
        d.text((M + 170, y + 60), t, font=font(FB, 46), fill=WHITE, anchor="lm")
        y += 145
    d.text((W / 2, y + 40), "Haz captura y pásaselo a quien hace los pedidos.", font=font(FM, 32),
           fill=(170, 185, 200), anchor="mm")
    return im


def s9():
    im, d = frame(9)
    put(im, ASSETS["logo_big"], W / 2, 400)
    d.text((W / 2, 640), "Altissia hace estos 5 pasos", font=font(FB, 56), fill=NAVY, anchor="mm")
    d.text((W / 2, 715), "en un clic.", font=font(FB, 56), fill=NAVY, anchor="mm")
    f = font(FB, 64); t = "+100 h al año de vuelta*"
    tw = d.textlength(t, font=f)
    d.rounded_rectangle((W / 2 - tw / 2 - 30, 790, W / 2 + tw / 2 + 30, 900), 26, fill=GREEN)
    d.text((W / 2, 846), t, font=f, fill=WHITE, anchor="mm")
    put(im, emoji("🔖", 110), W / 2, 1010)
    d.text((W / 2, 1110), "GUÁRDALO PARA EL PRÓXIMO PEDIDO", font=font(FB, 44), fill=NAVY, anchor="mm")
    d.text((W / 2, 1200), NOTE, font=font(FM, 24), fill=GREY, anchor="mm")
    return im


load_assets()
for k, fn in enumerate([s1, s2, s3, s4, s5, s6, s7, s8, s9], 1):
    fn().convert("RGB").save(os.path.join(OUT, f"{k:02d}.png"), optimize=True)
print("ok", OUT)
