# Skills Launch

Use this repository as a curated installer index for recommended agent skills.

## Installation Workflow

When asked to install one of the skills from this repository:

1. Read `skills.json` and find the requested skill by `name` or `aliases`.
2. Prefer installing from the upstream GitHub source in the `source` field.
3. If the upstream source is unavailable, install from the local fallback path in `fallback`.
4. Preserve the upstream directory structure when the source is a directory.
5. Check `package_type`. Standard skills use `skill`; Claude plugin-style packages use `claude_plugin`; complete multi-skill suites such as Superpowers use `skill_suite`. Plugins and suites should go into the target agent's plugin or suite directory when supported.
6. Install into the user's requested directory. If none is given, route standard skills through `AGENT_SKILLS_DIR` or the Codex skills directory, and route plugins or suites through `AGENT_PLUGINS_DIR`, `AGENT_SUITES_DIR`, or the Codex plugins directory.

The helper script implements this behavior:

```bash
python3 scripts/skills_launch.py install <skill-name>
```

Use `--target-dir` to choose a destination and `--force` when replacing an existing installed copy is intended.

## CLI-Backed Skills

Some skills are thin discovery stubs for an external command-line tool. After installing `agent-browser`, check whether the CLI is available before trying to use its browser automation workflows:

```bash
agent-browser --version
```

If the command is missing, guide the user to install and initialize the CLI:

```bash
npm i -g agent-browser
agent-browser install
```

Then load the version-matched workflow instructions from the CLI:

```bash
agent-browser skills get core
```

To install every listed entry, use:

```bash
python3 scripts/skills_launch.py install-all
```

For bulk installs, standard skills, Claude plugins, and complete suites can be routed separately with `--skills-dir`, `--plugins-dir`, and `--suites-dir`.

## Skill Suites

`superpowers` is installed as a complete upstream suite rather than as isolated `brainstorming` and `test-driven-development` skills. This preserves its workflow dependencies, platform manifests, and full skill library:

```bash
python3 scripts/skills_launch.py install superpowers
```

Use `--target-dir` for a harness-specific plugin location. During `install-all`, `skill_suite` entries default to the plugin directory and can be overridden with `--suites-dir`.

## Updating Fallback Copies

Repository maintainers can refresh the local fallback copies from upstream:

```bash
python3 scripts/skills_launch.py sync
```

If sync fails for a skill, keep the existing fallback copy and report the upstream URL that failed.

Validate the manifest and fallback copies before finishing changes:

```bash
python3 scripts/skills_launch.py validate
```
