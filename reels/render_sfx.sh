#!/usr/bin/env bash
# Renderiza los efectos del reel desde el banco de earshot (deterministas, semilla fija).
set -e
cd "$(dirname "$0")/sfx"
earshot sfx render cut_hit/punch -o hit.wav
i=0; for p in G4 A4 B4 C5 D5 E5 F#5 G5; do earshot sfx render ui_pop/soft --pitch $p -o pop$i.wav; i=$((i+1)); done
earshot sfx render swish/flick -o swish.wav
earshot sfx render mallet/celesta --pitch G5 -o bell.wav
earshot sfx render notify/mid_wood --pitch G5 -o cta.wav
