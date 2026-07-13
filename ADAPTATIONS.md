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
| `frontend-design` | https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md |
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

Claude keeps one standard Skill for every original. Standard upstream Skill folders retain their workflows and functional resources. `code-simplifier` is normalized from a plugin agent prompt into `SKILL.md`, drops the pinned model and fixed project conventions, and follows the target repository's instructions. Claude TDD retains the original strict bias. No Claude distribution includes source-history documentation.

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
