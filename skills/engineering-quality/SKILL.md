---
name: engineering-quality
description: Design, implement, review, and simplify engineering changes toward the simplest coherent end state. Use for technical approaches, nontrivial scope or architecture, code or design review, findings, and simplification; reuse established project logic first and apply bounded redesign when it lowers total lifecycle complexity under current evidence.
---

# Engineering Quality

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful.

Choose the solution with the lowest total lifecycle complexity that satisfies the user's goal and current commitments. Consider delivery, verification, adoption, coordination, operation, maintenance, reversibility, and future change supported by current evidence. Stop when additional structure no longer creates proportionate value.

## Choose the mode

- **Solution design:** define scope, compare approaches, make a technical decision, or prepare an implementation plan.
- **Implementation and fix:** implement an accepted design, correct a defect, or address accepted findings.
- **Review and re-review:** assess a bounded design or code change and verify its corrections.
- **Simplify:** reduce complexity while preserving intended behavior and contracts.

Use only the modes needed for the request.

## Shared quality standard

Start from the desired outcome, current commitments, acceptance criteria, supported assumptions, and relevant safety or authorization boundaries. Clarify only ambiguity that materially changes the outcome, risk, or cost; otherwise state a reasonable assumption and continue.

When concerns conflict, prioritize:

1. Safety, authorization boundaries, and data integrity.
2. The user's explicit goal and current product or operational commitments.
3. Correctness and credible verification.
4. Maintainability and ease of future change.
5. Simplicity, delivery speed, and change size.

Treat elegance as meeting the goal with a coherent set of concepts and responsibilities that is easy to explain, verify, operate, change, and revert. “Long-term”, “complete”, or “optimal” means the lowest total lifecycle complexity under established commitments and available evidence, not the broadest possible future compatibility. Value future options only when current evidence makes them reasonably foreseeable.

Judge simplicity by the resulting design rather than the size of the immediate change. Prefer reuse when existing logic expresses the intended responsibility cleanly. Use a bounded refactor or redesign when reshaping existing responsibilities produces a clearer root-cause solution and lower total lifecycle complexity.

Verification follows the same standard: gather enough evidence for the committed behavior and risk, while keeping the maintained verification burden proportionate.

## Solution design

1. Define the decision boundary: the requested outcome, affected users or systems, current constraints, and the smallest observable result that would satisfy the request.
2. Separate established facts and commitments from assumptions and future possibilities. Use current evidence to set present scope and to decide which future changes deserve design weight.
3. Understand the existing system before introducing structure. Reuse established concepts, ownership boundaries, interfaces, and operational practices where they fit.
4. Choose the smallest coherent end state. Use a local correction when the existing structure already supports the outcome cleanly; use a bounded refactor or redesign when the root cause lies in the current responsibilities or boundaries.
5. Compare viable approaches by correctness, user and operational impact, ease of verification, integration cost, maintenance burden, reversibility, and ease of revision when evidence changes.
6. Recommend one approach and explain why it is sufficient. State meaningful non-goals and the evidence that would justify later expansion.

Prefer decisions that remain easy to revise as evidence changes. When uncertainty is significant, choose an observable and reversible step that still delivers useful progress.

For any substantial new mechanism, explain the current outcome it enables, why a smaller use of existing mechanisms is insufficient, its lifecycle cost, and how its value will be observed. Persistent coordination or automated recovery are examples that often merit this explanation; they are not special categories or automatic requirements.

Organize delivery around meaningful outcomes. Keep tightly coupled changes together, and split work when parts are independently valuable and verifiable, can proceed safely with clear ownership, or benefit materially from risk isolation. Include coordination and integration cost in that decision.

Acceptance criteria should cover the committed normal behavior, demonstrated failures, and material boundaries supported by evidence. Keep future options separate from the recommended design.

## Implementation and fix

Before editing, confirm the accepted outcome, supported assumptions, affected contracts, and required evidence. For a proposed fix or finding, establish that the scenario is reachable and conflicts with intended behavior.

Prefer a focused root-cause correction that uses existing concepts and preserves intended contracts. Change size is an input to cost, not the objective: include bounded structural changes when they are needed to express the solution cleanly and reduce net complexity. Keep related changes together when that remains easy to verify; separate unrelated refactoring that would broaden the review surface.

Make uncertainty and failure explicit at the appropriate boundary. Rely on guarantees already enforced by types, validation, authorization, ownership, or upstream contracts, and add further protection when the supported risk requires it.

Preserve compatibility when current consumers, persisted information, staged adoption, or an explicit commitment requires it. When compatibility is transitional, record the condition for removing it.

Before handoff, inspect the complete final change once. Trace the materially affected decisions, branches, state transitions, contracts, consumers, side effects, and error paths. Run the smallest relevant checks and distinguish implementation self-checks from independent review.

## Review and re-review

1. Establish the baseline: the artifact or change being reviewed, its base, stated purpose, acceptance criteria, supported assumptions, and prior findings when applicable.
2. Inspect the complete bounded change before opening only the surrounding context needed to validate its effects.
3. Trace the materially affected paths, contracts, consumers, and operating behavior, and gather focused evidence where useful.
4. Complete one bounded pass across correctness, safety, authorization, data integrity, contracts, error handling, operability, verification, and complexity.
5. Report concrete, introduced, actionable findings whose avoided harm justifies the complete correction cost.

A finding should identify a supported scenario, the commitment or boundary it violates, the resulting impact, and how the reviewed change causes it. When evidence remains incomplete after a bounded investigation, present the issue as a question or verification gap rather than a confirmed defect.

Use the repository's severity scheme when defined. Otherwise calibrate urgency from reachability, impact, reversibility, and correction cost. Concentrate review attention on material correctness, security, data, contract, and operability outcomes.

For review-and-fix work, complete one bounded review, agree on the finding set, fix it as one batch, run the relevant checks, and re-review those fixes and their direct interactions. Reopen the set only when the fixes introduce a material issue or new evidence exposes a missed issue inside the original scope.

Review is read-only unless the user asks for fixes or another mutation. A clean review is a valid result.

## Simplify

Focus on the requested scope and its direct interactions. Preserve public interfaces, outputs, side effects, relied-on error behavior, performance characteristics, and verification semantics.

Keep a simplification when it reduces duplication, coupling, oversized responsibilities, ambiguous ownership, unnecessary concepts, or maintenance burden without expanding the operational surface. Prefer explicit flow and established concepts over clever compression, and judge simplicity by understanding and change cost rather than line count.

## Finish

State the decision or findings, the evidence and checks actually used, and any meaningful residual uncertainty or deliberately deferred boundary.
