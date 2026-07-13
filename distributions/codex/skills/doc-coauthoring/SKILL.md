---
name: doc-coauthoring
description: Collaboratively plan, draft, revise, and reader-test substantial documents such as technical specs, RFCs, proposals, decision records, PRDs, and long-form README content. Use when the document must transfer context accurately to readers beyond the current conversation.
---

# Document Coauthoring

## 1. Gather the missing context

Establish the document type, primary audience, desired decision or action, required format, and hard constraints. Accept shorthand or an unstructured context dump.

Read supplied files and authorized connected sources. Ask only questions that materially affect the document. Continue until you can discuss tradeoffs and edge cases without asking for basic project facts.

## 2. Structure and draft

Propose the smallest useful section structure. Start with the section carrying the main decision or most uncertainty; write summaries last.

For each section:

1. Confirm its purpose and required facts.
2. Surface missing arguments, alternatives, risks, and evidence.
3. Draft directly into the working document.
4. Apply feedback as targeted edits rather than repeatedly replacing settled text.
5. Remove duplication and generic filler before moving on.

Preserve the user's terminology and confidence level. Separate facts, decisions, assumptions, and open questions. Do not invent organizational context or evidence.

## 3. Reader-test

Review the completed document as a first-time reader who lacks the conversation context:

- What decision or action does the document request?
- Which terms, prerequisites, or causal links remain implicit?
- Can a reader distinguish requirements from examples and future possibilities?
- Are alternatives and tradeoffs represented fairly?
- Do commands, paths, owners, and success criteria resolve unambiguously?
- Is any section repetitive or safe to remove?

Use an independent context when available. Otherwise perform a deliberate cold read based only on the document text. Fix concrete gaps and contradictions, then run format or link checks supported by the repository.

## Boundaries

Local drafting and editing may proceed within the requested document. Confirm before publishing, sharing externally, notifying stakeholders, or editing a remote canonical document when the user requested only a draft.

Finish by naming the document changed and any unresolved decision the reader still needs to make.
