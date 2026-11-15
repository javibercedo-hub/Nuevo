# Guion de voz en off: "El del boli" (Altissia)

Duración del vídeo: **26 segundos**. Tono: cómplice, con guasa, como quien cuenta un drama
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
| 0:15,0 – 0:18,2 | **Más de 500 albaranes en unos 5 segundos.** | Claro y limpio, es el dato. |
| 0:18,2 – 0:20,3 | **Mira solo las diferencias. Café.** | "Café" seco, de remate. |
| 0:20,3 – 0:22,4 | **Tú vas por el 37.** | Remate: pausa corta antes, dicho con resignación. |
| 0:22,4 – 0:26,0 | **Etiqueta a quien sigue cotejando albaranes con boli.** | Sonriendo, invitando. |

## Texto seguido (para pegar en una app de texto a voz)

```
Nadie te avisó de los 500 albaranes.
Cinco años de carrera.
Para acabar comparando precios línea a línea con un boli... un subrayador y un café frío.
Se te escapa un error y adiós margen.
Tu compañera usa Altissia.
Más de 500 albaranes en unos 5 segundos.
Mira solo las diferencias. Café.
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
