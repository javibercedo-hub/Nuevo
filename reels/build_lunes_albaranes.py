import subprocess, os, sys
from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W = os.path.dirname(os.path.abspath(__file__))
FB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FR = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
NAVY, GREEN, GREY = (11, 37, 69), (22, 170, 120), (120, 130, 140)
X0, MAXW = 80, 770            # leave the right 230 px clear
TEXT_TOP = 280                # below the 230 px top bar
PANEL_Y, PW, PH = 800, 1080, 608
NOTE = "Casos comunicados por Altissia. Resultados variables."
FPS = 30

# duration, text lines [(text, colour, size)], source second, 16:9 crop (x,y,w,h), zoom at end
SEGS = [
    (2.8, [("Hasta 4.000 €", GREEN, 120), ("en errores en tus albaranes", NAVY, 72)], 160, (1120, 380, 800, 450), 1.10),
    (1.8, [("Un precio mal facturado.", NAVY, 86)], 160, (900, 420, 1020, 574), 1.06),
    (1.8, [("Una entrada que no cuadra.", NAVY, 86)], 160, (60, 500, 900, 506), 1.08),
    (2.2, [("Cientos de albaranes al mes.", NAVY, 86)], 160, (30, 170, 1240, 698), 1.08),
    (2.4, [("Nadie tiene tiempo de revisarlos línea a línea.", NAVY, 80)], 170, (620, 230, 1280, 720), 1.06),
    (2.6, [("Altissia coteja", NAVY, 86), ("500+ en ≈5 segundos", GREEN, 96)], 160, (60, 420, 1100, 619), 1.08),
    (2.6, [("Tú solo revisas las diferencias.", NAVY, 86)], 170, (720, 420, 1040, 585), 1.12),
    (2.0, [("El resto, cotejado.", NAVY, 92)], 170, (0, 0, 1920, 1080), 1.05),
    (3.2, [("¿Cuántos albaranes revisáis al mes?", NAVY, 86), ("Te leo en comentarios", GREEN, 60)], 218, (0, 0, 1920, 1080), 1.05),
]


def wrap(draw, text, font):
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= MAXW or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines


def card(i, parts):
    im = Image.new("RGB", (1080, 1920), "white")
    d = ImageDraw.Draw(im)
    y = TEXT_TOP
    for text, col, size in parts:
        f = ImageFont.truetype(FB, size)
        for ln in wrap(d, text, f):
            d.text((X0, y), ln, font=f, fill=col)
            y += int(size * 1.15)
        y += 18
    assert y < PANEL_Y - 20, f"card {i} text overflows into the footage ({y})"
    d.rectangle((X0, PANEL_Y - 40, X0 + 120, PANEL_Y - 32), fill=GREEN)
    fn = ImageFont.truetype(FR, 26)
    d.text((X0, PANEL_Y + PH + 30), NOTE, font=fn, fill=GREY)
    p = f"{W}/card{i}.png"; im.save(p); return p


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


parts = []
for i, (dur, txt, t, (cx, cy, cw, ch), z) in enumerate(SEGS):
    c = card(i, txt)
    still = f"{W}/still{i}.png"
    run(["ffmpeg", "-y", "-ss", str(t), "-i", SRC, "-frames:v", "1",
         "-vf", f"crop={cw}:{ch}:{cx}:{cy},scale=2160:1216", still])
    n = round(dur * FPS)
    zp = (f"zoompan=z='1+({z}-1)*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":d={n}:s={PW}x{PH}:fps={FPS}")
    seg = f"{W}/seg{i}.mp4"
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", c, "-i", still,
         "-filter_complex", f"[1:v]{zp}[f];[0:v][f]overlay=0:{PANEL_Y}:shortest=1,format=yuv420p",
         "-frames:v", str(n), "-r", str(FPS), "-c:v", "libx264", "-crf", "18", "-preset", "medium", seg])
    parts.append(seg)

lst = f"{W}/list.txt"
open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst,
     "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
     "-map", "0:v", "-map", "1:a", "-shortest", "-c:v", "libx264", "-crf", "18",
     "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac",
     "-movflags", "+faststart", OUT])
print("ok", OUT)
