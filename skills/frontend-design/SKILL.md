---
name: frontend-design
description: Design, implement, or review distinctive production frontend interfaces and design systems. Use for pages, components, dashboards, landing pages, responsive UI, accessibility, visual polish, or requests to improve generic-looking frontend work.
---

# Frontend Design

## Deliver

1. Inspect the product context, existing UI, framework, and repository conventions.
2. Choose one deliberate visual direction appropriate to the audience and task.
3. Define typography, color roles, spacing, composition, interaction states, and motion before polishing individual elements.
4. Implement the smallest coherent system that covers the requested surface.
5. Verify responsive behavior, keyboard use, contrast, loading/empty/error states, and visual consistency.

Preserve an established product language unless the user asks for a redesign. When no language exists, make a clear choice instead of assembling unrelated fashionable effects.

## Make the result distinctive

- Give the interface one memorable visual idea: a strong composition, typographic voice, material treatment, illustration system, or interaction motif.
- Use hierarchy rather than decoration. Make the primary action and information path obvious.
- Avoid interchangeable hero layouts, uniform card grids, default font stacks, gratuitous gradients, and decorative glass effects without product meaning.
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
- Keep decorative code subordinate to content and interaction correctness.

## Use the design search when it adds information

Run the bundled search without leaving the user's project directory when choosing an unfamiliar product pattern, palette, chart, font pairing, UX rule, or framework-specific convention. Resolve the absolute directory containing this `SKILL.md` file into `SKILL_ROOT`. Keep the user's project as the current working directory.

```bash
python3 "$SKILL_ROOT/scripts/search.py" "<product and task>" --domain <style|color|chart|landing|product|ux|typography|icons|web>
python3 "$SKILL_ROOT/scripts/search.py" "<implementation question>" --stack <react|nextjs|vue|svelte|swiftui|flutter|shadcn|html-tailwind>
```

Treat search output as candidates, not mandatory decisions. Do not run it when the repository already supplies the relevant design system. Persistence writes to the current project unless an explicit output directory is supplied.

## Verify

- Run the repository's relevant formatter, type checker, tests, and build.
- Inspect the rendered result at representative narrow and wide sizes when browser tooling is available.
- Check the primary task without a mouse.
- Confirm text contrast, focus visibility, content overflow, and touch target usability.
- Remove visual elements that do not improve hierarchy, comprehension, or brand character.

Finish with a concise summary of the implemented direction and the checks actually run.
