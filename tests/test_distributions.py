import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


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
        skill = ROOT / "distributions/claude/skills/ui-ux-pro-max"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Resolve the absolute directory containing this `SKILL.md` file into `SKILL_ROOT`.",
            instructions,
        )
        self.assertIn("Keep the user's project as the current working directory.", instructions)
        self.assertNotIn("skills/ui-ux-pro-max/scripts/search.py", instructions)
        self.assertNotIn("Run the commands below from the directory containing", instructions)
        self.assertNotIn("python3 scripts/search.py", instructions)
        commands = [
            line
            for line in instructions.splitlines()
            if line.startswith("python3 ") and "search.py" in line
        ]
        self.assertTrue(commands)
        for command in commands:
            self.assertTrue(
                command.startswith('python3 "$SKILL_ROOT/scripts/search.py"'),
                command,
            )
        script = skill / "scripts/search.py"
        with TemporaryDirectory() as project_dir:
            completed = subprocess.run(
                [sys.executable, "-B", str(script), "fintech dashboard", "--domain", "color", "--json"],
                cwd=project_dir,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"domain": "color"', completed.stdout)

    def test_ui_persistence_writes_to_project_working_directory(self):
        skill = ROOT / "distributions/claude/skills/ui-ux-pro-max"
        script = skill / "scripts/search.py"
        installed_entries_before = {
            path.relative_to(skill) for path in skill.rglob("*")
        }
        with TemporaryDirectory() as project_dir:
            project = Path(project_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(script),
                    "fintech dashboard",
                    "--design-system",
                    "--persist",
                    "-p",
                    "Persistence Regression",
                ],
                cwd=project,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(
                (project / "design-system/persistence-regression/MASTER.md").is_file()
            )
            self.assertFalse((skill / "design-system").exists())
        installed_entries_after = {
            path.relative_to(skill) for path in skill.rglob("*")
        }
        self.assertEqual(installed_entries_after, installed_entries_before)

    def test_webapp_testing_uses_portable_output_paths(self):
        skill = ROOT / "distributions/claude/skills/webapp-testing"
        portable_examples = [
            skill / "SKILL.md",
            skill / "examples/console_logging.py",
            skill / "examples/element_discovery.py",
            skill / "examples/static_html_automation.py",
        ]
        for path in portable_examples:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("/mnt/user-data/outputs", text, path.name)
            self.assertNotIn("/tmp", text, path.name)
            self.assertIn('Path("artifacts")', text, path.name)
            self.assertIn("mkdir(parents=True, exist_ok=True)", text, path.name)

    def test_webapp_testing_python_files_compile(self):
        skill = ROOT / "distributions/claude/skills/webapp-testing"
        for path in skill.rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")

    def test_claude_distribution_has_no_trailing_whitespace(self):
        distribution = ROOT / "distributions/claude"
        for path in distribution.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            for line_number, line in enumerate(path.read_bytes().splitlines(), start=1):
                self.assertEqual(
                    line,
                    line.rstrip(b" \t"),
                    f"{path.relative_to(ROOT)}:{line_number}",
                )


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

    def test_frontend_design_instructions_preserve_project_cwd(self):
        skill = ROOT / "distributions/codex/skills/frontend-design"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Resolve the absolute directory containing this `SKILL.md` file into `SKILL_ROOT`.",
            instructions,
        )
        self.assertIn("Keep the user's project as the current working directory.", instructions)
        self.assertNotIn("python3 scripts/search.py", instructions)
        commands = [
            line
            for line in instructions.splitlines()
            if line.startswith("python3 ") and "search.py" in line
        ]
        self.assertTrue(commands)
        for command in commands:
            self.assertTrue(
                command.startswith('python3 "$SKILL_ROOT/scripts/search.py"'),
                command,
            )

    def test_frontend_design_persistence_writes_to_project_working_directory(self):
        skill = ROOT / "distributions/codex/skills/frontend-design"
        script = skill / "scripts/search.py"
        installed_entries_before = {path.relative_to(skill) for path in skill.rglob("*")}
        with TemporaryDirectory() as project_dir:
            project = Path(project_dir)
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(script),
                    "fintech dashboard",
                    "--design-system",
                    "--persist",
                    "-p",
                    "Codex Persistence",
                ],
                cwd=project,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((project / "design-system/codex-persistence/MASTER.md").is_file())
            self.assertFalse((skill / "design-system").exists())
        installed_entries_after = {path.relative_to(skill) for path in skill.rglob("*")}
        self.assertEqual(installed_entries_after, installed_entries_before)

    def test_frontend_design_search_is_deterministic_and_agent_neutral(self):
        script = ROOT / "distributions/codex/skills/frontend-design/scripts/search.py"
        command = [sys.executable, "-B", str(script), "fintech dashboard", "--domain", "color"]
        first = subprocess.run(command, text=True, capture_output=True, check=False)
        second = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)
        for agent_specific in ("Claude", "UI Pro Max", "UI/UX Pro Max"):
            self.assertNotIn(agent_specific, first.stdout)

    def test_frontend_design_contains_only_runtime_resources(self):
        skill = ROOT / "distributions/codex/skills/frontend-design"
        self.assertEqual(
            {path.name for path in skill.iterdir()},
            {"SKILL.md", "scripts", "data"},
        )
        self.assertEqual(
            {path.name for path in (skill / "scripts").iterdir()},
            {"search.py", "core.py", "design_system.py"},
        )
        self.assertFalse((skill / "data/_sync_all.py").exists())
        for path in [skill / "SKILL.md", *(skill / "scripts").glob("*.py")]:
            text = path.read_text(encoding="utf-8")
            for forbidden in (
                "Claude",
                "UI Pro Max",
                "UI/UX Pro Max",
                "ui-ux-pro-max",
                "github.com",
                "Adapted from",
                "originals/",
            ):
                self.assertNotIn(forbidden, text, path.name)
            self.assertNotIn(str(ROOT), text, path.name)


if __name__ == "__main__":
    unittest.main()
