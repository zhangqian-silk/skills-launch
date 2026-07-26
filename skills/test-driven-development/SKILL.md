---
name: test-driven-development
description: Apply risk-based testing and pre-handoff verification while implementing features, bug fixes, review fixes, refactors, and repository changes. Default to a direct minimal edit with targeted verification; use strict red-green-refactor only for genuinely risky promised behavior, reproducible regressions, or costly failure paths.
---

# Risk-Based Test-Driven Development

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful.

Choose the lightest process that gives credible evidence. Tests protect committed behavior; they do not create product requirements or justify production complexity by themselves.

## Fast path by default

Implement directly when the change is small, localized, and low-risk, such as documentation, prompts, labels, metadata, mechanical renames or moves, dead-code removal, simple configuration, formatting, or an obvious local correction already covered by stronger checks.

Confirm the change does not alter a public contract, meaningful branch, state transition, error path, persistence, or security boundary. Make the edit and run the narrowest relevant formatter, parser, build, smoke check, or existing test.

Do not create ceremonial tests that restate text, constants, mocks, or implementation details.

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
4. Run the focused test and relevant regression suite.
5. Refactor while tests remain green.

Prefer real behavior over mock assertions. Mock only external or slow boundaries after understanding the dependency and preserving relied-on side effects.

## Keep tests inside the complexity budget

- Lock down product or SLO commitments, expected operating paths, reproduced defects, and high-impact security or data-integrity boundaries.
- For explicit best-effort behavior, test the promised timeout, fast failure, terminal state, or recovery boundary rather than inventing stronger guarantees.
- Treat an automated review or generated extreme case as an input to evaluate. Do not add durable state, workers, retries, fallbacks, leases, acknowledgements, or protocol fields merely to make a theoretical test pass.
- If a test reveals an uncommitted edge case, first decide its acceptable failure semantics and evidence. Record residual risk when deferral is safe.
- Keep refactoring and reliability escalation separate: behavior-preserving simplification may remain even when a speculative mechanism is rejected.

## Review findings and handoff

For a review finding, reproduce it or establish a reachable control-flow path under supported operating assumptions before changing code. Add a regression test when the finding violates committed behavior and the test fails against the pre-fix behavior. If automation is disproportionate or unavailable, retain reproducible manual evidence instead.

Do not encode internal states that enforced boundaries cannot produce, unsupported deployment models, or combinations of independent failures merely because a reviewer can construct them. Tests should prove the accepted behavior and failure boundary, not promote every proposed counterexample into a permanent guarantee.

After all changes, compare the complete diff with the acceptance criteria and affected observable or error paths, then run the focused checks and appropriate regression suite once. Resolve gaps before handoff; passing tests alone do not prove that the implementation is complete or that every review finding is valid.

Escalate from the Fast path when scope, hidden behavior, or regression risk grows. If automated testing is unavailable, explain the limitation and use reproducible manual verification.

Finish with the exact test or validation commands run.
