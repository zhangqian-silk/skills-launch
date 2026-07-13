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
        skill = ROOT / "distributions/claude/skills/ui-ux-pro-max"
        instructions = (skill / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Run the commands below from the directory containing this `SKILL.md` file.",
            instructions,
        )
        self.assertNotIn("skills/ui-ux-pro-max/scripts/search.py", instructions)
        completed = subprocess.run(
            [sys.executable, "scripts/search.py", "fintech dashboard", "--domain", "color", "--json"],
            cwd=skill,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"domain": "color"', completed.stdout)

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


if __name__ == "__main__":
    unittest.main()
