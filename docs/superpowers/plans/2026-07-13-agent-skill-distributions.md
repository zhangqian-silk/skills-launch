# Agent Skill Distributions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert skills-launch into a source library with separate install-ready Claude and Codex distributions, including six lean Codex skills and an offline, agent-aware installer.

**Architecture:** `originals/` is the immutable synchronization target, `distributions/<agent>/skills/` is the only installation source, and `skills.json` maps many upstream sources to each distribution entry. Root agent guidance routes repository maintenance separately from installation; `ADAPTATIONS.md` contains all provenance while installed skills contain runtime material only.

**Tech Stack:** Python 3 standard library, JSON manifest schema v2, `unittest`, Markdown/YAML-frontmatter Skill packages.

## Global Constraints

- Remove the root `SKILL.md`, the old `skills/` tree, the Claude `code-review` plugin, and the complete `suites/superpowers/` tree.
- Preserve complete upstream material under `originals/`; preserve only `test-driven-development` from Superpowers.
- Require `--agent codex` or `--agent claude` for every install command.
- Install only from `distributions/<agent>/skills/`; installation must not access the network or `originals/`.
- Expose exactly six Codex skills: `frontend-design`, `browser-workflows`, `code-quality`, `doc-coauthoring`, `test-driven-development`, and `find-skills`.
- Keep every Codex `SKILL.md` at or below 250 lines with frontmatter containing only `name` and `description`.
- Do not put upstream names, source links, adaptation history, README files, installation guides, quick references, or changelogs in a distribution skill.
- Use strict red-green-refactor for non-trivial behavior and regressions; use direct edits plus targeted checks for documentation, prompts, metadata, simple configuration, and mechanical moves.
- Never silently install Browser Use's Python CLI; report the exact `uv tool install --python 3.12 --upgrade --force browser-use` and `browser-use --doctor` commands when it is missing.

---

## File Map

- `skills.json`: schema v2 source catalog, distribution catalog, aliases, and external command dependencies.
- `scripts/skills_launch.py`: GitHub source synchronization, local distribution installation, path safety, dependency reporting, and validation.
- `AGENTS.md`: concise Codex maintenance/install intent router and verification contract.
- `CLAUDE.md`: concise Claude equivalent of the repository contract.
- `README.md`: human installation and maintenance guide.
- `ADAPTATIONS.md`: the only human-readable source map and adaptation record.
- `originals/*`: unmodified upstream packages; never installed directly.
- `distributions/claude/skills/*`: normalized Claude-installable skills.
- `distributions/codex/skills/*`: six rewritten Codex-installable skills.
- `tests/test_manifest.py`: schema, source layout, distribution mapping, and removed-tree assertions.
- `tests/test_installer.py`: agent routing, aliases, default targets, atomic replacement, dependency reporting, and install-all behavior.
- `tests/test_sync.py`: source lookup, original-only writes, and failure preservation.
- `tests/test_distributions.py`: distribution structure, frontmatter, Codex prompt-quality, reference, and smoke-test checks.

### Task 1: Migrate the source library and manifest schema

**Files:**
- Create: `tests/test_manifest.py`
- Modify: `skills.json`
- Move: `skills/*` to `originals/*`
- Move: `suites/superpowers/skills/test-driven-development/*` to `originals/test-driven-development/*`
- Delete: `SKILL.md`
- Delete: `suites/superpowers/`
- Delete: `tests/test_browser_use_catalog.py`
- Delete: `tests/test_superpowers_suite.py`
- Replace: `tests/test_codex_catalog.py`

**Interfaces:**
- Consumes: current schema v1 entries and local fallback directories.
- Produces: `manifest["sources"]`, `manifest["distributions"][agent]`, and stable `original`/`path` fields consumed by all later tasks.

- [ ] **Step 1: Write the failing schema and migration test**

Replace the existing catalog tests with `tests/test_manifest.py`:

```python
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))

    def test_manifest_uses_sources_and_agent_distributions(self):
        self.assertEqual(self.manifest["version"], 2)
        self.assertEqual(len(self.manifest["sources"]), 11)
        self.assertEqual(set(self.manifest["distributions"]), {"claude", "codex"})

    def test_original_source_names_are_unique_and_present(self):
        names = [source["name"] for source in self.manifest["sources"]]
        self.assertEqual(len(names), len(set(names)))
        for source in self.manifest["sources"]:
            self.assertTrue((ROOT / source["original"]).is_dir(), source["name"])

    def test_codex_catalog_is_lean_and_merged(self):
        entries = {entry["name"]: entry for entry in self.manifest["distributions"]["codex"]}
        self.assertEqual(
            set(entries),
            {
                "frontend-design",
                "browser-workflows",
                "code-quality",
                "doc-coauthoring",
                "test-driven-development",
                "find-skills",
            },
        )
        self.assertEqual(
            entries["frontend-design"]["sources"],
            ["frontend-design", "ui-ux-pro-max", "taste-skill"],
        )
        self.assertEqual(
            entries["browser-workflows"]["sources"],
            ["browser-use", "webapp-testing"],
        )
        self.assertEqual(
            entries["code-quality"]["sources"],
            ["code-reviewer", "code-simplifier"],
        )

    def test_removed_legacy_packages_are_absent(self):
        self.assertFalse((ROOT / "SKILL.md").exists())
        self.assertFalse((ROOT / "skills").exists())
        self.assertFalse((ROOT / "suites" / "superpowers").exists())
        source_names = {source["name"] for source in self.manifest["sources"]}
        self.assertNotIn("code-review", source_names)
        self.assertNotIn("superpowers", source_names)
        self.assertIn("test-driven-development", source_names)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the schema failure**

Run:

```bash
python3 -m unittest tests.test_manifest -v
```

Expected: failure because schema v1 has no `sources`, no agent distributions, and legacy paths still exist.

- [ ] **Step 3: Move originals without rewriting their content**

Run these mechanical moves:

```bash
mkdir -p originals
git mv skills/browser-use originals/browser-use
git mv skills/code-reviewer originals/code-reviewer
git mv skills/code-simplifier originals/code-simplifier
git mv skills/doc-coauthoring originals/doc-coauthoring
git mv skills/find-skills originals/find-skills
git mv skills/frontend-design originals/frontend-design
git mv skills/fullstack-developer originals/fullstack-developer
git mv skills/taste-skill originals/taste-skill
git mv skills/ui-ux-pro-max originals/ui-ux-pro-max
git mv skills/webapp-testing originals/webapp-testing
git mv suites/superpowers/skills/test-driven-development originals/test-driven-development
git rm -r suites/superpowers
git rm SKILL.md
git add -A skills/code-review
```

Delete the three obsolete catalog tests after `tests/test_manifest.py` replaces their assertions.

- [ ] **Step 4: Replace the manifest with schema v2**

Use the following entry shapes for all 11 sources and both distributions:

```json
{
  "version": 2,
  "updated": "2026-07-13",
  "description": "Curated original skills with separate install-ready Claude and Codex distributions.",
  "sources": [
    {"name":"frontend-design","source":{"kind":"github_file","repo":"anthropics/skills","ref":"main","path":"skills/frontend-design/SKILL.md"},"original":"originals/frontend-design"},
    {"name":"doc-coauthoring","source":{"kind":"github_file","repo":"anthropics/skills","ref":"main","path":"skills/doc-coauthoring/SKILL.md"},"original":"originals/doc-coauthoring"},
    {"name":"fullstack-developer","source":{"kind":"github_dir","repo":"Shubhamsaboo/awesome-llm-apps","ref":"main","path":"awesome_agent_skills/fullstack-developer"},"original":"originals/fullstack-developer"},
    {"name":"code-reviewer","source":{"kind":"github_file","repo":"google-gemini/gemini-cli","ref":"main","path":".gemini/skills/code-reviewer/SKILL.md"},"original":"originals/code-reviewer"},
    {"name":"webapp-testing","source":{"kind":"github_dir","repo":"anthropics/skills","ref":"main","path":"skills/webapp-testing"},"original":"originals/webapp-testing"},
    {"name":"browser-use","source":{"kind":"github_dir","repo":"browser-use/browser-use","ref":"main","path":"skills/browser-use"},"original":"originals/browser-use"},
    {"name":"find-skills","source":{"kind":"github_dir","repo":"vercel-labs/skills","ref":"main","path":"skills/find-skills"},"original":"originals/find-skills"},
    {"name":"ui-ux-pro-max","source":{"kind":"github_dir","repo":"nextlevelbuilder/ui-ux-pro-max-skill","ref":"main","path":".claude/skills/ui-ux-pro-max"},"original":"originals/ui-ux-pro-max"},
    {"name":"taste-skill","source":{"kind":"github_dir","repo":"leonxlnx/taste-skill","ref":"main","path":"skills/taste-skill"},"original":"originals/taste-skill"},
    {"name":"code-simplifier","source":{"kind":"github_dir","repo":"anthropics/claude-plugins-official","ref":"main","path":"plugins/code-simplifier"},"original":"originals/code-simplifier"},
    {"name":"test-driven-development","source":{"kind":"github_dir","repo":"obra/superpowers","ref":"main","path":"skills/test-driven-development"},"original":"originals/test-driven-development"}
  ],
  "distributions": {
    "claude": [
      {"name":"frontend-design","sources":["frontend-design"],"path":"distributions/claude/skills/frontend-design"},
      {"name":"doc-coauthoring","sources":["doc-coauthoring"],"path":"distributions/claude/skills/doc-coauthoring"},
      {"name":"fullstack-developer","sources":["fullstack-developer"],"path":"distributions/claude/skills/fullstack-developer"},
      {"name":"code-reviewer","aliases":["gemini-code-reviewer"],"sources":["code-reviewer"],"path":"distributions/claude/skills/code-reviewer"},
      {"name":"webapp-testing","sources":["webapp-testing"],"path":"distributions/claude/skills/webapp-testing"},
      {"name":"browser-use","aliases":["browser-use-official"],"sources":["browser-use"],"path":"distributions/claude/skills/browser-use","dependencies":[{"command":"browser-use","install":"uv tool install --python 3.12 --upgrade --force browser-use","verify":"browser-use --doctor"}]},
      {"name":"find-skills","aliases":["vercel-find-skills","vercel-labs-skills"],"sources":["find-skills"],"path":"distributions/claude/skills/find-skills"},
      {"name":"ui-ux-pro-max","aliases":["ui-ux-pro-max-skill"],"sources":["ui-ux-pro-max"],"path":"distributions/claude/skills/ui-ux-pro-max"},
      {"name":"taste-skill","aliases":["design-taste-frontend","taste"],"sources":["taste-skill"],"path":"distributions/claude/skills/taste-skill"},
      {"name":"code-simplifier","sources":["code-simplifier"],"path":"distributions/claude/skills/code-simplifier"},
      {"name":"test-driven-development","aliases":["tdd"],"sources":["test-driven-development"],"path":"distributions/claude/skills/test-driven-development"}
    ],
    "codex": [
      {"name":"frontend-design","aliases":["ui-ux-pro-max","taste-skill","design-taste-frontend"],"sources":["frontend-design","ui-ux-pro-max","taste-skill"],"path":"distributions/codex/skills/frontend-design"},
      {"name":"browser-workflows","aliases":["browser-use","browser-use-official","webapp-testing"],"sources":["browser-use","webapp-testing"],"path":"distributions/codex/skills/browser-workflows","dependencies":[{"command":"browser-use","install":"uv tool install --python 3.12 --upgrade --force browser-use","verify":"browser-use --doctor"}]},
      {"name":"code-quality","aliases":["code-reviewer","gemini-code-reviewer","code-simplifier"],"sources":["code-reviewer","code-simplifier"],"path":"distributions/codex/skills/code-quality"},
      {"name":"doc-coauthoring","sources":["doc-coauthoring"],"path":"distributions/codex/skills/doc-coauthoring"},
      {"name":"test-driven-development","aliases":["tdd"],"sources":["test-driven-development"],"path":"distributions/codex/skills/test-driven-development"},
      {"name":"find-skills","aliases":["vercel-find-skills","vercel-labs-skills"],"sources":["find-skills"],"path":"distributions/codex/skills/find-skills"}
    ]
  }
}
```

- [ ] **Step 5: Run the migration test**

Run:

```bash
python3 -m unittest tests.test_manifest -v
```

Expected: all four tests pass.

- [ ] **Step 6: Commit the source migration**

```bash
git add -A
git commit -m "refactor: separate original skill sources"
```

### Task 2: Build the normalized Claude distribution

**Files:**
- Create: `distributions/claude/skills/*`
- Create: `tests/test_distributions.py`
- Modify: Claude copies only where a platform-hardcoded path would otherwise break execution.

**Interfaces:**
- Consumes: `manifest["distributions"]["claude"]` and `originals/*`.
- Produces: 11 standard Skill directories directly consumable by the installer.

- [ ] **Step 1: Write the failing Claude distribution test**

Create the first part of `tests/test_distributions.py`:

```python
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_manifest():
    return json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))


class ClaudeDistributionTest(unittest.TestCase):
    def test_every_claude_entry_is_a_standard_skill(self):
        entries = read_manifest()["distributions"]["claude"]
        self.assertEqual(len(entries), 11)
        for entry in entries:
            path = ROOT / entry["path"]
            self.assertTrue((path / "SKILL.md").is_file(), entry["name"])
            self.assertFalse((path / "README.md").exists(), entry["name"])
            self.assertFalse((path / ".claude-plugin").exists(), entry["name"])

    def test_code_simplifier_is_normalized_from_plugin_to_skill(self):
        skill = ROOT / "distributions/claude/skills/code-simplifier/SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertIn("name: code-simplifier", text)
        self.assertNotIn("model: opus", text)

    def test_ui_search_script_runs_from_its_distribution(self):
        script = ROOT / "distributions/claude/skills/ui-ux-pro-max/scripts/search.py"
        completed = subprocess.run(
            [sys.executable, str(script), "fintech dashboard", "--domain", "color", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"domain": "color"', completed.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify missing distribution failures**

Run:

```bash
python3 -m unittest tests.test_distributions.ClaudeDistributionTest -v
```

Expected: failures because `distributions/claude/skills` does not exist.

- [ ] **Step 3: Copy only runtime files into standard Skill folders**

Create each directory from its original. Copy `SKILL.md` for standard single-file skills; include only required `scripts/`, `data/`, `examples/`, and referenced testing material:

```bash
mkdir -p distributions/claude/skills
for name in frontend-design doc-coauthoring fullstack-developer code-reviewer browser-use find-skills taste-skill; do
  mkdir -p "distributions/claude/skills/$name"
  cp "originals/$name/SKILL.md" "distributions/claude/skills/$name/SKILL.md"
done
cp -R originals/webapp-testing distributions/claude/skills/webapp-testing
rm -f distributions/claude/skills/webapp-testing/README.md distributions/claude/skills/webapp-testing/LICENSE.txt
cp -R originals/ui-ux-pro-max distributions/claude/skills/ui-ux-pro-max
rm -f distributions/claude/skills/ui-ux-pro-max/README.md
cp -R originals/test-driven-development distributions/claude/skills/test-driven-development
mkdir -p distributions/claude/skills/code-simplifier
cp originals/code-simplifier/agents/code-simplifier.md distributions/claude/skills/code-simplifier/SKILL.md
```

Normalize `code-simplifier` frontmatter to exactly:

```yaml
---
name: code-simplifier
description: Simplify recently modified code for clarity, consistency, and maintainability while preserving observable behavior. Use when the user asks Claude to simplify, clean up, or refine code without changing functionality.
---
```

Remove the hardcoded `CLAUDE.md` JavaScript conventions from its body and replace that paragraph with: `Read and follow the repository's nearest project instructions before editing.`

- [ ] **Step 4: Run the Claude distribution tests**

Run:

```bash
python3 -m unittest tests.test_distributions.ClaudeDistributionTest -v
```

Expected: all three tests pass.

- [ ] **Step 5: Commit the Claude distribution**

```bash
git add distributions/claude tests/test_distributions.py
git commit -m "feat: add normalized Claude skill distribution"
```

### Task 3: Replace network-first installation with agent-aware local installation

**Files:**
- Create: `tests/test_installer.py`
- Create: `tests/test_sync.py`
- Modify: `scripts/skills_launch.py`

**Interfaces:**
- Produces: `get_source(manifest, name)`, `get_distribution(manifest, agent, name)`, `default_target_dir(agent)`, `copy_directory_atomic(source, destination, force)`, `install_skill(args)`, `install_all(args)`, `sync_upstreams(args)`, and `validate(args)`.
- Consumes: schema v2 `original`, `path`, `aliases`, and `dependencies` fields.

- [ ] **Step 1: Write failing installer routing tests**

Create `tests/test_installer.py` with tests that import the script and patch only its repository manifest/root:

```python
import importlib.util
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("skills_launch", ROOT / "scripts/skills_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()

    def test_distribution_lookup_resolves_alias_within_agent(self):
        manifest = {
            "distributions": {
                "codex": [{"name": "browser-workflows", "aliases": ["browser-use"]}],
                "claude": [{"name": "browser-use"}],
            }
        }
        self.assertEqual(
            self.installer.get_distribution(manifest, "codex", "browser-use")["name"],
            "browser-workflows",
        )
        self.assertEqual(
            self.installer.get_distribution(manifest, "claude", "browser-use")["name"],
            "browser-use",
        )

    def test_default_targets_are_agent_specific(self):
        with mock.patch.dict(os.environ, {"CODEX_HOME": "/tmp/codex"}, clear=True):
            self.assertEqual(self.installer.default_target_dir("codex"), Path("/tmp/codex/skills"))
        with mock.patch.dict(os.environ, {"CLAUDE_HOME": "/tmp/claude"}, clear=True):
            self.assertEqual(self.installer.default_target_dir("claude"), Path("/tmp/claude/skills"))

    def test_install_copies_distribution_without_downloading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "distributions/codex/skills/sample"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("skill", encoding="utf-8")
            target = root / "target"
            manifest = {
                "distributions": {
                    "codex": [{"name": "sample", "path": "distributions/codex/skills/sample"}]
                }
            }
            args = Namespace(name="sample", agent="codex", target_dir=str(target), force=False)
            with mock.patch.object(self.installer, "REPOSITORY_ROOT", root), mock.patch.object(
                self.installer, "load_manifest", return_value=manifest
            ), mock.patch.object(self.installer, "save_github_source") as download:
                self.installer.install_skill(args)
            download.assert_not_called()
            self.assertEqual((target / "sample/SKILL.md").read_text(encoding="utf-8"), "skill")

    def test_failed_forced_copy_preserves_existing_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            destination = root / "target/sample"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("old", encoding="utf-8")
            with mock.patch("shutil.copytree", side_effect=OSError("copy failed")):
                with self.assertRaises(OSError):
                    self.installer.copy_directory_atomic(source, destination, force=True)
            self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "old")

    def test_missing_dependency_prints_install_and_verify_commands(self):
        entry = {
            "name": "browser-workflows",
            "dependencies": [{
                "command": "browser-use",
                "install": "uv tool install --python 3.12 --upgrade --force browser-use",
                "verify": "browser-use --doctor",
            }],
        }
        with mock.patch("shutil.which", return_value=None), mock.patch("builtins.print") as output:
            self.installer.report_dependencies(entry)
        rendered = "\n".join(str(call) for call in output.call_args_list)
        self.assertIn("uv tool install --python 3.12 --upgrade --force browser-use", rendered)
        self.assertIn("browser-use --doctor", rendered)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write failing sync isolation tests**

Create `tests/test_sync.py`:

```python
import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("skills_launch_sync", ROOT / "scripts/skills_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncTest(unittest.TestCase):
    def test_sync_replaces_only_original_after_successful_download(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            distribution = root / "distributions/codex/skills/sample"
            original.mkdir(parents=True)
            distribution.mkdir(parents=True)
            (original / "SKILL.md").write_text("old", encoding="utf-8")
            (distribution / "SKILL.md").write_text("optimized", encoding="utf-8")
            manifest = {
                "sources": [{
                    "name": "sample",
                    "source": {"kind": "github_file", "repo": "o/r", "ref": "main", "path": "SKILL.md"},
                    "original": "originals/sample",
                }]
            }

            def download(_source, destination):
                destination.mkdir(parents=True, exist_ok=True)
                (destination / "SKILL.md").write_text("new", encoding="utf-8")

            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source", side_effect=download):
                installer.sync_upstreams(Namespace(names=["sample"]))

            self.assertEqual((original / "SKILL.md").read_text(encoding="utf-8"), "new")
            self.assertEqual((distribution / "SKILL.md").read_text(encoding="utf-8"), "optimized")

    def test_failed_sync_preserves_existing_original(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            original.mkdir(parents=True)
            (original / "SKILL.md").write_text("old", encoding="utf-8")
            manifest = {"sources": [{"name": "sample", "source": {"repo": "o/r", "path": "x"}, "original": "originals/sample"}]}
            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source", side_effect=installer.SkillLaunchError("offline")):
                with self.assertRaises(installer.SkillLaunchError):
                    installer.sync_upstreams(Namespace(names=["sample"]))
            self.assertEqual((original / "SKILL.md").read_text(encoding="utf-8"), "old")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the focused tests and verify missing interfaces**

Run:

```bash
python3 -m unittest tests.test_installer tests.test_sync -v
```

Expected: failures for missing `get_distribution`, agent-aware targets, atomic copy, and schema v2 sync.

- [ ] **Step 4: Implement schema v2 lookup and safe local install**

Implement these exact contracts in `scripts/skills_launch.py`:

```python
SUPPORTED_AGENTS = ("claude", "codex")


def get_source(manifest, name):
    for source in manifest["sources"]:
        if source["name"] == name:
            return source
    available = ", ".join(source["name"] for source in manifest["sources"])
    raise SkillLaunchError(f"Unknown source '{name}'. Available sources: {available}")


def get_distribution(manifest, agent, name):
    if agent not in SUPPORTED_AGENTS:
        raise SkillLaunchError(f"Unsupported agent '{agent}'. Choose: {', '.join(SUPPORTED_AGENTS)}")
    entries = manifest["distributions"][agent]
    for entry in entries:
        if entry["name"] == name or name in entry.get("aliases", []):
            return entry
    available = ", ".join(entry["name"] for entry in entries)
    raise SkillLaunchError(f"Unknown {agent} skill '{name}'. Available skills: {available}")


def repository_path(relative):
    path = (REPOSITORY_ROOT / relative).resolve()
    root = REPOSITORY_ROOT.resolve()
    if path != root and root not in path.parents:
        raise SkillLaunchError(f"Repository path escapes the repository: {relative}")
    return path


def default_target_dir(agent):
    if os.environ.get("AGENT_SKILLS_DIR"):
        return Path(os.environ["AGENT_SKILLS_DIR"])
    if agent == "codex":
        if os.environ.get("CODEX_HOME"):
            return Path(os.environ["CODEX_HOME"]) / "skills"
        return Path.home() / ".agents" / "skills"
    if os.environ.get("CLAUDE_HOME"):
        return Path(os.environ["CLAUDE_HOME"]) / "skills"
    return Path.home() / ".claude" / "skills"


def copy_directory_atomic(source, destination, force=False):
    source = Path(source)
    destination = Path(destination)
    if not source.is_dir():
        raise SkillLaunchError(f"Cannot find distribution directory: {source}")
    if destination.exists() and not force:
        raise SkillLaunchError(f"Target already exists: {destination}. Re-run with --force to replace it.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}-", dir=destination.parent) as temp_dir:
        staged = Path(temp_dir) / "payload"
        shutil.copytree(source, staged)
        backup = Path(temp_dir) / "previous"
        had_previous = destination.exists()
        try:
            if had_previous:
                destination.rename(backup)
            staged.rename(destination)
        except Exception:
            if had_previous and backup.exists() and not destination.exists():
                backup.rename(destination)
            raise


def report_dependencies(entry):
    for dependency in entry.get("dependencies", []):
        if shutil.which(dependency["command"]):
            continue
        print(f"Warning: '{entry['name']}' requires missing command '{dependency['command']}'.", file=sys.stderr)
        print(f"Install: {dependency['install']}", file=sys.stderr)
        print(f"Verify: {dependency['verify']}", file=sys.stderr)
```

`install_skill` must resolve only `entry["path"]`, call `copy_directory_atomic`, then call `report_dependencies`. Remove `--use-fallback-only`, package-type routing, upstream download attempts, and plugin/suite destinations from installation.

`install-all` must iterate only `manifest["distributions"][args.agent]` and reuse `install_skill` with the selected target directory.

`sync_upstreams` must use `get_source`, download to a temporary directory, verify that the download is non-empty, and atomically replace only `source["original"]`.

- [ ] **Step 5: Update the parser**

Use these parser contracts:

```python
install_parser.add_argument("name")
install_parser.add_argument("--agent", choices=SUPPORTED_AGENTS, required=True)
install_parser.add_argument("--target-dir")
install_parser.add_argument("--force", action="store_true")

install_all_parser.add_argument("--agent", choices=SUPPORTED_AGENTS, required=True)
install_all_parser.add_argument("--target-dir")
install_all_parser.add_argument("--force", action="store_true")

sync_parser.add_argument("names", nargs="*")
```

- [ ] **Step 6: Run focused and full tests**

Run:

```bash
python3 -m unittest tests.test_installer tests.test_sync -v
python3 -m unittest discover -s tests -v
```

Expected: installer/sync tests and every test created through Task 3 pass; no schema v1 assertion remains.

- [ ] **Step 7: Commit the installer and sync behavior**

```bash
git add scripts/skills_launch.py tests/test_installer.py tests/test_sync.py
git commit -m "feat: install agent-specific local distributions"
```

### Task 4: Create the merged Codex frontend-design skill

**Files:**
- Create: `distributions/codex/skills/frontend-design/SKILL.md`
- Create: `distributions/codex/skills/frontend-design/scripts/{search.py,core.py,design_system.py}`
- Create: `distributions/codex/skills/frontend-design/data/*.csv`
- Extend: `tests/test_distributions.py`

**Interfaces:**
- Consumes: the visual direction rules, design datasets, and search implementation from the three mapped originals.
- Produces: one Codex trigger for frontend design, UI/UX review, and design-system lookup.

- [ ] **Step 1: Add failing Codex structure and prompt-quality tests**

Append this class to `tests/test_distributions.py`:

```python
class CodexDistributionTest(unittest.TestCase):
    FORBIDDEN_TEXT = (
        "Claude.ai",
        "model: opus",
        "create_file",
        "str_replace",
        ".claude/",
        "github.com",
        "Adapted from",
        "ADAPTATIONS.md",
        "originals/",
    )

    def assertLeanCodexSkill(self, name):
        path = ROOT / "distributions/codex/skills" / name
        skill = path / "SKILL.md"
        text = skill.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 250)
        self.assertTrue(text.startswith("---\nname: "))
        closing = text.find("\n---\n", 4)
        frontmatter = text[4:closing].splitlines()
        keys = [line.split(":", 1)[0] for line in frontmatter if ":" in line]
        self.assertEqual(keys, ["name", "description"])
        self.assertIn(f"name: {name}", text[:closing])
        for forbidden in self.FORBIDDEN_TEXT:
            self.assertNotIn(forbidden, text)
        for filename in ("README.md", "CHANGELOG.md", "ADAPTATION.md", "source-context.md"):
            self.assertFalse((path / filename).exists())

    def test_frontend_design_is_lean_and_searchable(self):
        self.assertLeanCodexSkill("frontend-design")
        script = ROOT / "distributions/codex/skills/frontend-design/scripts/search.py"
        completed = subprocess.run(
            [sys.executable, str(script), "healthcare dashboard", "--domain", "ux", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"domain": "ux"', completed.stdout)
```

- [ ] **Step 2: Run the focused test and verify the missing-skill failure**

```bash
python3 -m unittest tests.test_distributions.CodexDistributionTest.test_frontend_design_is_lean_and_searchable -v
```

Expected: failure because the Codex `frontend-design` distribution does not exist.

- [ ] **Step 3: Write the lean frontend workflow**

Create `distributions/codex/skills/frontend-design/SKILL.md` with this complete body:

```markdown
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

Run the bundled search from this skill directory when choosing an unfamiliar product pattern, palette, chart, font pairing, UX rule, or framework-specific convention:

```bash
python3 scripts/search.py "<product and task>" --domain <style|color|chart|landing|product|ux|typography|icons|web>
python3 scripts/search.py "<implementation question>" --stack <react|nextjs|vue|svelte|swiftui|flutter|shadcn|html-tailwind>
```

Treat search output as candidates, not mandatory decisions. Do not run it when the repository already supplies the relevant design system.

## Verify

- Run the repository's relevant formatter, type checker, tests, and build.
- Inspect the rendered result at representative narrow and wide sizes when browser tooling is available.
- Check the primary task without a mouse.
- Confirm text contrast, focus visibility, content overflow, and touch target usability.
- Remove visual elements that do not improve hierarchy, comprehension, or brand character.

Finish with a concise summary of the implemented direction and the checks actually run.
```

- [ ] **Step 4: Add the deterministic design search resources**

Copy the three search scripts and CSV data from the design-data original. Remove `data/_sync_all.py`, because upstream synchronization belongs to this repository rather than the installed Skill. In `scripts/search.py`, change `Format results for Claude consumption` to `Format compact search results`. Keep all data paths relative to the script's parent so installation location does not matter.

```bash
mkdir -p distributions/codex/skills/frontend-design/scripts distributions/codex/skills/frontend-design/data
cp originals/ui-ux-pro-max/scripts/search.py distributions/codex/skills/frontend-design/scripts/search.py
cp originals/ui-ux-pro-max/scripts/core.py distributions/codex/skills/frontend-design/scripts/core.py
cp originals/ui-ux-pro-max/scripts/design_system.py distributions/codex/skills/frontend-design/scripts/design_system.py
cp -R originals/ui-ux-pro-max/data/. distributions/codex/skills/frontend-design/data/
rm -f distributions/codex/skills/frontend-design/data/_sync_all.py
```

- [ ] **Step 5: Run the Skill and smoke tests**

```bash
python3 -m unittest tests.test_distributions.CodexDistributionTest.test_frontend_design_is_lean_and_searchable -v
python3 distributions/codex/skills/frontend-design/scripts/search.py "fintech dashboard" --domain color --json
```

Expected: the unit test passes and the command emits JSON with `"domain": "color"`.

- [ ] **Step 6: Commit the frontend distribution**

```bash
git add distributions/codex/skills/frontend-design tests/test_distributions.py
git commit -m "feat: merge Codex frontend design guidance"
```

### Task 5: Create Codex browser-workflows and code-quality skills

**Files:**
- Create: `distributions/codex/skills/browser-workflows/SKILL.md`
- Create: `distributions/codex/skills/browser-workflows/scripts/with_server.py`
- Create: `distributions/codex/skills/code-quality/SKILL.md`
- Extend: `tests/test_distributions.py`

**Interfaces:**
- Produces: one browser automation/testing trigger and one review/simplification trigger.
- Consumes: Browser Use CLI from the environment and the bundled local-server helper.

- [ ] **Step 1: Add failing tests for both merged skills**

Append to `CodexDistributionTest`:

```python
    def test_browser_and_code_quality_skills_are_lean(self):
        self.assertLeanCodexSkill("browser-workflows")
        self.assertLeanCodexSkill("code-quality")
        browser = (ROOT / "distributions/codex/skills/browser-workflows/SKILL.md").read_text(encoding="utf-8")
        quality = (ROOT / "distributions/codex/skills/code-quality/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("browser-use --doctor", browser)
        self.assertIn("Review mode", quality)
        self.assertIn("Simplify mode", quality)
        self.assertNotIn("npm run preflight", quality)
```

- [ ] **Step 2: Run the test and verify both missing paths**

```bash
python3 -m unittest tests.test_distributions.CodexDistributionTest.test_browser_and_code_quality_skills_are_lean -v
```

Expected: failure on the missing `browser-workflows/SKILL.md`.

- [ ] **Step 3: Write browser-workflows**

Create `distributions/codex/skills/browser-workflows/SKILL.md`:

```markdown
---
name: browser-workflows
description: Operate a browser and verify web applications through Browser Use, including navigation, interaction, screenshots, extraction, console inspection, and local-server testing. Use when a task requires real browser state or end-to-end UI evidence rather than source inspection alone.
---

# Browser Workflows

## Choose the path

- For a live site or an already-running app, use the `browser-use` CLI directly.
- For a local app that needs one or more servers, run `python3 scripts/with_server.py --help`, then start the servers through that helper before browser interaction.
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
python3 scripts/with_server.py \
  --server "npm run dev" --port 5173 \
  -- python3 /tmp/verify_app.py
```

Keep temporary automation focused on the requested behavior. Capture console errors and a screenshot when they materially explain a failure.

## Boundaries

- Use existing authenticated state only when the intended account and action are unambiguous.
- Stop for passwords, MFA, consent, payment, destructive actions, publishing, or ambiguous account selection.
- Confirm before starting paid remote browser capacity or leaving it running.
- Do not claim success from a click alone; verify the resulting page state, network-visible outcome, or persisted data.

## Finish

State the flow exercised, the observed result, and any browser/runtime limitation. Save screenshots only when they provide useful evidence.
```

Copy `originals/webapp-testing/scripts/with_server.py` into the distribution unchanged and verify `python3 .../with_server.py --help` exits successfully.

- [ ] **Step 4: Write code-quality**

Create `distributions/codex/skills/code-quality/SKILL.md`:

```markdown
---
name: code-quality
description: Review code for actionable defects or simplify recently changed code without altering behavior. Use for local diffs, pull requests, regression-focused review, maintainability review, cleanup, or explicit simplification requests.
---

# Code Quality

Choose one mode from the user's intent. Do not silently turn a review into an edit or a simplification into a broad rewrite.

## Review mode

1. Determine the target: a PR, commit range, staged changes, working tree, or named files.
2. Read repository guidance and the change's stated purpose.
3. Inspect the diff before opening surrounding code needed to validate assumptions.
4. Run the smallest relevant existing checks when they are safe and useful.
5. Report only findings that are concrete, introduced by the change, and worth the author's attention.

Prioritize correctness, security, data loss, broken contracts, concurrency, error paths, and missing regression coverage. Treat style preferences as findings only when they violate an established project rule or create a real maintenance hazard.

For each finding provide:

- severity and concise title;
- exact file and line;
- the failing scenario or affected behavior;
- why the current code causes it;
- a bounded correction direction.

Lead with findings ordered by severity. If none meet the bar, say so and mention any meaningful verification gap. Do not add praise, summaries, or speculative concerns that obscure the result.

## Simplify mode

1. Limit scope to recently modified code unless the user names a broader target.
2. Read nearby code and project conventions before editing.
3. Identify unnecessary nesting, duplication, indirection, clever expressions, stale comments, and names that hide intent.
4. Preserve public interfaces, outputs, side effects, error behavior, performance characteristics that callers rely on, and test semantics.
5. Make the smallest coherent cleanup and run relevant checks.

Prefer explicit control flow and established abstractions. Do not collapse distinct responsibilities, remove useful boundaries, or optimize for fewer lines. If simplification would change observable behavior, stop and present it as a separate proposed change.

## Boundaries

- Review mode is read-only unless the user asks for fixes.
- Do not check out a PR, post a review, resolve comments, or publish changes without authorization for that external action.
- Use repository-defined validation commands; do not assume a language, package manager, or preflight script.
- Keep unrelated pre-existing issues outside the result unless they block evaluation of the requested change.

Finish with the checks actually run and any remaining uncertainty.
```

- [ ] **Step 5: Run focused tests and the server-helper smoke test**

```bash
python3 -m unittest tests.test_distributions.CodexDistributionTest.test_browser_and_code_quality_skills_are_lean -v
python3 distributions/codex/skills/browser-workflows/scripts/with_server.py --help
```

Expected: unit test passes and helper prints usage with exit code 0.

- [ ] **Step 6: Commit both merged skills**

```bash
git add distributions/codex/skills/browser-workflows distributions/codex/skills/code-quality tests/test_distributions.py
git commit -m "feat: add Codex browser and code quality workflows"
```

### Task 6: Create the remaining three Codex skills

**Files:**
- Create: `distributions/codex/skills/doc-coauthoring/SKILL.md`
- Create: `distributions/codex/skills/test-driven-development/SKILL.md`
- Create: `distributions/codex/skills/find-skills/SKILL.md`
- Extend: `tests/test_distributions.py`

**Interfaces:**
- Produces: the final six-entry Codex distribution.
- Consumes: only runtime capabilities; no source or adaptation context is copied into these directories.

- [ ] **Step 1: Add failing final-catalog and TDD fast-path tests**

Append to `CodexDistributionTest`:

```python
    def test_exactly_six_codex_skills_are_installable(self):
        entries = read_manifest()["distributions"]["codex"]
        expected = {entry["name"] for entry in entries}
        actual = {path.name for path in (ROOT / "distributions/codex/skills").iterdir() if path.is_dir()}
        self.assertEqual(actual, expected)
        for name in expected:
            self.assertLeanCodexSkill(name)

    def test_tdd_skill_has_a_low_risk_fast_path(self):
        text = (ROOT / "distributions/codex/skills/test-driven-development/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Fast path", text)
        self.assertIn("Strict TDD", text)
        self.assertIn("low-risk", text)
        self.assertNotIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", text)
```

- [ ] **Step 2: Run tests and verify three missing skills**

```bash
python3 -m unittest \
  tests.test_distributions.CodexDistributionTest.test_exactly_six_codex_skills_are_installable \
  tests.test_distributions.CodexDistributionTest.test_tdd_skill_has_a_low_risk_fast_path -v
```

Expected: failures because only three Codex Skill directories exist.

- [ ] **Step 3: Write doc-coauthoring**

Create `distributions/codex/skills/doc-coauthoring/SKILL.md`:

```markdown
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
```

- [ ] **Step 4: Write risk-based test-driven-development**

Create `distributions/codex/skills/test-driven-development/SKILL.md`:

```markdown
---
name: test-driven-development
description: Apply risk-based testing while implementing features, bug fixes, refactors, and small repository changes. Use strict red-green-refactor for non-trivial or regression-prone behavior; use direct implementation plus targeted verification for small, low-risk changes where a new test would add little value.
---

# Risk-Based Test-Driven Development

Choose the lightest process that provides credible evidence.

## Use Strict TDD

Use red-green-refactor for:

- new or changed observable behavior;
- a reproducible bug or regression;
- non-trivial branching, state, parsing, retries, concurrency, or error handling;
- public interfaces, persistence, migrations, security boundaries, or high-risk refactors;
- changes where a future regression would be costly or hard to detect.

Cycle one behavior at a time:

1. Write the smallest test that expresses the required behavior.
2. Run it and confirm it fails for the missing behavior, not a setup mistake.
3. Implement only enough production code to pass.
4. Run the focused test and relevant regression suite.
5. Refactor only while tests remain green.

Prefer real behavior over mock assertions. Mock only external or slow boundaries after understanding the real dependency and preserve any side effects the test relies on.

## Use the Fast path

Implement directly when the change is small and low-risk, such as:

- documentation, comments, prompts, labels, or metadata;
- a simple configuration value with an existing validation path;
- formatting, renaming, file movement, or another mechanical transformation;
- an obvious local correction where a new test would duplicate stronger existing checks.

Before using the fast path, confirm the change does not alter a public contract, branch behavior, state transition, error path, or security boundary. Make the edit, run the narrowest relevant formatter, parser, build, smoke check, or existing test, and report that evidence.

Do not create ceremonial tests that merely restate text, constants, mocks, or implementation details.

## Escalate when risk grows

Switch from the fast path to Strict TDD if the edit expands in scope, reveals hidden behavior, lacks a reliable existing check, or produces a regression. If the project cannot support an automated test, explain the limitation and use a reproducible manual verification.

Finish with the test or validation commands actually run.
```

- [ ] **Step 5: Write find-skills**

Create `distributions/codex/skills/find-skills/SKILL.md`:

```markdown
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
```

- [ ] **Step 6: Run all distribution tests**

```bash
python3 -m unittest tests.test_distributions -v
```

Expected: Claude and all six Codex distribution tests pass.

- [ ] **Step 7: Commit the final Codex Skill set**

```bash
git add distributions/codex/skills tests/test_distributions.py
git commit -m "feat: complete lean Codex skill distribution"
```

### Task 7: Enforce validation and document both repository modes

**Files:**
- Modify: `scripts/skills_launch.py`
- Create: `tests/test_validation.py`
- Create: `tests/test_repository_docs.py`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `ADAPTATIONS.md`
- Rewrite: `README.md`

**Interfaces:**
- Produces: `validate_manifest(manifest, root) -> list[str]` and a non-zero `validate` CLI result for any invalid source/distribution.
- Produces: always-read agent routing in `AGENTS.md`/`CLAUDE.md`; all provenance in `ADAPTATIONS.md`; user commands in README.

- [ ] **Step 1: Write failing validation tests**

Create `tests/test_validation.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("skills_launch_validation", ROOT / "scripts/skills_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidationTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()
        self.manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))

    def test_repository_manifest_and_distributions_validate(self):
        self.assertEqual(self.installer.validate_manifest(self.manifest, ROOT), [])

    def test_unknown_source_mapping_is_rejected(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["distributions"]["codex"][0]["sources"] = ["missing-source"]
        errors = self.installer.validate_manifest(manifest, ROOT)
        self.assertTrue(any("unknown source" in error for error in errors), errors)

    def test_repository_path_escape_is_rejected(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["sources"][0]["original"] = "../outside"
        errors = self.installer.validate_manifest(manifest, ROOT)
        self.assertTrue(any("escapes repository" in error for error in errors), errors)

    def test_codex_provenance_text_is_rejected(self):
        manifest = {
            "version": 2,
            "sources": [],
            "distributions": {"claude": [], "codex": [{
                "name": "sample", "sources": [], "path": "dist/sample"
            }]},
        }
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "dist/sample"
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(
                "---\nname: sample\ndescription: Use for sample tasks.\n---\n\nAdapted from upstream.\n",
                encoding="utf-8",
            )
            errors = self.installer.validate_manifest(manifest, root)
        self.assertTrue(any("forbidden text" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run validation tests and verify the missing validator**

```bash
python3 -m unittest tests.test_validation -v
```

Expected: failure because `validate_manifest` is not implemented.

- [ ] **Step 3: Implement manifest and distribution validation**

Add these constants and helpers to `scripts/skills_launch.py`:

```python
CODEX_FORBIDDEN_TEXT = (
    "Claude.ai",
    "model: opus",
    "create_file",
    "str_replace",
    ".claude/",
    "github.com",
    "Adapted from",
    "ADAPTATIONS.md",
    "originals/",
)
FORBIDDEN_DISTRIBUTION_FILES = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
    "ADAPTATION.md",
    "source-context.md",
}


def frontmatter_keys(text):
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---\n", 4)
    if end < 0:
        return []
    return [
        line.split(":", 1)[0].strip()
        for line in text[4:end].splitlines()
        if ":" in line and not line.startswith((" ", "\t"))
    ]


def resolve_within(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise SkillLaunchError(f"path escapes repository: {relative}")
    return path


def validate_manifest(manifest, root=REPOSITORY_ROOT):
    errors = []
    if manifest.get("version") != 2:
        errors.append("manifest version must be 2")
    sources = manifest.get("sources", [])
    source_names = [source.get("name") for source in sources]
    if len(source_names) != len(set(source_names)):
        errors.append("source names must be unique")
    source_set = set(source_names)
    for source in sources:
        for field in ("name", "source", "original"):
            if not source.get(field):
                errors.append(f"source is missing {field}: {source.get('name', '<unknown>')}")
        source_spec = source.get("source", {})
        for field in ("kind", "repo", "ref", "path"):
            if field not in source_spec:
                errors.append(f"{source.get('name', '<unknown>')} source is missing {field}")
        if source_spec.get("kind") not in {"github_file", "github_dir"}:
            errors.append(f"unsupported source kind: {source_spec.get('kind')}")
        try:
            original = resolve_within(root, source.get("original", ""))
        except SkillLaunchError as error:
            errors.append(str(error))
            continue
        if not original.is_dir():
            errors.append(f"missing original directory: {source.get('original')}")

    distributions = manifest.get("distributions", {})
    if set(distributions) != set(SUPPORTED_AGENTS):
        errors.append("distributions must contain exactly claude and codex")
    for agent in SUPPORTED_AGENTS:
        entries = distributions.get(agent, [])
        names = [entry.get("name") for entry in entries]
        if len(names) != len(set(names)):
            errors.append(f"{agent} distribution names must be unique")
        aliases = [alias for entry in entries for alias in entry.get("aliases", [])]
        if set(names) & set(aliases) or len(aliases) != len(set(aliases)):
            errors.append(f"{agent} aliases must be unique and not shadow names")
        for entry in entries:
            name = entry.get("name", "<unknown>")
            unknown = set(entry.get("sources", [])) - source_set
            if unknown:
                errors.append(f"{agent}/{name} references unknown source: {', '.join(sorted(unknown))}")
            try:
                path = resolve_within(root, entry.get("path", ""))
            except SkillLaunchError as error:
                errors.append(str(error))
                continue
            if not path.is_dir() or not (path / "SKILL.md").is_file():
                errors.append(f"missing distribution skill: {agent}/{name}")
                continue
            if path.name != name:
                errors.append(f"{agent}/{name} directory name must match skill name")
            for dependency in entry.get("dependencies", []):
                missing = {"command", "install", "verify"} - set(dependency)
                if missing:
                    errors.append(f"{agent}/{name} dependency is missing: {', '.join(sorted(missing))}")
            for forbidden_file in FORBIDDEN_DISTRIBUTION_FILES:
                if (path / forbidden_file).exists():
                    errors.append(f"{agent}/{name} contains forbidden file: {forbidden_file}")
            text = (path / "SKILL.md").read_text(encoding="utf-8")
            if agent == "codex":
                if frontmatter_keys(text) != ["name", "description"]:
                    errors.append(f"{agent}/{name} frontmatter must contain only name and description")
                if len(text.splitlines()) > 250:
                    errors.append(f"{agent}/{name} SKILL.md exceeds 250 lines")
                for forbidden in CODEX_FORBIDDEN_TEXT:
                    if forbidden in text:
                        errors.append(f"{agent}/{name} contains forbidden text: {forbidden}")
            references = path / "references"
            if references.is_dir():
                if any(child.is_dir() for child in references.iterdir()):
                    errors.append(f"{agent}/{name} references must be one level deep")
                for reference in references.iterdir():
                    if reference.is_file() and reference.name not in text:
                        errors.append(f"{agent}/{name} does not link reference: {reference.name}")
    return errors
```

Make `validate(args)` call `validate_manifest(load_manifest(), REPOSITORY_ROOT)`, print each error to stderr, return 1 when any exist, and print counts of sources plus Claude/Codex distribution entries on success.

- [ ] **Step 4: Run validation tests and repository validation**

```bash
python3 -m unittest tests.test_validation -v
python3 scripts/skills_launch.py validate
```

Expected: four tests pass and CLI reports 11 sources, 11 Claude skills, and 6 Codex skills.

- [ ] **Step 5: Write failing repository-routing documentation tests**

Create `tests/test_repository_docs.py`:

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryDocsTest(unittest.TestCase):
    def test_agents_routes_maintenance_and_installation(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Maintenance mode", text)
        self.assertIn("Installation mode", text)
        self.assertIn("ADAPTATIONS.md", text)
        self.assertIn("--agent codex", text)

    def test_adaptations_centralizes_sources_and_codex_changes(self):
        text = (ROOT / "ADAPTATIONS.md").read_text(encoding="utf-8")
        self.assertIn("2026-07-13", text)
        self.assertIn("migration-quickstart", text)
        self.assertIn("frontend-design + ui-ux-pro-max + taste-skill", text)
        self.assertIn("browser-use + webapp-testing", text)
        self.assertIn("code-reviewer + code-simplifier", text)

    def test_readme_documents_agent_specific_install_and_browser_dependency(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("install frontend-design --agent codex", text)
        self.assertIn("install-all --agent claude", text)
        self.assertIn("uv tool install --python 3.12 --upgrade --force browser-use", text)
        self.assertIn("browser-use --doctor", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 6: Run the docs tests and verify missing files/stale README**

```bash
python3 -m unittest tests.test_repository_docs -v
```

Expected: failures because `AGENTS.md` and `ADAPTATIONS.md` do not exist and README still describes network-first installation.

- [ ] **Step 7: Create concise repository routing files**

Create `AGENTS.md` with this complete contract:

```markdown
# Repository Instructions

This repository maintains original Skill sources and separate install-ready Claude and Codex distributions.

## Intent routing

- **Maintenance mode:** For requests to sync, add, remove, merge, adapt, or validate skills, read `ADAPTATIONS.md`, `skills.json`, the relevant `originals/` directories, and the affected distributions before editing.
- **Installation mode:** For requests to install skills, do not modify the repository. Read `skills.json` and install only from the requested `distributions/<agent>/skills/` entry.
- If the request does not identify maintenance versus installation or does not identify the target agent, ask before changing files or installing anything.

## Hard boundaries

- Treat `originals/` as upstream material. Only `python3 scripts/skills_launch.py sync` may replace it.
- Never install from `originals/` or fetch upstream content during installation.
- Keep all provenance and adaptation history in `ADAPTATIONS.md`, never inside distribution skills.
- Codex distributions may merge or omit originals when that produces a smaller, clearer workflow.
- Use `python3 scripts/skills_launch.py install <name> --agent codex` for Codex installation.

## Verification

Run before completing repository changes:

```bash
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```
```

Create `CLAUDE.md` with this complete contract:

```markdown
# Repository Instructions

This file is Claude's repository entry for maintaining and installing the checked-in Skill distributions.

## Intent routing

- **Maintenance mode:** For requests to sync, add, remove, merge, adapt, or validate skills, read `ADAPTATIONS.md`, `skills.json`, the relevant `originals/` directories, and the affected distributions before editing.
- **Installation mode:** For requests to install skills, do not modify the repository. Read `skills.json` and install only from the requested `distributions/<agent>/skills/` entry.
- If the request does not identify maintenance versus installation or does not identify the target agent, ask before changing files or installing anything.

## Hard boundaries

- Treat `originals/` as upstream material. Only `python3 scripts/skills_launch.py sync` may replace it.
- Never install from `originals/` or fetch upstream content during installation.
- Keep all provenance and adaptation history in `ADAPTATIONS.md`, never inside distribution skills.
- Preserve Claude-specific workflows only in the Claude distribution; do not copy them into Codex packages without applying the Codex adaptation rules.
- Use `python3 scripts/skills_launch.py install <name> --agent claude` for Claude installation.

## Verification

Run before completing repository changes:

```bash
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```
```

- [ ] **Step 8: Write the centralized adaptation record and README**

`ADAPTATIONS.md` must contain these concrete sections and mappings:

```markdown
# Skill Adaptations

## References

- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#migration-quickstart
- Read 2026-07-13: https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices
- Read 2026-07-13: https://developers.openai.com/codex/concepts/customization

## Distribution policy

Originals preserve complete upstream context. Claude distributions normalize packages into directly installable standard skills. Codex distributions state each instruction once, retain only non-obvious procedural knowledge, use progressive disclosure for runtime references, define autonomy and verification boundaries, and never hardcode a model or reasoning effort.

## Original catalog

| Original | Source |
| --- | --- |
| `frontend-design` | https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md |
| `doc-coauthoring` | https://github.com/anthropics/skills/blob/main/skills/doc-coauthoring/SKILL.md |
| `fullstack-developer` | https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/awesome_agent_skills/fullstack-developer |
| `code-reviewer` | https://github.com/google-gemini/gemini-cli/blob/main/.gemini/skills/code-reviewer/SKILL.md |
| `webapp-testing` | https://github.com/anthropics/skills/tree/main/skills/webapp-testing |
| `browser-use` | https://github.com/browser-use/browser-use/tree/main/skills/browser-use |
| `find-skills` | https://github.com/vercel-labs/skills/tree/main/skills/find-skills |
| `ui-ux-pro-max` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/tree/main/.claude/skills/ui-ux-pro-max |
| `taste-skill` | https://github.com/leonxlnx/taste-skill/tree/main/skills/taste-skill |
| `code-simplifier` | https://github.com/anthropics/claude-plugins-official/tree/main/plugins/code-simplifier |
| `test-driven-development` | https://github.com/obra/superpowers/tree/main/skills/test-driven-development |

The complete Superpowers suite and the Claude `code-review` plugin were intentionally removed. TDD remains as an ordinary source and distribution skill.

## Claude map

Claude keeps one standard Skill for every original. Standard upstream Skill folders retain their workflows and functional resources. `code-simplifier` is normalized from a plugin agent prompt into `SKILL.md`, drops the pinned model and fixed project conventions, and follows the target repository's instructions. Claude TDD retains the original strict bias. No Claude distribution includes source-history documentation.

## Codex map

| Codex distribution | Original inputs | Adaptation |
| --- | --- | --- |
| `frontend-design` | frontend-design + ui-ux-pro-max + taste-skill | Merge visual direction, UX checks, implementation constraints, and deterministic design search; remove repeated aesthetic slogans and fixed repository paths. |
| `browser-workflows` | browser-use + webapp-testing | Merge live browser operation with local-server testing; keep the external CLI boundary and remove platform-specific workspace assumptions. |
| `code-quality` | code-reviewer + code-simplifier | Route review and simplification as separate modes; remove fixed package-manager commands, model selection, and project-file assumptions. |
| `doc-coauthoring` | doc-coauthoring | Compress context gathering, section drafting, and reader testing; replace named platform tools and connectors with capability-based actions. |
| `test-driven-development` | test-driven-development | Use strict TDD for risky behavior and a targeted fast path for small low-risk edits. |
| `find-skills` | find-skills | Keep discovery and evaluation concise; require authorization before installation. |

`fullstack-developer` remains in originals and the Claude distribution but is omitted as a standalone Codex skill because its broad framework knowledge duplicates Codex's baseline capability.

## Updating an adaptation

1. Sync only the named source into `originals/`.
2. Read the changed original and the existing target distribution.
3. Decide independently which platform benefits from the new material.
4. Preserve unique workflows and deterministic resources; remove repeated general knowledge and platform-specific assumptions.
5. Update this mapping when a capability is merged, split, renamed, retained, or omitted.
6. Run repository validation and tests. Never copy this record into a distribution directory.
```

Rewrite README with this complete user-facing content:

````markdown
# skills-launch

为 Claude 和 Codex 维护的 Skill 源码与优化发行仓库。

## 目录模型

- `originals/`：完整上游内容，只用于同步和重新适配。
- `distributions/claude/skills/`：可直接安装给 Claude 的标准 Skill。
- `distributions/codex/skills/`：面向 Codex 精简、合并后的标准 Skill。
- `ADAPTATIONS.md`：集中记录来源、合并关系和平台适配规则，不随 Skill 安装。

安装完全使用仓库中已经检验的发行版，不访问上游网络，也不会安装 `originals/`。

## 安装

安装给 Codex：

```bash
python3 scripts/skills_launch.py install frontend-design --agent codex
```

安装给 Claude：

```bash
python3 scripts/skills_launch.py install frontend-design --agent claude
```

安装目标 Agent 的全部 Skill：

```bash
python3 scripts/skills_launch.py install-all --agent codex
python3 scripts/skills_launch.py install-all --agent claude
```

使用 `--target-dir <path>` 指定目录，使用 `--force` 替换已有安装。默认情况下，Codex 使用 `$CODEX_HOME/skills` 或 `$HOME/.agents/skills`，Claude 使用 `$CLAUDE_HOME/skills` 或 `$HOME/.claude/skills`；`AGENT_SKILLS_DIR` 可统一覆盖默认值。

## Codex 发行版

| Skill | 能力 |
| --- | --- |
| `frontend-design` | 前端设计、UI/UX、设计系统搜索与实现检查 |
| `browser-workflows` | Browser Use 操作和本地 Web 应用测试 |
| `code-quality` | 代码审查与行为保持的简化 |
| `doc-coauthoring` | 结构化文档协作与读者验证 |
| `test-driven-development` | 风险分级的 TDD 与小改动快速验证 |
| `find-skills` | 外部 Skill 发现、评估和授权安装 |

Codex 安装时可继续使用原名称作为别名，例如 `ui-ux-pro-max` 会安装合并后的 `frontend-design`，`browser-use` 会安装 `browser-workflows`。

## Claude 发行版

Claude 保留 11 个标准 Skill：`frontend-design`、`doc-coauthoring`、`fullstack-developer`、`code-reviewer`、`webapp-testing`、`browser-use`、`find-skills`、`ui-ux-pro-max`、`taste-skill`、`code-simplifier` 和 `test-driven-development`。

## Browser Use CLI

安装浏览器 Skill 不会自动修改 Python 环境。缺少 `browser-use` 命令时运行：

```bash
uv tool install --python 3.12 --upgrade --force browser-use
browser-use --doctor
```

## 维护

同步一个或全部完整原版：

```bash
python3 scripts/skills_launch.py sync browser-use
python3 scripts/skills_launch.py sync
```

同步只更新 `originals/`，不会覆盖任何发行版。适配前阅读 `ADAPTATIONS.md`。

完成修改前运行：

```bash
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```
````

- [ ] **Step 9: Run docs, validation, and full tests**

```bash
python3 -m unittest tests.test_repository_docs tests.test_validation -v
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```

Expected: all commands pass.

- [ ] **Step 10: Commit validation and documentation**

```bash
git add scripts/skills_launch.py tests/test_validation.py tests/test_repository_docs.py AGENTS.md CLAUDE.md ADAPTATIONS.md README.md
git commit -m "docs: define skill maintenance and install workflows"
```

### Task 8: Run clean-room installation and final regression checks

**Files:**
- Modify only files required by concrete failures found in this task.

**Interfaces:**
- Consumes: the finished manifest, installer, distributions, validation, and docs.
- Produces: evidence that checked-in Codex and Claude packages install without network or source-library access.

- [ ] **Step 1: Run static repository checks**

```bash
git diff --check
python3 scripts/skills_launch.py validate
python3 -m unittest discover -s tests -v
```

Expected: no whitespace errors; validation and all tests pass.

- [ ] **Step 2: Install representative aliases into isolated directories**

```bash
codex_target="$(mktemp -d)"
claude_target="$(mktemp -d)"
python3 scripts/skills_launch.py install ui-ux-pro-max --agent codex --target-dir "$codex_target"
python3 scripts/skills_launch.py install code-simplifier --agent claude --target-dir "$claude_target"
test -f "$codex_target/frontend-design/SKILL.md"
test -f "$claude_target/code-simplifier/SKILL.md"
rm -rf "$codex_target" "$claude_target"
```

Expected: the Codex alias installs the merged `frontend-design`; the Claude name installs the normalized Claude `code-simplifier`.

- [ ] **Step 3: Install all skills for each agent and inspect the counts**

```bash
codex_target="$(mktemp -d)"
claude_target="$(mktemp -d)"
python3 scripts/skills_launch.py install-all --agent codex --target-dir "$codex_target"
python3 scripts/skills_launch.py install-all --agent claude --target-dir "$claude_target"
test "$(find "$codex_target" -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 6
test "$(find "$claude_target" -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 11
rm -rf "$codex_target" "$claude_target"
```

Expected: exactly 6 Codex directories and 11 Claude directories. Browser Use may print dependency guidance but installation still succeeds.

- [ ] **Step 4: Smoke-test bundled runtime scripts**

```bash
python3 distributions/codex/skills/frontend-design/scripts/search.py "SaaS dashboard" --stack react --json
python3 distributions/codex/skills/browser-workflows/scripts/with_server.py --help
```

Expected: design search emits JSON results and server helper emits usage.

- [ ] **Step 5: Confirm the final diff matches the approved scope**

```bash
git status --short
git diff --stat master~6..HEAD
git log --oneline -8
```

Verify the diff contains the original migration, two distributions, installer/tests, centralized adaptation docs, root guidance, and the previously requested `code-review` removal, with no unrelated files.

- [ ] **Step 6: Commit any evidence-driven correction**

If Step 1-5 required a correction, stage only the affected implementation and test files and commit with a message naming that correction. If no correction was required, do not create an empty commit.
