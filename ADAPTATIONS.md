# Skill Adaptations

## References

- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#migration-quickstart
- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices
- Read 2026-07-13: https://developers.openai.com/codex/concepts/customization
- User-provided engineering-principles `AGENTS.md` (2026-08-18): source of the compatibility and defense boundaries merged into `code-quality`.

## Adaptation policy

Originals preserve complete upstream context. `skills/` contains the maintained catalog: state each instruction once, retain non-obvious procedural knowledge, use progressive disclosure for runtime references, define autonomy and verification boundaries, and never hardcode a model or reasoning effort.

The former separate Claude and Codex distributions were consolidated on 2026-07-22. The curated catalog retains the smaller merged workflows previously maintained for Codex; the repository no longer provides agent-specific distributions or an automated installer.

2026-08-18 lean pass, per the prompting-best-practices guidance above: removed generic restatements of baseline model behavior and deduplicated the reliability-mechanism admission criteria into `code-quality`. Each remaining rule must encode a product requirement, a non-obvious procedure, or a boundary the model does not default to; generic wisdom is not re-added.

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

The complete Superpowers suite and the Claude `code-review` plugin were intentionally removed. TDD remains as an ordinary source and maintained Skill.

## Skill map

| Skill | Original inputs | Adaptation |
| --- | --- | --- |
| `frontend-design` | frontend-design + ui-ux-pro-max + taste-skill | Merge visual direction, UX checks, implementation constraints, and deterministic design search; remove repeated aesthetic slogans and fixed repository paths. |
| `browser-workflows` | browser-use + webapp-testing | Merge live browser operation with local-server testing; keep the external CLI boundary and remove platform-specific workspace assumptions. |
| `code-quality` | code-reviewer + code-simplifier | Merge review, simplification, implementation discipline, and evidence-based risk and complexity budgeting; require comprehensive bounded first reviews, reachability- and ROI-backed P1/P2 findings, batched fixes, and convergent re-reviews while rejecting speculative reliability machinery, backward-compat shims, swallowed errors, and symptom-level patches. |
| `doc-coauthoring` | doc-coauthoring | Compress context gathering, drafting, and reader testing; keep a compact reliability-mechanism admission trigger, with the full evidence and lifecycle-cost criteria living in `code-quality`. |
| `test-driven-development` | test-driven-development | Use strict TDD for genuinely risky committed behavior and targeted temporary evidence for current changes; promote a test to permanent coverage only for a stable contract or demonstrated high-impact defect. Keep regression coverage lean and seconds-scale around the core path, and do not turn exceptional, deletion, abandonment, or deprecation-judgment cases into permanent requirements. |
| `find-skills` | find-skills | Keep discovery and evaluation concise; require authorization before installation. |

`fullstack-developer` remains in originals but is omitted as a standalone Skill because its broad framework knowledge duplicates baseline implementation capability.

Runtime resource removals drop `data/draft.csv`, `data/design.csv`, and the maintenance executable `data/_sync_all.py` from maintained Skills while preserving them in originals. Legal companions may remain when required by packaged runtime material. Maintained Skills contain no source-history documentation.

## Updating an adaptation

1. Run `python3 scripts/update_originals.py <name>`; it updates only the named original.
2. Review `git diff -- originals/<name>` and the mapped maintained Skills printed by the script.
3. Preserve unique workflows and deterministic resources; remove repeated general knowledge and platform-specific assumptions.
4. Apply selected changes manually. Never replace a maintained Skill with an original wholesale.
5. Keep decision rules in the narrowest Skill that reliably triggers for the task; avoid copying the same policy into multiple Skills.
6. Update this map when a capability is merged, split, renamed, retained, or omitted, then run focused checks.
