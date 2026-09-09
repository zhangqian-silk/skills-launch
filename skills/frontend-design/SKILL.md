---
name: frontend-design
description: Design, implement, or review frontend interfaces when visual direction, interaction design, responsive layout, or accessibility is part of the task.
---

# Frontend Design

## Choose the mode

- **Design:** propose a visual and interaction direction for the requested surface; do not assume implementation is requested.
- **Implement or refine:** make the requested interface changes and verify the affected behavior.
- **Review:** inspect the existing interface and report actionable findings; do not edit unless fixes are requested.

Use only the modes requested. Inspect the relevant product context, existing UI, framework, and conventions. Preserve an established product language unless the user asks for a redesign. A local correction does not require a new visual direction or design system.

## Design a coherent interface

For new interfaces or requested redesigns, choose a deliberate visual direction appropriate to the audience. Define the typography, color roles, composition, and interaction states needed for the surface before polishing details.

- Where distinctiveness serves the product, use a strong composition, typographic voice, material treatment, or interaction motif.
- Make the primary action and information path obvious.
- Choose layouts and visual effects for the content and task. Familiar patterns and system fonts are valid when they fit; novelty alone is not a reason to replace them.
- Choose display and body typography that fit the brand and remain readable. Reuse existing fonts when continuity matters.
- Build a restrained semantic palette with explicit foreground, background, surface, border, accent, success, warning, and destructive roles.
- Vary density by task: operational interfaces may be compact; editorial and marketing surfaces need more rhythm and breathing room.
- Use motion to explain state or hierarchy. Respect reduced-motion preferences and avoid animation that delays routine work.

## Implement as a system

- Reuse the repository's components and tokens before creating parallel abstractions.
- Centralize repeated colors, spacing, radii, shadows, and motion values.
- Keep components responsive to their container and content, not only to a few fixed viewport widths.
- Prefer semantic HTML and native controls. Preserve visible focus, labels, error association, and keyboard navigation.
- Include hover, active, focus, disabled, loading, empty, error, and overflow behavior where applicable.

## Use the design search when it adds information

Run the bundled search without leaving the user's project directory when choosing an unfamiliar product pattern, palette, chart, font pairing, UX rule, or framework-specific convention. Resolve the absolute directory containing this `SKILL.md` file into `SKILL_ROOT`. Keep the user's project as the current working directory.

```bash
python3 "$SKILL_ROOT/scripts/search.py" "<product and task>" --domain <style|color|chart|landing|product|ux|typography|icons|web>
python3 "$SKILL_ROOT/scripts/search.py" "<implementation question>" --stack <react|nextjs|vue|svelte|swiftui|flutter|shadcn|html-tailwind>
```

Treat search output as candidates, not mandatory decisions. Do not run it when the repository already supplies the relevant design system. Persistence writes to the current project unless an explicit output directory is supplied.

## Verify the affected surface

Select checks for the changed or reviewed behavior: representative narrow and wide layouts for responsive changes, keyboard and focus behavior for interactive controls, and contrast, overflow, touch targets, or loading/empty/error states where affected. Inspect rendering when it is needed to support a visual claim; disclose limitations when browser tooling is unavailable.

For implementation, run the relevant formatter, type check, test, or build plus repository-required checks. Passing checks need not be repeated or broadened without new changes, failures, or unresolved concerns. Review stays read-only, including diagnostic commands.

Finish with the proposed direction, implemented change, or review findings for the selected mode, the evidence actually obtained, and any material gap. An implementation is complete when the requested surface works and its relevant checks are resolved, not merely when a first draft renders.
