# Repository Instructions

Always respond in Simplified Chinese. Code, commands, identifiers, and proper nouns may remain in their original form.

This repository maintains complete upstream originals and a small curated Skill catalog.

## Usage and installation

- For requests to use or install a Skill, consider only directories currently present under `skills/`.
- Read the selected `skills/<name>/SKILL.md` and only the resources it references from the same Skill directory.
- Before installation, inspect existing common Skill locations in the target environment, such as `.agents/skills/`, `.codex/skills/`, and `.claude/skills/` under the project or user directory.
- If an existing Skill has similar functionality, tell the user its name, path, and main overlap. Ask whether to keep all overlapping Skills or only a selected subset; do not overwrite, delete, or merge anything before the user decides.
- Use locally installed Skills only for conflict detection, not as installation sources.
- Install by copying the complete selected Skill directory according to the target agent's conventions. The repository intentionally provides no installer.
- Do not inspect `originals/`, `skills.json`, `ADAPTATIONS.md`, or upstream repositories to expand or alter an installation.
- If the requested Skill is absent from `skills/`, report that it is unavailable. Do not substitute an original or fetch an external Skill.

## Maintenance workflow

- Before updating a source, read `skills.json`, `ADAPTATIONS.md`, the relevant `originals/` entry, and every mapped entry under `skills/`.
- Use `python3 scripts/update_originals.py [name ...]` to update originals. Do not replace `originals/` by another path.
- The update script must never modify `skills/`. Review the original diff, then apply selected changes to maintained Skills manually.
- Treat `originals/` as upstream material. Keep provenance and adaptation decisions in `ADAPTATIONS.md`, never inside `skills/`.
- Merge or omit upstream material when that produces a smaller, clearer workflow. Do not copy an original wholesale without reviewing overlap and platform assumptions.
- Do not add an installation script or package-management workflow.

## Verification

Run before completing repository changes:

```bash
python3 -m unittest discover -s tests -v
```
