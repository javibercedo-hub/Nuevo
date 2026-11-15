# CLAUDE.md

This repo holds an Instagram skill pack (`.claude/skills/ig-*`, from
Jakeschincariol/instagram-agent-skill, adapted to Spanish from Spain).

- **Talk to the user in Spanish from Spain** (tú, no voseo).
- **Instagram state lives in `.claude/instagram/`** at the repo root, not in
  `~/.claude/instagram/`: `voice.md` (voice profile), `swipe.md` (`/ig-viral`),
  `log.md` (posted reels), `plan.md` (`/ig-plan`). Every `.claude/instagram/...`
  path in the skills is relative to the repo root, also when you run a skill's
  script from its own folder, so pass absolute paths to the scripts.
- Cloud sessions are ephemeral: after a skill writes or updates one of those
  files, commit it so it survives the session.
