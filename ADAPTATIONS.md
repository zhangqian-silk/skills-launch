# Skill Adaptations

## References

- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#migration-quickstart
- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices
- Read 2026-07-13: https://developers.openai.com/codex/concepts/customization

## Distribution policy

Originals preserve complete upstream context. Claude distributions normalize packages into directly installable standard skills. Codex distributions state each instruction once, retain only non-obvious procedural knowledge, use progressive disclosure for runtime references, define autonomy and verification boundaries, and never hardcode a model or reasoning effort.

## Original catalog

| Original | Source |
| --- | --- |
| `frontend-design` | https://github.com/anthropics/skills/tree/main/skills/frontend-design |
| `doc-coauthoring` | https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md |
| `fullstack-developer` | https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/awesome_agent_skills/fullstack-developer |
| `code-reviewer` | https://github.com/google-gemini/gemini-cli/blob/main/.gemini/skills/code-reviewer/SKILL.md |
| `webapp-testing` | https://github.com/anthropics/skills/tree/main/skills/webapp-testing |
| `browser-use` | https://github.com/browser-use/browser-use/tree/main/skills/browser-use |
| `find-skills` | https://github.com/vercel-labs/skills/tree/main/skills/find-skills |
| `ui-ux-pro-max` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/main/.claude/skills/ui-ux-pro-max |
| `taste-skill` | https://github.com/leonxlnx/taste-skill/tree/main/skills/taste-skill |
| `code-simplifier` | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier |
| `test-driven-development` | https://github.com/obra/superpowers/tree/main/skills/test-driven-development |

The complete Superpowers suite and the Claude `code-review` plugin were intentionally removed. TDD remains as an ordinary source and distribution skill.

## Claude map

| Claude distribution | Original input | Adaptation |
| --- | --- | --- |
| `frontend-design` | frontend-design | Retain the upstream workflow and its frontend license companion, `LICENSE.txt`. |
| `doc-coauthoring` | doc-coauthoring | Retain the standard coauthoring workflow without source-history material. |
| `fullstack-developer` | fullstack-developer | Retain the broad implementation workflow as a standalone Claude Skill. |
| `code-reviewer` | code-reviewer | Retain the review workflow in standard Skill packaging. |
| `webapp-testing` | webapp-testing | Portability rewrite: resolve the installed helper through `SKILL_ROOT`, preserve the user's project cwd and artifact paths, harden server lifecycle logging and cleanup, and retain the referenced license companion. |
| `browser-use` | browser-use | Retain the CLI workflow and declare the external command dependency in the manifest. |
| `find-skills` | find-skills | Retain discovery and evaluation as a standard Skill. |
| `ui-ux-pro-max` | ui-ux-pro-max | Portability rewrite: resolve search scripts through `SKILL_ROOT`, preserve project-relative persistence, and keep only data reached by runtime code. |
| `taste-skill` | taste-skill | Apply identity normalization so frontmatter matches the catalog and directory; retain `design-taste-frontend` as an install alias. |
| `code-simplifier` | code-simplifier | Apply plugin normalization from an agent prompt into `SKILL.md`; drop the pinned model and fixed project conventions. |
| `test-driven-development` | test-driven-development | Retain the upstream strict bias as a standalone Skill. |

Runtime resource removals drop `data/draft.csv`, `data/design.csv`, and the maintenance executable `data/_sync_all.py` from affected Claude and Codex distributions while preserving them in originals. License companions are a legal exception to runtime-only distribution content; they remain beside a Skill when its frontmatter points to their complete terms. No Claude distribution includes source-history documentation.

## Codex map

| Codex distribution | Original inputs | Adaptation |
| --- | --- | --- |
| `frontend-design` | frontend-design + ui-ux-pro-max + taste-skill | Merge visual direction, UX checks, implementation constraints, and deterministic design search; remove repeated aesthetic slogans and fixed repository paths. |
| `browser-workflows` | browser-use + webapp-testing | Merge live browser operation with local-server testing; keep the external CLI boundary and remove platform-specific workspace assumptions. |
| `code-quality` | code-reviewer + code-simplifier | Route review and simplification as separate modes; remove fixed package-manager commands, model selection, and project-file assumptions. |
| `doc-coauthoring` | doc-coauthoring | Compress context gathering, section drafting, and reader testing; replace named platform tools and connectors with capability-based actions. |
| `test-driven-development` | test-driven-development | Use strict TDD for risky behavior and a targeted fast path for small low-risk edits. |
| `find-skills` | find-skills | Keep discovery and evaluation concise; require authorization before installation. |

`fullstack-developer` remains in originals and the Claude distribution but is omitted as a standalone Codex skill because its broad framework knowledge duplicates Codex's baseline capability.

## Updating an adaptation

1. Sync only the named source into `originals/`.
2. Read the changed original and the existing target distribution.
3. Decide independently which platform benefits from the new material.
4. Preserve unique workflows and deterministic resources; remove repeated general knowledge and platform-specific assumptions.
5. Update this mapping when a capability is merged, split, renamed, retained, or omitted.
6. Run repository validation and tests. Never copy this record into a distribution directory.
