#!/usr/bin/env python3
"""
hookscore.py - score the first line of a Reel on the five things strong hooks
have in common, and rank a batch of them against each other.

What this is:  five local heuristics, computed on your machine from the text
alone. They measure properties that hooks which hold attention tend to share -
a length you can say in under three seconds, a concrete marker, something at stake,
the payload at the front rather than the back, and a viewer to aim it at.

What this is NOT:  a view predictor. It was tested against 74 real short-form
hooks, transcribed from the first three seconds of the top eight and bottom
eight performers on five channels. Separating a real hook from a deliberately
bad one it does well: AUC 0.83, and 9 of 10 written-to-be-bad hooks scored
below the real median. Separating a good creator's hits from that same
creator's misses it barely does at all: AUC 0.56, where 0.50 is a coin flip.

So use it for what it measured well. It catches greetings, preambles, hooks
with nothing concrete in them and hooks that take five seconds to say. It will
not tell you which of two decent hooks will travel, and nothing that reads text
can, because that is decided by your face, your edit, your audio and who
Instagram shows it to. Trust the retention graph over this script.

Each check returns 0 to 100. Higher is better.

Usage
  python3 hookscore.py hooks.txt              # one hook per line, ranked
  python3 hookscore.py --hook "I lost $18,000 on one missing contract."
  pbpaste | python3 hookscore.py -
  python3 hookscore.py hooks.txt --json
"""

import argparse
import json
import re
import statistics
import sys
import unicodedata

# Bilingual: English plus Spanish as spoken in Spain (tú / vosotros, euros).
# Every word list below is matched after lower-casing and stripping accents,
# so "perdí" and "perdi", "vídeo" and "video" count the same.
WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9$€%'’-]+")
NUMBER_RE = re.compile(
    r"[$€]\s?\d(?:[\d.,]*\d)?"                       # money, $ or € in front
    r"|\b\d(?:[\d.,]*\d)?\s?"                        # a figure, with or
    r"(?:%|€|k\b|x\b|hrs?\b|hours?\b|mins?\b|minutes?\b"  # without a unit
    r"|days?\b|weeks?\b|months?\b|years?\b"
    r"|h\b|horas?\b|minutos?\b|seg(?:undos?)?\b|d[ií]as?\b|semanas?\b"
    r"|mes(?:es)?\b|a[ñn]os?\b|euros?\b|pavos\b)?",
    re.IGNORECASE)
PROPER_RE = re.compile(r"(?<!^)\b[A-ZÁÉÍÓÚÑ][a-záéíóúüñ]{2,}\b")
PRICE_RE = re.compile(r"[$€]\s?\d|\d\s?€|\d\s?(?:euros?|pavos)\b", re.IGNORECASE)


def fold(text):
    """Lower-case and drop accents: 'Perdí' -> 'perdi'."""
    t = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def norm(token):
    return fold(token).strip("'’")
HASHTAG_RE = re.compile(r"(?:^|\s)#\w+")
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")

# Spoken hooks say their numbers out loud. "Zero dollars" and "twenty grand"
# are as concrete as "$0" and "$20,000", and counting only digits missed them.
# "one" and "first" are deliberately absent: they are filler far more often
# than they are a quantity.
SPOKEN_NUMBERS = {
    "zero", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "fifteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred", "thousand", "million",
    "billion", "dozen", "half", "twice", "triple",
    # es-ES. "uno", "una" y "primero" fuera por lo mismo: casi siempre relleno.
    "cero", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
    "diez", "once", "doce", "trece", "catorce", "quince", "dieciseis",
    "diecisiete", "dieciocho", "diecinueve", "veinte", "veinticinco", "treinta",
    "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa", "cien",
    "cientos", "doscientos", "trescientos", "quinientos", "mil", "millon",
    "millones", "docena", "mitad", "doble", "triple",
}
MONEY_WORDS = {
    "dollars", "dollar", "bucks", "grand", "percent", "cents",
    "millionaire", "billionaire", "revenue", "profit", "salary", "rent",
    # es-ES
    "euros", "euro", "pavos", "pasta", "pelas", "ciento", "facturacion",
    "facture", "facturo", "beneficio", "beneficios", "sueldo", "salario",
    "nomina", "alquiler", "hipoteca", "ingresos", "millonario", "millonaria",
}

# Words that put something on the line. A hook with none of these is a
# statement; a hook with one is a reason to keep watching.
STAKES = {
    "stop", "never", "wrong", "mistake", "mistakes", "lost", "lose", "losing",
    "cost", "costs", "broke", "broken", "failed", "failure", "fail", "nobody",
    "no", "not", "don't", "dont", "doesn't", "didn't", "can't", "won't",
    "quit", "quitting", "fired", "deleted", "delete", "killed", "kills", "kill",
    "replaced", "replaces", "cut", "beat", "free", "paid", "charged", "hired",
    "saved", "first",
    "banned", "illegal", "worst", "hate", "hated", "wasted", "waste", "scam",
    "lie", "lied", "lying", "truth", "secret", "hidden", "stole", "stolen",
    "before", "until", "instead", "but", "except", "unless", "problem",
    "risk", "danger", "warning", "regret", "wish", "should", "shouldn't",
    "still", "already", "only", "without", "versus", "vs", "actually",
    # es-ES ("para" y "ya" fuera: son preposición/relleno casi siempre)
    "deja", "dejar", "deje", "dejad", "nunca", "jamas", "mal", "error",
    "errores", "equivocado", "equivocada", "perdi", "perder", "perdido",
    "perdiendo", "pierdes", "pierde", "cuesta", "cuestan", "costo", "coste",
    "arruinado", "arruinada", "ruina", "roto", "falle", "fallo", "fracase",
    "fracaso", "nadie", "nada", "ni", "dimiti", "despedido", "despedida",
    "despidieron", "borre", "borra", "borrar", "elimine", "mato", "mata",
    "matar", "sustituyo", "sustituye", "reemplazo", "recorte", "gane",
    "gratis", "pague", "pagar", "cobre", "cobran", "contrate", "ahorre",
    "ahorrar", "primero", "primera", "prohibido", "ilegal", "peor", "odio",
    "odiaba", "tire", "desperdicie", "estafa", "timo", "mentira", "menti",
    "mienten", "verdad", "secreto", "oculto", "robe", "robado", "antes",
    "hasta", "pero", "excepto", "salvo", "problema", "riesgo", "peligro",
    "cuidado", "ojala", "arrepiento", "deberias", "debes", "todavia", "aun",
    "solo", "sin", "contra", "realmente", "literalmente",
}

# Openers that spend the first second saying nothing. Matched as whole
# words from the start of the hook ("so" does not catch "something").
WEAK_OPENERS = [
    "so", "ok", "okay", "hey", "hi", "hello", "guys", "yo", "alright",
    "welcome", "today", "basically", "honestly", "look", "listen", "um",
    "just", "let", "lets", "let's", "i wanted", "i want", "one of",
    "have you", "did you", "do you", "are you", "in this", "in today",
    "the thing", "a lot", "there is", "there are", "this is", "it is",
    "as a", "when it", "if you've", "you know",
    # es-ES
    "bueno", "vale", "hola", "buenas", "chicos", "chicas", "chavales", "gente",
    "hoy", "basicamente", "sinceramente", "honestamente", "mira", "mirad",
    "oye", "escucha", "eh", "em", "pues", "venga", "a ver", "quiero",
    "queria", "os voy", "te voy", "voy a", "vamos a", "has visto",
    "habeis visto", "sabias", "sabes", "sabeis", "alguna vez", "estas",
    "esto es", "hay", "en este", "en el", "lo que", "la cosa", "si alguna",
    "si alguna vez", "cuando se", "tengo que", "bienvenidos", "que tal",
]

# Imperatives that earn the front position.
IMPERATIVES = {
    "stop", "steal", "copy", "delete", "try", "watch", "read", "save",
    "use", "build", "make", "write", "send", "take", "start", "quit",
    "never", "always", "don't", "dont", "do", "put", "run", "check",
    # es-ES, tú y vosotros
    "deja", "dejad", "roba", "robad", "copia", "copiad", "borra", "borrad",
    "prueba", "probad", "lee", "leed", "guarda", "guardad", "usa", "usad",
    "haz", "haced", "construye", "escribe", "escribid", "manda", "mandad",
    "envia", "enviad", "coge", "coged", "pilla", "empieza", "empezad",
    "nunca", "siempre", "no", "pon", "poned", "revisa", "apunta", "apuntad",
    "olvida", "olvidad", "evita", "evitad", "cambia", "cambiad",
}

DEALBREAKERS = [
    (re.compile(r"(?i)^\s*(?:stop scrolling|don'?t scroll"
                r"|(?:deja|dejad|para|parad) de (?:hacer )?scroll|no (?:hagas|hagáis|hagais) scroll"
                r"|no (?:deslices|sigas bajando))"),
     "Opens with \"stop scrolling\". Asking for attention proves you have not earned it."),
    (re.compile(r"(?i)\b(?:in (?:this|today'?s) (?:video|reel)|i'?m going to show you|i'?ll show you how"
                r"|en (?:este|el) (?:v[ií]deo|reel)|en el (?:v[ií]deo|reel) de hoy"
                r"|(?:os|te) voy a (?:ense[ñn]ar|contar|explicar|mostrar|decir)"
                r"|(?:os|te) ense[ñn]o c[oó]mo)\b"),
     "Video preamble. Delete it and open on the payoff."),
    (re.compile(r"(?i)^\s*(?:hey |hi |what'?s up |welcome "
                r"|hola\b|holi\b|buenas\b|qu[eé] tal\b|bienvenid[oa]s?\b|qu[eé] pasa (?:gente|chavales|familia)\b)"),
     "Greeting. Nobody came to the feed to be greeted."),
    (HASHTAG_RE,
     "Hashtag in the hook. Hashtags belong at the bottom of the caption, if anywhere."),
    (EMOJI_RE,
     "Emoji in the hook. On-screen text at hook size has room for words or for an emoji, not both."),
]


VIEWER_RE = re.compile(
    r"\b(you|your|you're|youre|yourself"
    r"|tu|tus|te|ti|contigo|vosotros|vosotras|os|vuestro|vuestra|vuestros|vuestras"
    r"|usted|ustedes)\b")
FIRST_PERSON_RE = re.compile(
    r"\b(i|my|me|we|our"
    r"|yo|mi|mis|conmigo|nosotros|nosotras|nuestro|nuestra|nuestros|nuestras|nos)\b")
# Words ending in -é / -í that are not a first-person past tense.
NOT_PRETERITE = {"aquí", "allí", "ahí", "así", "café", "bebé", "josé", "rubí",
                 "esquí", "maniquí", "jabalí", "colibrí"}


def clamp(n):
    return max(0.0, min(100.0, n))


def words(text):
    # "$18,000" / "18.000 €" is one word when it is spoken, so it is one word
    # here too. Spain writes thousands with a dot, so both separators go.
    return WORD_RE.findall(re.sub(r"(?<=\d)[.,](?=\d{3}\b)", "", text))


def check_length(text):
    """A hook has to land before the thumb moves. Roughly two seconds."""
    w = words(text)
    n = len(w)
    secs = n / 2.75                      # ~165 words per minute, spoken
    chars = len(text.strip())
    if 5 <= n <= 12:
        score = 100.0
    elif n < 5:
        score = clamp(100 - (5 - n) * 20)
    else:
        score = clamp(100 - (n - 12) * 11)
    if chars > 60:                       # two lines of big on-screen text
        score -= 12
    return clamp(score), f"{n} words, {chars} chars, ~{secs:.1f}s spoken (want 5-12 words)"


def check_specificity(text):
    """One concrete thing beats three abstract ones."""
    nums = [n.strip() for n in NUMBER_RE.findall(text) if n.strip()]
    propers = set(PROPER_RE.findall(text))
    low = [norm(w) for w in words(text)]
    spoken =[w for w in low if w in SPOKEN_NUMBERS or w in MONEY_WORDS]
    hits = len(nums) + len(propers) + len(spoken)
    score = 15.0 if hits == 0 else clamp(45 + hits * 30)
    found = ", ".join(nums[:2] + sorted(propers)[:2] + spoken[:2])
    return score, (f"{hits} concrete marker(s)" + (f": {found}" if found else
                   " - no number, no name, nothing checkable"))


def check_stakes(text):
    """Tension, cost, negation. Something the viewer might lose."""
    w = [norm(x) for x in words(text)]
    hits = [x for x in w if x in STAKES]
    markers = sorted(set(hits))
    if PRICE_RE.search(text):
        markers.append("a price")
    n = len(markers)
    score = {0: 20.0, 1: 70.0}.get(n, 100.0)
    detail = f"{n} tension marker(s)" + (f": {', '.join(markers[:4])}" if markers else
                                         " - nothing is at stake in this line")
    return clamp(score), detail


def check_frontload(text):
    """The interesting word cannot be in position nine."""
    w = words(text)
    if not w:
        return 0.0, "empty"
    low = [norm(x) for x in w]
    penalty = 0
    hit_opener = None
    for weak in WEAK_OPENERS:
        parts = weak.split()
        if low[:len(parts)] == parts:
            penalty, hit_opener = 30, weak
            break
    payload = None
    for i, token in enumerate(low):
        if (token in STAKES or token in SPOKEN_NUMBERS or token in MONEY_WORDS
                or NUMBER_RE.match(w[i]) or (i and PROPER_RE.match(w[i]))):
            payload = i
            break
    if payload is None:
        base = 30.0
        where = "no payload word anywhere in the line"
    elif payload <= 3:
        base = 100.0
        where = f"payload at word {payload + 1}"
    elif payload <= 6:
        base = 70.0
        where = f"payload at word {payload + 1}, could move forward"
    else:
        base = 40.0
        where = f"payload at word {payload + 1}, too late"
    detail = where + (f"; weak opener \"{hit_opener}\"" if hit_opener else "")
    return clamp(base - penalty), detail


def check_address(text):
    """Aimed at one viewer, or floating in the air."""
    low = fold(text)
    w = [norm(x) for x in words(text)]
    if VIEWER_RE.search(low):
        return 100.0, "speaks to the viewer"
    if w and w[0] in IMPERATIVES:
        return 90.0, f"imperative opener (\"{w[0]}\")"
    if FIRST_PERSON_RE.search(low) or any(
            len(x) >= 4 and x[-1] in "éí" and x not in NOT_PRETERITE
            for x in (t.lower() for t in words(text))):
        # Spanish drops the pronoun: "Perdí 18.000 €" is first person.
        return 70.0, "first person, no viewer named"
    return 35.0, "third person, nobody in the room"


CHECKS = ["LENGTH", "SPECIFICITY", "STAKES", "FRONTLOAD", "ADDRESS"]


def run(text):
    results = {
        "LENGTH": check_length(text),
        "SPECIFICITY": check_specificity(text),
        "STAKES": check_stakes(text),
        "FRONTLOAD": check_frontload(text),
        "ADDRESS": check_address(text),
    }
    flags = [msg for pattern, msg in DEALBREAKERS if pattern.search(text)]
    scores = [results[c][0] for c in CHECKS]
    # The weakest property caps the hook, same logic as detect.py: one bad
    # property is enough for the thumb to keep moving.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4 - len(flags) * 15
    overall = clamp(overall)
    verdict = "STRONG" if overall >= 70 and min(scores) >= 55 and not flags else (
        "OK" if overall >= 50 else "WEAK")
    return results, overall, verdict, flags


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render_one(text, results, overall, verdict, flags, out=sys.stdout):
    print("\nHOOK SCORE", file=out)
    print("=" * 62, file=out)
    print(f"  \"{text.strip()}\"\n", file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<13} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'HOOK SCORE':<13} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    for f in flags:
        print(f"\n  DEALBREAKER  {f}", file=out)
    if verdict != "STRONG":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Weakest property: {weakest}. Fix that one and re-run.", file=out)
    print("", file=out)


def render_table(rows, out=sys.stdout):
    print("\nHOOK RANKING\n" + "=" * 78, file=out)
    for i, r in enumerate(rows, 1):
        mark = "->" if i == 1 else "  "
        hook = r["hook"] if len(r["hook"]) <= 62 else r["hook"][:59] + "..."
        print(f"{mark} {r['score']:5.1f} {r['verdict']:<7} {hook}", file=out)
        print(f"        weakest: {r['weakest']} ({r['checks'][r['weakest']]['score']:.0f})", file=out)
        for f in r["flags"]:
            print(f"        dealbreaker: {f}", file=out)
    print("\nShoot the top one. If the top one is under 50, none of these are the hook.\n",
          file=out)


def main():
    ap = argparse.ArgumentParser(description="Score a Reel hook on five properties.")
    ap.add_argument("input", nargs="?", default="-", help="file with one hook per line, or -")
    ap.add_argument("--hook", help="score a single hook given on the command line")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.hook:
        lines = [args.hook]
    else:
        raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
    if not lines:
        print("nothing to score", file=sys.stderr)
        sys.exit(2)

    payload = []
    for line in lines:
        results, overall, verdict, flags = run(line)
        payload.append({
            "hook": line,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "weakest": min(CHECKS, key=lambda c: results[c][0]),
            "flags": flags,
            "score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if len(payload) > 1 else payload[0], indent=2, ensure_ascii=False))
        return

    if len(payload) == 1:
        results, overall, verdict, flags = run(lines[0])
        render_one(lines[0], results, overall, verdict, flags)
    else:
        render_table(sorted(payload, key=lambda r: -r["score"]))

    sys.exit(0 if max(p["score"] for p in payload) >= 70 else 1)


if __name__ == "__main__":
    main()
