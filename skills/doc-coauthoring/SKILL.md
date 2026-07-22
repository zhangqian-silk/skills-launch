---
name: doc-coauthoring
description: Collaboratively plan, draft, revise, and reader-test substantial documents such as technical specs, RFCs, proposals, decision records, PRDs, and long-form README content. Use when the document must transfer context, evidence, decisions, and tradeoffs accurately beyond the current conversation.
---

# Document Coauthoring

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful. Preserve the document's requested language and terminology.

## 1. Gather the missing context

Establish the document type, audience, desired decision or action, current product commitment, success criteria, required format, and hard constraints. Accept shorthand or an unstructured context dump.

Read supplied files and authorized sources. Ask only questions whose answer materially changes the decision, risk, or cost. Continue when a reasonable assumption preserves the outcome; label assumptions, facts, inferences, and unknowns.

## 2. Structure and draft

Propose the smallest useful section structure. Start with the decision or highest uncertainty; write summaries last.

For each section:

1. Confirm its purpose and required facts.
2. Surface missing arguments, alternatives, risks, evidence, and reversibility.
3. Draft directly into the working document.
4. Apply feedback as targeted edits rather than replacing settled text.
5. Remove duplication and generic filler.

Do not invent organizational context or evidence. Quantify probability, scope, thresholds, cost, or SLO impact when possible. Stop elaborating when additional detail does not change a decision or make implementation safer.

## Reliability mechanism admission

When a design proposes persistent state, a recovery worker, retry, fallback, cache-consistency protocol, table, migration, distributed lease, acknowledgement, or protocol field, require the document to state:

1. The product commitment, SLO, security boundary, or observed failure it protects.
2. Probability, impact scope, and evidence from production, monitoring, load tests, fault injection, or official protocol documentation.
3. The simplest acceptable failure semantics and why timeout, fast failure, manual retry, or operational recovery are insufficient.
4. Added state, migration, configuration, monitoring, testing, operational, and maintenance cost.
5. How activation will be observed and whether observation can be added before the mechanism.

If the case is not established, document the failure semantics, impact scope, residual risk, observability, and best-effort boundary instead of presenting the mechanism as required. Separate present commitments from future possibilities.

## 3. Reader-test

Review the completed document as a first-time reader without conversation context:

- Is the requested decision or action explicit?
- Are requirements separated from examples, assumptions, and future options?
- Does evidence support the claimed risk and proposed complexity?
- Are alternatives, failure semantics, operational costs, and rollback represented fairly?
- Do commands, paths, owners, and success criteria resolve unambiguously?
- Can any section be removed without losing a decision-relevant fact?

Use an independent context when available; otherwise cold-read only the document. Fix concrete gaps and contradictions, then run repository-supported format or link checks.

## Boundaries

Local drafting and editing may proceed within the requested document. Confirm before publishing, sharing externally, notifying stakeholders, or editing a remote canonical document when the user requested only a draft.

Finish by naming the document changed and any unresolved decision.
