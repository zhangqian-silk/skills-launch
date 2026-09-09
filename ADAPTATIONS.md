# Skill Adaptations

## References

- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#migration-quickstart
- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices
- Read 2026-07-13: https://developers.openai.com/codex/concepts/customization
- User-provided engineering-principles `AGENTS.md` (2026-08-18): source of the compatibility and defense boundaries merged into `engineering-quality`.
- Reviewed 2026-09-09: https://x.com/pvncher/status/2095991462416490862 — article text retrieved through a public mirror; embedded images were not verified.
- Reviewed 2026-09-09: https://developers.openai.com/api/docs/guides/latest-model — skill sensitivity, task completion, authorization boundaries, and proportionate verification.

## Adaptation policy

Originals preserve complete upstream context. `skills/` contains the maintained catalog: state each instruction once, retain non-obvious procedural knowledge, use progressive disclosure for runtime references, define autonomy and verification boundaries, and never hardcode a model or reasoning effort.

The former separate Claude and Codex distributions were consolidated on 2026-07-22. The curated catalog retains the smaller merged workflows previously maintained for Codex; the repository no longer provides agent-specific distributions or an automated installer.

2026-08-18 lean pass, per the prompting-best-practices guidance above: removed generic restatements of baseline model behavior and deduplicated the reliability-mechanism admission criteria into `engineering-quality`. Each remaining rule must encode a product requirement, a non-obvious procedure, or a boundary the model does not default to; generic wisdom is not re-added.

2026-09-02 design pass: renamed `code-quality` to `engineering-quality`, widened discovery to technical solution design and implementation planning, and reorganized the workflow around a shared quality standard with solution design, implementation/fix, review/re-review, and simplification modes. Complexity guidance now uses general, evidence-proportional mechanism selection across engineering domains and evaluates simplicity at the resulting design: reuse is preferred when it fits, while bounded redesign is appropriate when it produces a clearer root-cause solution with lower total lifecycle complexity. “Long-term optimal” is explicitly bounded by established commitments and current evidence rather than broad future compatibility. The upstream source mapping remains unchanged.

2026-09-09 workflow pass: shortened discovery descriptions and separated design, implementation, and read-only review. Existing authorization now carries through in-scope work without an extra approval checkpoint; credentials, ambiguous targets, and new authority still require user input. Engineering review distinguishes diff-introduced defects from existing-artifact audits. Document design arguments use proportionate evidence without requiring production measurements or silently weakening commitments. TDD retains regression tests by detection value and maintenance cost, replacing the earlier default-removal, exceptional-path exclusions, and seconds-scale suite rules. Relevant checks and repository-required checks remain mandatory; repetition or expansion needs new evidence.

The five remaining Skills stay self-contained: after removing duplicated rules, their mode-specific guidance is short enough that separate router files would add indirection without useful context savings. Runtime scripts and data are unchanged. No upstream refresh was performed in this pass.

Removed `find-skills`, its original, and its source/mapping entries on 2026-09-09 at the user's request. External Skill discovery and package-manager installation are no longer part of this catalog; installed copies outside this repository were not changed.

## Original catalog

| Original | Source |
| --- | --- |
| `frontend-design` | https://github.com/anthropics/skills/tree/main/skills/frontend-design |
| `doc-coauthoring` | https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md |
| `fullstack-developer` | https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/awesome_agent_skills/fullstack-developer |
| `code-reviewer` | https://github.com/google-gemini/gemini-cli/blob/main/.gemini/skills/code-reviewer/SKILL.md |
| `webapp-testing` | https://github.com/anthropics/skills/tree/main/skills/webapp-testing |
| `browser-use` | https://github.com/browser-use/browser-use/tree/main/skills/browser-use |
| `ui-ux-pro-max` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/main/.claude/skills/ui-ux-pro-max |
| `taste-skill` | https://github.com/leonxlnx/taste-skill/tree/main/skills/taste-skill |
| `code-simplifier` | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier |
| `test-driven-development` | https://github.com/obra/superpowers/tree/main/skills/test-driven-development |

The complete Superpowers suite and the Claude `code-review` plugin were intentionally removed. TDD remains as an ordinary source and maintained Skill.

## Skill map

| Skill | Original inputs | Adaptation |
| --- | --- | --- |
| `frontend-design` | frontend-design + ui-ux-pro-max + taste-skill | Separate design, implementation, and read-only review; retain coherent visual direction, accessible interactions, and optional deterministic search without prescribing novelty or unrelated checks. |
| `browser-workflows` | browser-use + webapp-testing | Merge live browser operation with local-server testing; preserve observed-state verification and the external CLI boundary; distinguish user handoff from already-authorized actions. |
| `engineering-quality` | code-reviewer + code-simplifier | Share outcome, evidence, and lifecycle-cost criteria across design, implementation, review, and simplification; distinguish audits from diff reviews and complete authorized fixes with focused re-review. |
| `doc-coauthoring` | doc-coauthoring | Keep context gathering, scoped drafting/revision/review, and reader testing; justify substantial mechanisms using available evidence and labeled assumptions without imposing a generic reliability admission gate. |
| `test-driven-development` | test-driven-development | Use risk-proportionate checks and test-first development where valuable; retain regression coverage by defect-detection value and maintenance cost, including important failure paths; stop repeating passing checks without new evidence. |

`fullstack-developer` remains in originals but is omitted as a standalone Skill because its broad framework knowledge duplicates baseline implementation capability.

Runtime resource removals drop `data/draft.csv`, `data/design.csv`, and the maintenance executable `data/_sync_all.py` from maintained Skills while preserving them in originals. Legal companions may remain when required by packaged runtime material. Maintained Skills contain no source-history documentation.

## Updating an adaptation

1. Run `python3 scripts/update_originals.py <name>`; it updates only the named original.
2. Review `git diff -- originals/<name>` and the mapped maintained Skills printed by the script.
3. Preserve unique workflows and deterministic resources; remove repeated general knowledge and platform-specific assumptions.
4. Apply selected changes manually. Never replace a maintained Skill with an original wholesale.
5. Keep decision rules in the narrowest Skill that reliably triggers for the task; avoid copying the same policy into multiple Skills.
6. Update this map when a capability is merged, split, renamed, retained, or omitted, then run focused checks.
