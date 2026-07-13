---
name: test-driven-development
description: Apply risk-based testing while implementing features, bug fixes, refactors, and small repository changes. Use strict red-green-refactor for non-trivial or regression-prone behavior; use direct implementation plus targeted verification for small, low-risk changes where a new test would add little value.
---

# Risk-Based Test-Driven Development

Choose the lightest process that provides credible evidence.

## Use Strict TDD

Use red-green-refactor for:

- new or changed observable behavior;
- a reproducible bug or regression;
- non-trivial branching, state, parsing, retries, concurrency, or error handling;
- public interfaces, persistence, migrations, security boundaries, or high-risk refactors;
- changes where a future regression would be costly or hard to detect.

Cycle one behavior at a time:

1. Write the smallest test that expresses the required behavior.
2. Run it and confirm it fails for the missing behavior, not a setup mistake.
3. Implement only enough production code to pass.
4. Run the focused test and relevant regression suite.
5. Refactor only while tests remain green.

Prefer real behavior over mock assertions. Mock only external or slow boundaries after understanding the real dependency and preserve any side effects the test relies on.

## Use the Fast path

Implement directly when the change is small and low-risk, such as:

- documentation, comments, prompts, labels, or metadata;
- a simple configuration value with an existing validation path;
- formatting, renaming, file movement, or another mechanical transformation;
- an obvious local correction where a new test would duplicate stronger existing checks.

Before using the fast path, confirm the change does not alter a public contract, branch behavior, state transition, error path, or security boundary. Make the edit, run the narrowest relevant formatter, parser, build, smoke check, or existing test, and report that evidence.

Do not create ceremonial tests that merely restate text, constants, mocks, or implementation details.

## Escalate when risk grows

Switch from the fast path to Strict TDD if the edit expands in scope, reveals hidden behavior, lacks a reliable existing check, or produces a regression. If the project cannot support an automated test, explain the limitation and use a reproducible manual verification.

Finish with the test or validation commands actually run.
