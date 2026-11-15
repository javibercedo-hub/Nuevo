"""Separa la locución en sus frases y las vuelve a montar con un hueco fijo entre ellas.

uso: python3 -I respace.py words.json voz48.wav HUECO_S salida_voz.wav timing.json
Escribe la voz reespaciada y timing.json (inicio de cada escena, marcas de palabras, final)
para build.py. Cada escena entra 0,4 s antes de su frase.
"""
import json, sys, numpy as np, soundfile as sf

words = json.load(open(sys.argv[1])); x, sr = sf.read(sys.argv[2]); x = x if x.ndim == 1 else x.mean(1)
GAP, OUT_V, OUT_T = float(sys.argv[3]), sys.argv[4], sys.argv[5]
LEAD = 0.4                                     # la diapositiva entra antes que la voz
hop = int(0.01 * sr)
db = 20 * np.log10(np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x) - hop, hop)]) + 1e-9)
voiced = db > db.max() - 40


def w(tok, after):
    return next(s for s, e, t in words if s >= after and t.lower().strip(".,…") == tok)


# primera palabra de cada frase y desde qué segundo buscarla
LINES = [("nadie", 0), ("5", 2), ("para", 4), ("un", 8), ("se", 10), ("tu", 12.5), ("coteja", 14.5),
         ("revisas", 17.5), ("tú", 21), ("etiqueta", 22.5)]
firsts = [w(t, a) for t, a in LINES]
quiet = db < db.max() - 35


def cut_between(i):
    """Silencio más largo entre el final de la frase i y el principio de la i+1: (fin de i, inicio de i+1)."""
    last_end = max(e for s_, e, t_ in words if s_ < firsts[i + 1])
    lo, hi = int((min(last_end, firsts[i + 1]) - 0.15) * 100), int((firsts[i + 1] + 0.1) * 100)
    best, run_s = (0, lo, lo), None
    for k in range(lo, hi + 1):
        if k < len(quiet) and quiet[k]:
            run_s = k if run_s is None else run_s
            if k - run_s + 1 > best[0]:
                best = (k - run_s + 1, run_s, k)
        else:
            run_s = None
    if best[0] == 0:                                            # sin silencio: cortar en el punto más bajo
        k = lo + int(np.argmin(db[lo:hi])); return k / 100, k / 100
    return best[1] / 100 + 0.06, best[2] / 100 - 0.02


bounds = [cut_between(i) for i in range(len(firsts) - 1)]
v_on = int(np.argmax(voiced)); v_off = len(voiced) - int(np.argmax(voiced[::-1]))
starts_src = [max(0, v_on / 100 - 0.02)] + [b_[1] for b_ in bounds]
ends_src = [b_[0] for b_ in bounds] + [v_off / 100 + 0.12]
segs = list(zip(starts_src, ends_src))
out, new_starts, t = [], [], LEAD
for i, (a, b) in enumerate(segs):
    piece = x[int(a * sr):int(b * sr)].copy()
    f = int(0.01 * sr); piece[:f] *= np.linspace(0, 1, f); piece[-f:] *= np.linspace(1, 0, f)
    new_starts.append(t if i else 0.0)                          # la primera frase arranca en el fotograma 1
    pos = int(new_starts[-1] * sr)
    out.append((pos, piece))
    t = new_starts[-1] + (b - a) + GAP
end_voice = max(p / sr + len(q) / sr for p, q in out)
y = np.zeros(int((end_voice + 2) * sr))
for p, q in out:
    y[p:p + len(q)] += q
sf.write(OUT_V, y, sr)


def remap(ts):
    i = max(k for k, (a, b) in enumerate(segs) if a <= ts + 1e-6)
    return round(ts - segs[i][0] + new_starts[i], 2)


scenes = [0.0] + [round(s - LEAD, 2) for s in new_starts[1:]]
marks = {k: remap(w(tok, a)) for k, tok, a in [("frio", "frío", 8), ("error", "error", 10), ("adios", "adiós", 11),
                                                ("quinientos", "500", 15), ("cafe", "café", 20), ("treinta", "37", 21)]}
timing = {"gap": GAP, "scenes": scenes, "end": round(end_voice + 1.4, 2), "voice_end": round(end_voice, 2),
          "line_starts": [round(s, 2) for s in new_starts], "segments_src": [[round(a, 2), round(b, 2)] for a, b in segs],
          "marks": marks}
json.dump(timing, open(OUT_T, "w"), indent=1)
print(json.dumps(timing))
