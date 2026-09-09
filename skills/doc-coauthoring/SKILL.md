---
name: doc-coauthoring
description: Draft, revise, or review substantial specs, proposals, and decision documents that must make sense to readers outside the conversation.
---

# Document Coauthoring

Respond to the user in Simplified Chinese. Keep code, commands, identifiers, and proper nouns unchanged when useful. Preserve the document's requested language and terminology.

## Scope and context

Match the requested deliverable: draft or edit the document when requested, and keep review-only work read-only. For a targeted revision, preserve settled content and structure outside its scope.

Establish the audience, desired decision or action, required format, and hard constraints from supplied files and authorized sources. Accept shorthand or an unstructured context dump. Ask only when missing information materially changes the outcome, risk, or cost; otherwise continue with labeled assumptions and unknowns.

## Structure and draft

Use the smallest useful structure for the audience and requested format. Make the decision or intended action easy to find; develop high-uncertainty sections early when that helps resolve the rest.

Draft from the available facts and surface decision-relevant gaps, alternatives, risks, and evidence. Apply feedback as targeted edits rather than replacing settled text. Do not invent organizational context or evidence.

For proposals that substantially increase state, coordination, or operational cost, explain the commitment or failure they address, why a simpler approach is insufficient, and the added lifecycle cost. Distinguish measured evidence, constraints, reasoning, and assumptions; new designs do not require production measurements before a draft can proceed.

When justification is incomplete, present the mechanism as a proposal with a proportionate validation step, not an established requirement. Do not silently weaken a required guarantee to best-effort behavior; mark the unresolved tradeoff and complete the independent sections.

Stop elaborating when additional detail does not change a decision or improve the reader's ability to act.

## Reader-test

Review the completed document as a first-time reader without conversation context:

- Is the requested decision or action explicit?
- Are requirements separated from examples, assumptions, and future options?
- Does evidence support the claimed risk and proposed complexity?
- Where relevant, are alternatives, failure semantics, operational costs, and rollback represented fairly?
- Do commands, paths, owners, and success criteria resolve unambiguously?
- Can any section be removed without losing a decision-relevant fact?

Cold-read the document without relying on unstated conversation context. Use an independent reader only when available, authorized, and useful for a consequential ambiguity. For drafting or editing, fix concrete gaps and run applicable document checks plus repository-required checks; for review, report findings without rewriting.

## Boundaries

Local drafting and editing may proceed within the requested document. A draft request does not authorize publishing, external sharing, stakeholder notifications, or editing a remote canonical document. When those actions are explicitly requested, honor their authorized target and scope without an extra confirmation merely because this Skill is active.

Finish with the document or review result, checks actually performed, and any decision that still requires user input. Do not stop at an outline when a completed draft was requested and the available context supports one.
