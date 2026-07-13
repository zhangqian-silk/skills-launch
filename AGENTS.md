# Repository Instructions

This repository maintains original Skill sources and separate install-ready Claude and Codex distributions.

## Intent routing

- **Maintenance mode:** For requests to sync, add, remove, merge, adapt, or validate skills, read `ADAPTATIONS.md`, `skills.json`, the relevant `originals/` directories, and the affected distributions before editing.
- **Installation mode:** For requests to install skills, do not modify the repository. Read `skills.json` and install only from the requested `distributions/<agent>/skills/` entry.
- If the request does not identify maintenance versus installation or does not identify the target agent, ask before changing files or installing anything.

## Hard boundaries

- Treat `originals/` as upstream material. Only `python3 scripts/skills_launch.py sync` may replace it.
- Never install from `originals/` or fetch upstream content during installation.
- Keep all provenance and adaptation history in `ADAPTATIONS.md`, never inside distribution skills.
- Codex distributions may merge or omit originals when that produces a smaller, clearer workflow.
- Use `python3 scripts/skills_launch.py install <name> --agent codex` for Codex installation.

## Verification

Run before completing repository changes:

```bash
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```
