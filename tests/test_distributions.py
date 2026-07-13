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
