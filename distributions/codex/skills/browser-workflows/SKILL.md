---
name: browser-workflows
description: Operate a browser and verify web applications through Browser Use, including navigation, interaction, screenshots, extraction, console inspection, and local-server testing. Use when a task requires real browser state or end-to-end UI evidence rather than source inspection alone.
---

# Browser Workflows

## Choose the path

- For a live site or an already-running app, use the `browser-use` CLI directly.
- For a local app that needs one or more servers, resolve the absolute directory containing this `SKILL.md` file into `SKILL_ROOT`, run `python3 "$SKILL_ROOT/scripts/with_server.py" --help`, then start the servers through that helper before browser interaction.
- For static markup, inspect source first; open it in a browser only when rendering or interaction affects the answer.

If `browser-use` is unavailable or cannot connect, run:

```bash
browser-use --doctor
```

Report the missing runtime instead of substituting unverified assumptions.

## Operate the browser

Use heredocs for multi-step Browser Use sessions:

```bash
browser-use <<'PY'
new_tab("https://example.com")
wait_for_load()
print(page_info())
PY
```

1. Inspect the current page or capture a screenshot before acting.
2. Identify controls from rendered state rather than guessed selectors or coordinates.
3. Perform one logical interaction.
4. Wait for the resulting navigation or state change.
5. Reinspect the page and record evidence.

Prefer semantic or DOM inspection for structured extraction. Use coordinate clicks when visual composition, cross-origin frames, or canvas content makes DOM targeting unreliable.

## Test a local application

Start a single server and a browser script with:

```bash
python3 "$SKILL_ROOT/scripts/with_server.py" \
  --server "npm run dev" --port 5173 \
  -- python3 verify_app.py
```

Keep temporary automation focused on the requested behavior. Capture console errors and a screenshot when they materially explain a failure.

## Boundaries

- Use existing authenticated state only when the intended account and action are unambiguous.
- Stop for passwords, MFA, consent, payment, destructive actions, publishing, or ambiguous account selection.
- Confirm before starting paid remote browser capacity or leaving it running.
- Do not claim success from a click alone; verify the resulting page state, network-visible outcome, or persisted data.

## Finish

State the flow exercised, the observed result, and any browser/runtime limitation. Save screenshots only when they provide useful evidence.
