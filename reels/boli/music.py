"""Música original del reel "el del boli", compuesta en código (sin muestras ni licencias).

Parte A (0 - 7 compases): re menor, marimba nerviosa en corcheas, bajo pizzicato, palmas.
Parón cómico de medio tiempo antes del cambio de escena.
Parte B (desde el compás 7): fa mayor, más luminosa, glockenspiel encima, acorde final con cola.
uso: python3 -I music.py SALIDA.wav DURACION_SEGUNDOS
"""
import sys
import numpy as np
import soundfile as sf

SR = 48000
BPM = 125.4                       # 7 compases = 13,4 s: el cambio cae justo en la escena de Altissia
BEAT = 60 / BPM
OUT, DUR = sys.argv[1], float(sys.argv[2])
rng = np.random.default_rng(7)
L = int((DUR + 2) * SR)
mus = np.zeros(L)
drums = np.zeros(L)


def hz(note):
    names = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7,
             "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
    n, o = note[:-1], int(note[-1])
    return 440 * 2 ** ((names[n] + 12 * (o + 1) - 69) / 12)


def add(buf, x, t):
    a = int(t * SR)
    if a >= len(buf):
        return
    buf[a:a + len(x)] += x[: len(buf) - a]


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(t / attack, 1) * np.exp(-t / decay)


def marimba(f, dur=0.45, amp=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) * env(n, 0.002, 0.16)
         + 0.25 * np.sin(2 * np.pi * 3.93 * f * t) * env(n, 0.001, 0.035)
         + 0.07 * np.sin(2 * np.pi * 9.8 * f * t) * env(n, 0.001, 0.01))
    return amp * x


def glock(f, dur=0.8, amp=0.18):
    n = int(dur * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) * env(n, 0.001, 0.35)
         + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * env(n, 0.001, 0.12)
         + 0.2 * np.sin(2 * np.pi * 5.4 * f * t) * env(n, 0.001, 0.05))
    return amp * x


def pizz(f, dur=0.32, amp=0.55):
    # Karplus-Strong corto: cuerda pulsada
    n = int(dur * SR); p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p); out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return amp * out * env(n, 0.003, 0.12)


def kick(amp=0.7):
    n = int(0.22 * SR); t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t / 0.03)
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, 0.001, 0.08)


def clap(amp=0.28):
    n = int(0.18 * SR); x = np.zeros(n)
    for d in (0.0, 0.011, 0.022):
        a = int(d * SR); m = n - a
        x[a:] += rng.normal(0, 1, m) * env(m, 0.0005, 0.012 if d < 0.02 else 0.06)
    x = np.convolve(x, np.ones(6) / 6, "same") - np.convolve(x, np.ones(40) / 40, "same")
    return amp * x


def shaker(amp=0.06):
    n = int(0.05 * SR)
    x = rng.normal(0, 1, n); x = x - np.convolve(x, np.ones(8) / 8, "same")
    return amp * x * env(n, 0.004, 0.012)


# progresiones: un compás por acorde (raíz del bajo, arpegio de la marimba)
A_BARS = [("D2", ["D4", "F4", "A4", "F4", "D5", "A4", "F4", "A4"]),
          ("A1", ["C#4", "E4", "A4", "E4", "C#5", "A4", "E4", "A4"]),
          ("Bb1", ["D4", "F4", "Bb4", "F4", "D5", "Bb4", "F4", "Bb4"]),
          ("A1", ["C#4", "E4", "G4", "E4", "A4", "G4", "E4", "C#4"])]
B_BARS = [("F2", ["F4", "A4", "C5", "A4", "F5", "C5", "A4", "C5"]),
          ("C2", ["E4", "G4", "C5", "G4", "E5", "C5", "G4", "C5"]),
          ("D2", ["D4", "F4", "A4", "F4", "D5", "A4", "F4", "A4"]),
          ("Bb1", ["D4", "F4", "Bb4", "F4", "D5", "Bb4", "C5", "E5"])]
GLOCK_B = [["C6", None, "A5", None], ["G5", None, "E5", None], ["F5", None, "A5", None], ["Bb5", "A5", "G5", None]]

bar_len = 4 * BEAT
n_bars = int(np.ceil(DUR / bar_len))
SWITCH = 7                                   # compás donde entra Altissia
for b in range(n_bars):
    t0 = b * bar_len
    part_b = b >= SWITCH
    root, arp = (B_BARS if part_b else A_BARS)[(b - SWITCH if part_b else b) % 4]
    last_a = b == SWITCH - 1
    for i, note in enumerate(arp):
        t = t0 + i * BEAT / 2
        if last_a and i >= 6:                # parón cómico: silencio el último tiempo antes del cambio
            continue
        add(mus, marimba(hz(note), amp=0.42 if i % 2 == 0 else 0.3), t + rng.normal(0, 0.003))
    for i, beat in enumerate((0, 2)):          # bajo: raíz en el 1, quinta (A) u octava (B) en el 3
        add(mus, pizz(hz(root) * (1 if i == 0 else 2 if part_b else 1.5)), t0 + beat * BEAT)
    for beat in range(4):
        t = t0 + beat * BEAT
        if last_a and beat == 3:
            continue
        if beat in (0, 2):
            add(drums, kick(), t)
        else:
            add(drums, clap(), t)
        add(drums, shaker(), t + BEAT / 2)
    if part_b:
        for i, note in enumerate(GLOCK_B[(b - SWITCH) % 4]):
            if note:
                add(mus, glock(hz(note)), t0 + i * BEAT)

# final: acorde de fa mayor con cola, justo al final
end_t = DUR - 1.6
cut = int(end_t * SR)
mus[cut:] = 0; drums[cut:] = 0
for note in ("F3", "A3", "C4", "F4", "A4", "C5"):
    add(mus, marimba(hz(note), dur=1.6, amp=0.32), end_t)
add(mus, glock(hz("F5"), dur=1.6, amp=0.22), end_t)
add(drums, kick(0.5), end_t)

mix = mus + 0.8 * drums
mix = mix[: int(DUR * SR)]
mix = np.tanh(mix * 1.2) / 1.2                # un pelín de saturación suave
mix /= np.abs(mix).max()
sf.write(OUT, np.stack([mix, mix], 1) * 0.9, SR)
print("ok", OUT, f"{DUR:.1f}s, {BPM} BPM, cambio en {SWITCH * bar_len:.2f}s")
