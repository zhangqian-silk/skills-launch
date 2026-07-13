---
name: code-quality
description: Review code for actionable defects or simplify recently changed code without altering behavior. Use for local diffs, pull requests, regression-focused review, maintainability review, cleanup, or explicit simplification requests.
---

# Code Quality

Choose one mode from the user's intent. Do not silently turn a review into an edit or a simplification into a broad rewrite.

## Review mode

1. Determine the target: a PR, commit range, staged changes, working tree, or named files.
2. Read repository guidance and the change's stated purpose.
3. Inspect the diff before opening surrounding code needed to validate assumptions.
4. Run the smallest relevant existing checks when they are safe and useful.
5. Report only findings that are concrete, introduced by the change, and worth the author's attention.

Prioritize correctness, security, data loss, broken contracts, concurrency, error paths, and missing regression coverage. Treat style preferences as findings only when they violate an established project rule or create a real maintenance hazard.

For each finding provide:

- severity and concise title;
- exact file and line;
- the failing scenario or affected behavior;
- why the current code causes it;
- a bounded correction direction.

Lead with findings ordered by severity. If none meet the bar, say so and mention any meaningful verification gap. Do not add praise, summaries, or speculative concerns that obscure the result.

## Simplify mode

1. Limit scope to recently modified code unless the user names a broader target.
2. Read nearby code and project conventions before editing.
3. Identify unnecessary nesting, duplication, indirection, clever expressions, stale comments, and names that hide intent.
4. Preserve public interfaces, outputs, side effects, error behavior, performance characteristics that callers rely on, and test semantics.
5. Make the smallest coherent cleanup and run relevant checks.

Prefer explicit control flow and established abstractions. Do not collapse distinct responsibilities, remove useful boundaries, or optimize for fewer lines. If simplification would change observable behavior, stop and present it as a separate proposed change.

## Boundaries

- Review mode is read-only unless the user asks for fixes.
- Do not check out a PR, post a review, resolve comments, or publish changes without authorization for that external action.
- Use repository-defined validation commands; do not assume a language, package manager, or preflight script.
- Keep unrelated pre-existing issues outside the result unless they block evaluation of the requested change.

Finish with the checks actually run and any remaining uncertainty.
