---
name: test-driven-development
description: Apply risk-based testing while implementing features, bug fixes, refactors, and small repository changes. Default to a direct, minimal edit with targeted verification; use strict red-green-refactor only for genuinely risky behavior. Resist over-engineering and defensive layers that the task does not ask for.
---

# Risk-Based Test-Driven Development

Default to the lightest process that gives credible evidence. Most changes are small and low-risk; do not escalate to Strict TDD or add protective layers unless the change is genuinely risky.

## Start with the Fast path (default)

Implement directly when the change is small, localized, and low-risk. This is the expected default, not an exception. Examples:

- documentation, comments, prompts, labels, or metadata;
- renaming a field, variable, or function with mechanical call-site updates;
- removing dead code, an unused branch, or a no-longer-needed feature;
- a simple configuration value with an existing validation path;
- formatting, file movement, or another mechanical transformation;
- an obvious local correction where a new test would duplicate stronger existing checks;
- a tweak to copy, styling, or a constant that does not change control flow.

Confirm the change does not alter a public contract, branch behavior, state transition, error path, or security boundary. Make the edit, run the narrowest relevant formatter, parser, build, smoke check, or existing test, and report that evidence.

Do not create ceremonial tests that merely restate text, constants, mocks, or implementation details. A test that only asserts "the code does what the code does" is waste.

## Escalate to Strict TDD only when risk is real

Use red-green-refactor only when all three hold:

1. the change introduces or modifies observable behavior with meaningful branching, state, parsing, retries, concurrency, or error handling;
2. a future regression would be costly, silent, or hard to detect manually;
3. no existing test already covers the path.

Typical triggers: a reproducible bug or regression, a public interface change, persistence or migrations, security boundaries, or a high-risk refactor touching shared logic.

If you are unsure whether a change qualifies, stay on the Fast path. Strict TDD is a deliberate escalation, not the starting posture.

Cycle one behavior at a time:

1. Write the smallest test that expresses the required behavior.
2. Run it and confirm it fails for the missing behavior, not a setup mistake.
3. Implement only enough production code to pass.
4. Run the focused test and relevant regression suite.
5. Refactor only while tests remain green.

Prefer real behavior over mock assertions. Mock only external or slow boundaries after understanding the real dependency and preserve any side effects the test relies on.

## Resist over-engineering

Implement the smallest change that satisfies the request. Do not preemptively add:

- validation, null checks, or error handling for inputs the caller never produces;
- abstraction layers, interfaces, or extension points for a single current use;
- retries, fallbacks, caches, or feature flags the task does not mention;
- generic frameworks to solve one specific problem;
- speculative "defensive" code that guards against hypothetical future requirements.

If a genuine edge case appears while working, handle it with the lightest fix that keeps the change coherent, then continue. Do not expand scope to cover every conceivable failure mode. When in doubt, do less.

## Escalate when risk grows

Switch from the Fast path to Strict TDD if the edit expands in scope, reveals hidden behavior, lacks a reliable existing check, or produces a regression. If the project cannot support an automated test, explain the limitation and use a reproducible manual verification.

Finish with the test or validation commands actually run.
