---
name: test-driven-development
description: Apply risk-based testing and pre-handoff verification while implementing features, bug fixes, review fixes, refactors, and repository changes. Default to a direct minimal edit with targeted verification; use strict red-green-refactor only for genuinely risky promised behavior, reproducible regressions, or costly failure paths. Keep change-specific evidence temporary unless it protects a stable contract, and keep permanent regression coverage lean.
---

# Risk-Based Test-Driven Development

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful.

Choose the lightest process that gives credible evidence. Tests protect committed behavior; they do not create product requirements or justify production complexity by themselves.

## Fast path by default

Implement directly when the change is small, localized, and low-risk, such as documentation, prompts, labels, metadata, mechanical renames or moves, dead-code removal, simple configuration, formatting, or an obvious local correction already covered by stronger checks.

Confirm the change does not alter a public contract, meaningful branch, state transition, error path, persistence, or security boundary. Make the edit and run the narrowest relevant formatter, parser, build, smoke check, or existing test.

Do not create ceremonial tests that restate text, constants, mocks, or implementation details.

## Temporary change evidence and lean regression suite

A test written for the current requirement is development evidence; it does not become a permanent regression test automatically.

- Keep focused tests, reproductions, and one-off scripts while implementing and validating the current change. Remove them from the maintained suite before handoff unless they protect a stable user-visible contract, a reproduced defect with ongoing risk, or a high-impact security or data-integrity boundary.
- Run change-specific evidence only while developing or validating the current requirement; do not wire it into default CI or require unrelated future changes to rerun it.
- Keep the permanent regression suite small and seconds-scale, covering the core normal path and essential package or launch smoke. Do not add a broad diagnostic suite or require every development change to trigger one.
- Do not add permanent regression cases solely for malformed state, exceptional branches, deletion, abandonment or deprecation decisions, cleanup behavior, or reviewer-constructed edge combinations. Keep such evidence temporary unless the product explicitly commits to that behavior.

## Strict TDD when risk is real

Use red-green-refactor when all three hold:

1. The change introduces or modifies promised observable behavior with meaningful branching, state, parsing, retries, concurrency, or error handling.
2. Regression would be costly, silent, or hard to detect manually.
3. No reliable existing check covers the path.

Typical triggers include a reproducible bug, public interface change, persistence or migration, security boundary, duplicate side effect, irreversible data damage, or high-risk refactor.

Cycle one behavior at a time:

1. Write the smallest test expressing the required behavior.
2. Confirm it fails because the behavior is missing.
3. Implement only enough production code to pass.
4. Run the focused change test or reproducible evidence; run the existing lean core smoke only when the changed path affects it.
5. Refactor while tests remain green.

Prefer real behavior over mock assertions. Mock only external or slow boundaries after understanding the dependency and preserving relied-on side effects.

## Keep tests inside the complexity budget

- Lock down product or SLO commitments, expected operating paths, reproduced defects, and high-impact security or data-integrity boundaries.
- For explicit best-effort behavior, test the promised timeout, fast failure, terminal state, or recovery boundary rather than inventing stronger guarantees.
- Treat generated extreme cases as input to evaluate, not requirements; do not add production mechanisms merely to make a theoretical test pass.
- If a test reveals an uncommitted edge case, first decide its acceptable failure semantics and evidence. Record residual risk when deferral is safe.
- Do not promote a focused requirement test to permanent regression coverage unless it protects a stable committed contract or a demonstrated high-impact defect.
- Keep refactoring and reliability escalation separate: behavior-preserving simplification may remain even when a speculative mechanism is rejected.

## Review findings and handoff

For a review finding, reproduce it or establish a reachable control-flow path under supported operating assumptions before changing code. Add a permanent regression test only when the finding violates a stable committed contract or a demonstrated high-impact boundary, and the test belongs in the lean core suite. Otherwise retain a focused temporary reproducer or manual evidence and remove it before handoff.

Tests prove accepted behavior and failure boundaries; do not encode states that enforced boundaries cannot produce, unsupported deployments, or independent-failure combinations merely because a reviewer can construct them.

After all changes, compare the complete diff with the acceptance criteria and affected observable or error paths, then run the focused checks and, when affected, the existing lean core smoke once. Do not expand permanent regression coverage for exceptional, deletion, abandonment, or deprecation-judgment paths unless they are explicit product commitments. Resolve gaps before handoff; passing tests alone do not prove the implementation is complete.

Escalate from the Fast path when scope, hidden behavior, or regression risk grows. If automated testing is unavailable, explain the limitation and use reproducible manual verification.

Finish with the exact test or validation commands run.
