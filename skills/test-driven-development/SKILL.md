---
name: test-driven-development
description: Select risk-proportionate verification and regression coverage for implementation changes and bug fixes, using test-first development where it adds confidence.
---

# Risk-Based Test-Driven Development

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful.

Choose the lightest process that gives credible evidence for the affected behavior. Tests protect requirements and supported failure boundaries; they do not create new product guarantees. Honor explicit testing requirements and repository-required checks.

## Choose the verification path

For small, localized, low-risk changes, implement directly and use the narrowest relevant existing check. Assess the effect rather than the file type: a prompt or configuration change can still alter authorization, persistence, or other important behavior.

Use a focused test-first cycle when changing meaningful behavior whose regression would be costly, silent, or hard to detect, and existing checks do not cover it. Typical cases include parsing, state transitions, public interfaces, concurrency, persistence, or security boundaries. For a bug, reproduce the failure or establish a reachable path that violates intended behavior before fixing it.

Do not add tests that merely repeat text, constants, mocks, or implementation details. When a reliable existing test covers the behavior, reuse it instead of creating a parallel one.

## Test-first cycle

1. Write the smallest test for the required behavior or demonstrated failure.
2. Confirm that it fails for the intended reason, not a broken setup.
3. Implement the correction and run the focused test.
4. Refactor as needed while the affected tests remain green.

Prefer observable behavior and real dependencies where practical. Mock slow or external boundaries when needed, preserving the contracts and side effects relevant to the test.

If automation is unavailable, use reproducible manual evidence and disclose its limitations. Increase verification when the change reveals additional behavior or risk.

## Decide what to retain

Keep regression tests when their likely defect-detection value justifies execution and maintenance cost. Stable contracts, reproduced bugs with recurrence risk, and important security or data-integrity boundaries are strong candidates.

Temporary diagnostics and exploratory scripts need not enter the maintained suite. Remove task-created scratch artifacts when no longer useful, but do not delete useful regression coverage merely because it was written for this change or exercises an error, cleanup, or deletion path. Removing or weakening existing tests requires a change-supported reason, not a generic suite-size target.

Keep feedback efficient through focused checks and the repository's test organization. Do not impose a universal runtime target or restrict permanent coverage to the happy path.

## Bound the guarantees

- Test committed behavior, supported operating paths, and material failure boundaries.
- For explicit best-effort behavior, test the promised timeout, fast failure, terminal state, or recovery boundary rather than inventing stronger guarantees.
- Treat generated edge cases as evidence to evaluate. Check reachability, impact, and existing guarantees before adding a production mechanism.
- Do not dismiss a reachable security or data-integrity failure merely because it was not explicitly listed in a product requirement.

## Finish

Compare the final change with the requested outcome and affected behavior. Run relevant checks and all repository-required checks; resolve failures caused by the change. Once they pass, broaden or repeat verification only for new changes, failures, or unresolved concerns.

Report the exact validation commands run, their results, and any material gap. Passing tests does not replace completing the requested implementation.
