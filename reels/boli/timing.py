import json, sys, numpy as np, soundfile as sf
words = json.load(open(sys.argv[1])); x, sr = sf.read(sys.argv[2]); x = x if x.ndim == 1 else x.mean(1)
hop = int(0.01 * sr); rms = np.array([np.sqrt(np.mean(x[i:i+hop]**2)) for i in range(0, len(x)-hop, hop)])
db = 20*np.log10(rms+1e-9); thr = db.max() - 35
def onset(t):                      # primer frame con voz en una ventana de ±0,25 s alrededor de la marca de whisper
    a, b = max(0, int((t-0.25)*100)), int((t+0.25)*100)
    idx = np.where(db[a:b] > thr)[0]
    return round((a + idx[0]) / 100, 2) if len(idx) else t
def w(token, after=0):
    return next(s for s, e, t in words if s >= after and t.lower().strip(".,") == token)
# primera palabra de cada frase y desde qué segundo buscarla
LINES = [("nadie", 0), ("5", 2), ("para", 4), ("un", 8), ("se", 10), ("tu", 12.5), ("más", 14.5),
         ("mira", 17.5), ("tú", 20), ("etiqueta", 22)]
starts = [onset(w(tok, mn)) for tok, mn in LINES]
end_voice = max(e for s, e, t in words)
nz = np.where(db > thr)[0]; end_voice = round(nz[-1]/100, 2)
scenes = [0.0] + [round(max(0, s - 0.12), 2) for s in starts[1:]]   # la imagen entra un pelín antes que la frase
marks = {k: w(t, a) for k, t, a in [("frio", "frío", 8), ("error", "error", 10), ("adios", "adiós", 11),
                                            ("quinientos", "500", 15), ("cafe", "café", 19), ("treinta", "37", 20)]}
out = {"scenes": scenes, "end": round(end_voice + 1.2, 2), "voice_end": end_voice, "line_onsets": starts, "marks": marks}
json.dump(out, open(sys.argv[3], "w"), indent=1); print(json.dumps(out))
