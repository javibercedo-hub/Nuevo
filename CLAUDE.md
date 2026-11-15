# CLAUDE.md

This repo holds an Instagram skill pack (`.claude/skills/ig-*`, from
Jakeschincariol/instagram-agent-skill, adapted to Spanish from Spain).

- **Talk to the user in Spanish from Spain** (tú, no voseo).
- **Instagram state lives in `.claude/instagram/`** at the repo root, not in
  `~/.claude/instagram/`: `voice.md` (voice profile), `swipe.md` (`/ig-viral`),
  `log.md` (posted reels), `plan.md` (`/ig-plan`). Every `.claude/instagram/...`
  path in the skills is relative to the repo root, also when you run a skill's
  script from its own folder, so pass absolute paths to the scripts.
- **Sound: earshot** (`.claude/skills/earshot`, `.claude/skills/real-sound`, from
  Leonxlnx/earshot, MIT). The Python package is not in the repo: in a new
  session install it with `pip install "earshot[mcp] @ git+https://github.com/Leonxlnx/earshot"`
  (needs `huggingface.co` allowed for the models; `earshot sfx` / `kit` work without them).
  `real-sound` downloads from Freesound / Mixkit, which this environment's network does not allow.
- **Clipwing skills** (`.claude/skills/real-sfx`, `.claude/skills/hyperframes-to-after-effects`,
  from Clipwing/skills, MIT). `real-sfx` is set up with only the 78 bundled uisfx UI sounds
  (`config.json`, no own library yet; add one with `scripts/setup.py add-library`). Its optional
  listening model (`listen.py install`) downloads from download.pytorch.org / huggingface.co.
  `hyperframes-to-after-effects` needs Adobe After Effects, so it cannot run in a cloud session.
- **Reels** live in `reels/`: each one has its `build_*.py` (python3 -I build.py SOURCE OUT.mp4 reels/sfx),
  its effects in `reels/sfx/` (`render_sfx.sh`) and its `.cues.json` for `earshot timeline --cues`.
- Cloud sessions are ephemeral: after a skill writes or updates one of those
  files, commit it so it survives the session.
