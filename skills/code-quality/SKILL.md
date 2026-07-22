---
name: code-quality
description: Review code, guide implementation decisions, and simplify recent changes while keeping mechanisms proportional to current product commitments and evidence. Use for local diffs, pull requests, reliability or architecture tradeoffs, regression-focused review, maintainability review, cleanup, or explicit simplification requests.
---

# Code Quality

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful.

Choose the lowest-long-term-cost solution that satisfies the user's goal and known constraints. Count implementation, testing, migration, maintenance, operations, recovery, state, interfaces, configuration, cognitive load, reversibility, and future change cost. Optimize within current commitments, evidence, and reasonably foreseeable change; stop when marginal benefit no longer pays for added complexity.

When concerns conflict, prioritize:

1. Safety, authorization boundaries, and data integrity.
2. The user's explicit goal and product or SLO commitments.
3. Correctness and verifiability.
4. Long-term maintainability and evolvability.
5. Implementation simplicity, delivery speed, and diff size.

Treat elegance as satisfying the goal with the fewest necessary states, interfaces, branches, and special rules while remaining easy to explain, test, observe, change, and revert.

## Think and execute

- Start from the goal, constraints, acceptance criteria, and threat model. Challenge a false premise before building on it.
- Combine first principles, production evidence, official documentation, and mature engineering experience. Experience informs a decision; it does not settle it.
- Ask only when ambiguity materially changes the outcome, risk, or cost. Otherwise state a reasonable assumption and continue.
- Quantify probability, scope, thresholds, or cost when evidence permits. Distinguish facts, inferences, and unknowns.
- If the requested path is materially worse, complete compatible work and explain the better option and tradeoff concisely.
- Lead with the result. Add depth only to expose a wrong premise, hidden cost, material risk, or better path.

## Engineering complexity budget

Use the smallest sufficient mechanism for current commitments. Low probability alone is not a reason to ignore a risk, but a theoretical counterexample is not a reason to upgrade the system into a stronger distributed protocol.

Handle a case when at least one applies:

- Product behavior, an SLO, or a normal operating path such as rolling upgrades, reconnects, or timeouts requires it.
- Failure can cause privilege escalation, cross-tenant impact, irreversible data damage, duplicate side effects, or permanent or unbounded blocking.
- Production incidents, monitoring, load tests, fault injection, or official protocol documentation support it.
- A local, clear, low-maintenance fix closes the boundary without materially expanding the state machine or protocol.

Otherwise default to documenting and deferring when the case requires multiple independent low-probability failures outside deployment assumptions, SLOs, or an explicit best-effort boundary; safely converges through timeout, fast failure, a terminal state, user retry, or operational recovery; or lacks evidence while requiring durable state, recovery workers, distributed leases, protocol acknowledgements, or layered retry and fallback.

When deferring, record the failure semantics, impact scope, observability, residual risk, and best-effort boundary.

Before adding persistent state, a recovery worker, retry, fallback, cache-consistency protocol, table, or protocol field, require a bounded answer to:

1. Which product commitment, SLO, security boundary, or real failure requires it?
2. What evidence supports its probability and impact?
3. Why are timeout, fast failure, manual retry, or operational recovery insufficient?
4. What state, migration, configuration, monitoring, testing, and maintenance costs does it add?
5. How will activation be observed, and can observation precede implementation?

If these cannot be answered, do not add the mechanism. Record the boundary and improve observation first.

## Review mode

1. Determine the target and read repository guidance plus the change's stated purpose.
2. Inspect the diff before opening only the surrounding code needed to validate assumptions.
3. Run the smallest relevant existing checks when safe and useful.
4. Report only concrete, introduced, actionable findings whose impact justifies attention.

Prioritize correctness, security, data loss, broken contracts, concurrency, error paths, and missing regression coverage. Also flag new states, protocols, retries, fallbacks, or abstractions that fail the complexity budget. An automated review's theoretical counterexample is evidence to evaluate, not a requirement to implement.

For each finding provide severity, exact location, failing scenario, causal explanation, and a bounded correction direction. Lead with findings. If none meet the bar, say so and name any meaningful verification gap.

Review is read-only unless the user asks for fixes. Do not check out a PR, publish comments, resolve threads, or mutate remote state without authorization.

## Simplify mode

Limit scope to recently modified code unless the user names a broader target. Preserve public interfaces, outputs, side effects, relied-on error behavior, performance characteristics, and test semantics.

Keep a refactor with the feature when it does not expand runtime state, protocol surface, or operational burden; clearly reduces duplication, coupling, oversized functions, or ambiguous responsibility; lowers net long-term complexity; and remains easy to verify.

Split a refactor when it is unrelated to the goal, creates broad file churn or review surface, or adds abstraction without reducing actual complexity. Do not revert a verified net simplification merely to minimize diff size. Prefer explicit control flow and established abstractions; do not optimize for fewer lines.

Finish with the checks actually run and any remaining uncertainty.
