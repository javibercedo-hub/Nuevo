# Critique, round 1

| axis | score | basis |
|---|---|---|
| hook | 10.0 | first sound at 0.00s |
| sync | 10.0 | 9/9 sounds on their frame (peaks, arrivals, or first onsets for clicks) |
| coverage | n/a | 10 cues for 10 declared events (the list is the reference; runs and clusters are thinned on purpose) |
| pacing | 8.6 | 2.3 weighted events per 10 s, longest silence 3.1 s; 4.6 gestures per 10 s (the references run up to 15.11; this film has no sound of its own, so too busy is judged by that number) |
| variety | n/a | not judged: only interface sounds, runs and sounds of one physical source |
| hierarchy | 6.5 | 3.3 dB between the loud and the quiet sounds |
| headroom | 10.0 | true peak -1.9 dBTP |
| loudness | 8.0 | final -15.9 LUFS; target -14 LUFS not reached: the file measures -15.9 LUFS (sparse sound; going further would need heavy limiting) |
| mono | 10.0 | the SFX track loses 0.0 dB when folded to mono (0 = the channels agree, 3 = unrelated, 6+ = parts cancel); 0 of 10 sounds lose more than 6 dB |

**FIX**: lowest axis 6.5 (every axis must reach 8; ok to show)

Three worst problems, fix only these, re-render, run again:
1. hierarchy: all sounds sit within 3.3 dB; make the big moments clearly bigger and the small ticks quieter

Listen to this moment, on headphones and then once on a phone speaker. This script cannot hear: they are the places where the numbers above are least certain, and none of them says that it sounds good:
  1.    0.00s  'hit': the first sound of the film: the hook; the highest peak of the film (-14 dBFS before the master). Listen for: does it land with the picture at once, and is it clearly there under the music or the voice? / is it big without hurting on headphones, and does the music under it pump?
  (--listen-out FILE.wav cuts them into one file of the film's own sound)

(The sound of this film is only SFX: --style clean-sfx-refs sets it against nine finished SFX reels, numbers only, no scores.)

Still to judge by eye on review.png: character fit (each sound suits its picture), cleanliness (no mud in the low end under music/voice, nothing masks speech), taste (designed, not sprayed on).

---

# Critique, round 2

| axis | score | basis |
|---|---|---|
| hook | 10.0 | first sound at 0.00s |
| sync | 10.0 | 9/9 sounds on their frame (peaks, arrivals, or first onsets for clicks) |
| coverage | n/a | 10 cues for 10 declared events (the list is the reference; runs and clusters are thinned on purpose) |
| pacing | 8.6 | 2.3 weighted events per 10 s, longest silence 3.1 s; 4.6 gestures per 10 s (the references run up to 15.11; this film has no sound of its own, so too busy is judged by that number) |
| variety | n/a | not judged: only interface sounds, runs and sounds of one physical source |
| hierarchy | 8.4 | 5.9 dB between the loud and the quiet sounds |
| headroom | 10.0 | true peak -1.7 dBTP |
| loudness | 8.0 | final -17.3 LUFS; target -14 LUFS not reached: the file measures -17.3 LUFS (sparse sound; going further would need heavy limiting) |
| mono | 10.0 | the SFX track loses 0.0 dB when folded to mono (0 = the channels agree, 3 = unrelated, 6+ = parts cancel); 0 of 10 sounds lose more than 6 dB |

**PASS**: lowest axis 8.0 (every axis must reach 8; a new film needs at least 3 rounds)

Listen to this moment, on headphones and then once on a phone speaker. This script cannot hear: they are the places where the numbers above are least certain, and none of them says that it sounds good:
  1.    0.00s  'hit': the first sound of the film: the hook; the highest peak of the film (-11 dBFS before the master). Listen for: does it land with the picture at once, and is it clearly there under the music or the voice? / is it big without hurting on headphones, and does the music under it pump?
  (--listen-out FILE.wav cuts them into one file of the film's own sound)

(The sound of this film is only SFX: --style clean-sfx-refs sets it against nine finished SFX reels, numbers only, no scores.)

Still to judge by eye on review.png: character fit (each sound suits its picture), cleanliness (no mud in the low end under music/voice, nothing masks speech), taste (designed, not sprayed on).