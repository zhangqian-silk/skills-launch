---
name: code-quality
description: Review code for actionable defects, simplify recently changed code without altering behavior, and keep implementations proportional to the task. Use for local diffs, pull requests, regression-focused review, maintainability review, cleanup, explicit simplification requests, or as an active discipline while implementing.
---

# Code Quality

Choose one mode from the user's intent. Do not silently turn a review into an edit or a simplification into a broad rewrite.

## Implementation discipline (active, while building)

Keep the implementation proportional to the task and its real operating constraints. Before adding any layer, abstraction, or safeguard, ask: does the current task actually need this? If the answer is "maybe later" or "to be safe," do not add it.

Default to the simplest structure that works:

- Match the complexity of the code to the complexity of the problem and its real operating constraints (scale, concurrency, failure mode, audience). Do not import patterns designed for a much harder problem into one that does not need them.
- Prefer one direct path over a framework of hooks, adapters, registries, or extension points for a single current use.
- Use the project's existing storage, transport, and error handling instead of introducing parallel ones.
- Add a table, index, trigger, or state machine only when the data or behavior genuinely requires it; not as a precaution.
- Keep files focused. If a file grows past a few hundred lines, split by responsibility rather than piling more in.

Specifically avoid:

- speculative validation, null checks, or error handling for inputs the caller never produces;
- retries, fallbacks, caches, feature flags, or migration paths the task does not mention;
- heavy reliability or coordination machinery (multi-phase commit, outbox, leases, epochs, sagas, distributed locks) for a problem that a single transaction, a plain retry loop, or a manual recovery step already covers;
- abstraction layers, interfaces, or plugins with exactly one implementation;
- defensive code that guards against hypothetical future requirements.

If a genuine edge case appears while working, handle it with the lightest fix that keeps the change coherent, then continue. Do not expand scope to cover every conceivable failure mode. When in doubt, do less.

This discipline applies during implementation, not only during review. If you realize a change you are making is growing beyond what the task asked for, stop and trim it back before continuing.

## Review mode

1. Determine the target: a PR, commit range, staged changes, working tree, or named files.
2. Read repository guidance and the change's stated purpose.
3. Inspect the diff before opening surrounding code needed to validate assumptions.
4. Run the smallest relevant existing checks when they are safe and useful.
5. Report only findings that are concrete, introduced by the change, and worth the author's attention.

Prioritize correctness, security, data loss, broken contracts, concurrency, error paths, and missing regression coverage. Also flag over-engineering introduced by the change: abstractions, layers, state machines, or safeguards that the task does not justify. Treat style preferences as findings only when they violate an established project rule or create a real maintenance hazard.

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
3. Identify unnecessary nesting, duplication, indirection, clever expressions, stale comments, and names that hide intent. Also identify whole layers, abstractions, and safeguards that the task no longer needs.
4. Preserve public interfaces, outputs, side effects, error behavior, performance characteristics that callers rely on, and test semantics.
5. Make the smallest coherent cleanup and run relevant checks.

Prefer explicit control flow and established abstractions. Do not collapse distinct responsibilities, remove useful boundaries, or optimize for fewer lines. If simplification would change observable behavior, stop and present it as a separate proposed change.

## Boundaries

- Review mode is read-only unless the user asks for fixes.
- Do not check out a PR, post a review, resolve comments, or publish changes without authorization for that external action.
- Use repository-defined validation commands; do not assume a language, package manager, or preflight script.
- Keep unrelated pre-existing issues outside the result unless they block evaluation of the requested change.

Finish with the checks actually run and any remaining uncertainty.
