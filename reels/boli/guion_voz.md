# Guion de voz en off: "El del boli" (Altissia)

Duración del vídeo: **34,8 segundos** en la versión montada (1 s entre frases). Tono: cómplice, con guasa, como quien cuenta un drama
de trabajo a un compañero. Ritmo ágil (unas 165 palabras por minuto), sin prisa en los remates.

Cada frase tiene su ventana en el vídeo. Si la voz cae dentro de la ventana, cuadra con la
animación. Si sobra tiempo, mejor un silencio al final de la ventana que estirar la frase.

| ventana | frase | cómo decirla |
|---|---|---|
| 0:00 – 0:02,9 | **Nadie te avisó de los 500 albaranes.** | Arranca sin respirar antes. Tono de confidencia, "500" con peso. |
| 0:02,9 – 0:04,6 | **Cinco años de carrera.** | Con orgullo fingido. |
| 0:04,6 – 0:07,6 | **Para acabar comparando precios línea a línea con un boli,** | Se va desinflando. "Línea a línea" despacio, aburrido. |
| 0:07,6 – 0:10,4 | **un subrayador y un café frío.** | Pausa mínima antes de "café frío", dicho con pena. |
| 0:10,4 – 0:13,4 | **Se te escapa un error y adiós margen.** | "Adiós margen" como quien despide a alguien. |
| 0:13,4 – 0:15,0 | **Tu compañera usa Altissia.** | Cambio de tono: aquí cambia la música. Más ligero, casi con envidia. |
| 0:15,0 – 0:18,2 | **Coteja más de 500 albaranes en unos 5 segundos.** | Claro y limpio, es el dato. |
| 0:18,2 – 0:20,3 | **Revisas solo las diferencias y… café.** | "Café" seco, de remate. |
| 0:20,3 – 0:22,4 | **Tú vas por el 37.** | Remate: pausa corta antes, dicho con resignación. |
| 0:22,4 – 0:26,0 | **Etiqueta a quien sigue cotejando albaranes con boli.** | Sonriendo, invitando. |

## Texto seguido (para pegar en una app de texto a voz)

```
Nadie te avisó de los 500 albaranes.
Cinco años de carrera.
Para acabar comparando precios línea a línea con un boli... un subrayador y un café frío.
Se te escapa un error y adiós margen.
Tu compañera usa Altissia.
Coteja más de 500 albaranes en unos 5 segundos.
Revisas solo las diferencias y... café.
Tú vas por el 37.
Etiqueta a quien sigue cotejando albaranes con boli.
```

## Si usas texto a voz

- Elige una voz de **español de España** (no "español" a secas, que suele ser latino).
- Velocidad normal o un 5 % más rápida. Si el audio pasa de 24 segundos, súbela un poco o
  recorta la pausa entre frases.
- Si la app admite pausas (SSML), pon `<break time="300ms"/>` antes de "Tu compañera usa
  Altissia" y antes de "Tú vas por el 37": ahí están los dos giros del chiste.
- Pronunciación: "Altissia" se lee **al-TI-sia**. Si la app lo lee raro, escríbelo "Altisia".
- Exporta en WAV o MP3 a 44,1 o 48 kHz.

## Para montarlo

- `boli.mp4` ya lleva la música (baja, unos -28 LUFS) y los efectos. Pon la voz encima,
  empezando en 0:00, a unos **-16 LUFS** (lo normal en Instagram). La música quedará unos
  12 dB por debajo.
- Si quieres rehacer el equilibrio en tu editor (CapCut, Premiere, etc.), tienes las pistas
  sueltas: `boli_music.wav` (música) y `boli_sfx.wav` (efectos).
- La voz no debe pisar el primer fotograma: el gancho en pantalla ya funciona en silencio.

## Versión montada con la locución (boli_voz.mp4)

Locución: `locucion_elevenlabs.mp3` (ElevenLabs, voz en castellano). Cómo se ha montado:

1. `faster-whisper` transcribe la voz palabra a palabra (`words.json`).
   `respace.py words.json voz48.wav 1.0 voz_esp.wav timing.json` corta la locución en sus 10 frases
   por los silencios y las vuelve a montar con **1 s entre frase y frase** (versión actual, 34,8 s).
2. `timing.py words.json voz48.wav timing.json` saca dónde empieza cada frase (ajustado con la
   energía de la voz) y las palabras clave ("frío", "error", "adiós", "500", "café", "37").
3. `music.py` se genera a `7*4*60/inicio_Altissia` BPM, para que el cambio de la música caiga
   justo en "Tu compañera usa Altissia".
4. `build.py ... timing.json voz48.wav`: cada escena entra 0,12 s antes de su frase, los gestos
   caen en su palabra, la voz va a -16 LUFS, la música 14 LU por debajo con un hueco en 1-4 kHz
   y se aparta 7 dB mientras habla (vuelve en las pausas).

Comprobado con earshot (`boli_voz_sheet.png`): -13,7 LUFS, pico -1,5 dBTP; la voz queda
una mediana de 20 dB por encima de la música mientras habla.
