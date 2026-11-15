#!/usr/bin/env bash
# Efectos del reel "el del boli", desde el banco de earshot (deterministas).
set -e
cd "$(dirname "$0")/sfx"
earshot sfx render cut_hit/punch -o hit.wav
earshot sfx render swish/flick -o swish.wav
earshot sfx render glitch/mid -o glitch.wav
earshot sfx render ui_pop/soft --pitch A4 -o pop.wav
earshot sfx render notify/mid_tine --pitch F5 -o chime.wav
earshot sfx render mallet/flourish -o done.wav
