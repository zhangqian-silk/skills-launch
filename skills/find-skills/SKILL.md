---
name: find-skills
description: Discover and evaluate installable agent skills when the user asks for a reusable capability, a skill recommendation, or a way to extend the current agent. Use when a specialized workflow may already exist and installing external code is potentially useful.
---

# Find Skills

## Discover

Clarify the concrete task, environment, and whether the user wants a recommendation or an installation. Search with specific capability terms:

```bash
npx skills find <query>
```

Try one or two alternate terms when the first query is weak. Do not keep broadening the search after clearly relevant candidates appear.

## Evaluate

Inspect a candidate before recommending it:

- Does its trigger and workflow match the requested task?
- Does it require tools, credentials, runtimes, or permissions the environment lacks?
- Is the source identifiable and maintained?
- Are its instructions concise, safe, and compatible with the current agent?
- Does an already-installed skill cover the same capability?

Prefer the smallest credible package. Popularity is supporting evidence, not proof of quality.

## Present and install

Present a short comparison with capability, important dependency, and installation scope. Installation changes the user's agent environment, so obtain confirmation before running:

```bash
npx skills add <package>
```

Use explicit target or global flags only when the user selected that scope. Do not bypass confirmation flags unless the user already authorized unattended installation.

After installation, verify that the expected Skill directory and `SKILL.md` exist and report any dependency that remains unavailable.

If no candidate is a good fit, say so and offer to complete the task with current capabilities or create a focused Skill when the workflow will recur.
