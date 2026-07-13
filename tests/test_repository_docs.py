import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryDocsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))

    def assert_intent_router(self, filename, agent):
        text = (ROOT / filename).read_text(encoding="utf-8")
        self.assertIn("Maintenance mode", text)
        self.assertIn("Installation mode", text)
        self.assertIn("ADAPTATIONS.md", text)
        self.assertIn(f"--agent {agent}", text)

    def test_agents_routes_maintenance_and_installation(self):
        self.assert_intent_router("AGENTS.md", "codex")

    def test_claude_routes_maintenance_and_installation(self):
        self.assert_intent_router("CLAUDE.md", "claude")

    def test_adaptations_centralizes_sources_and_codex_changes(self):
        text = (ROOT / "ADAPTATIONS.md").read_text(encoding="utf-8")
        self.assertIn("2026-07-13", text)
        self.assertIn("migration-quickstart", text)
        self.assertIn("frontend-design + ui-ux-pro-max + taste-skill", text)
        self.assertIn("browser-use + webapp-testing", text)
        self.assertIn("code-reviewer + code-simplifier", text)

        original_section = text.split("## Original catalog", 1)[1].split("## Claude map", 1)[0]
        original_names = re.findall(
            r"^\| `([^`]+)` \| https://github\.com/",
            original_section,
            re.MULTILINE,
        )
        self.assertEqual(len(original_names), len(self.manifest["sources"]))
        self.assertEqual(set(original_names), {source["name"] for source in self.manifest["sources"]})

        codex_section = text.split("## Codex map", 1)[1].split("## Updating an adaptation", 1)[0]
        codex_names = re.findall(r"^\| `([^`]+)` \|", codex_section, re.MULTILINE)
        self.assertEqual(len(codex_names), len(self.manifest["distributions"]["codex"]))
        self.assertEqual(
            set(codex_names),
            {entry["name"] for entry in self.manifest["distributions"]["codex"]},
        )

    def test_readme_documents_agent_specific_install_and_browser_dependency(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("install frontend-design --agent codex", text)
        self.assertIn("install-all --agent claude", text)
        self.assertIn("uv tool install --python 3.12 --upgrade --force browser-use", text)
        self.assertIn("browser-use --doctor", text)

        codex_section = text.split("## Codex 发行版", 1)[1].split("## Claude 发行版", 1)[0]
        codex_names = re.findall(r"^\| `([^`]+)` \|", codex_section, re.MULTILINE)
        self.assertEqual(len(codex_names), len(self.manifest["distributions"]["codex"]))
        self.assertEqual(
            set(codex_names),
            {entry["name"] for entry in self.manifest["distributions"]["codex"]},
        )

        claude_entries = self.manifest["distributions"]["claude"]
        claude_section = text.split("## Claude 发行版", 1)[1].split("## Browser Use CLI", 1)[0]
        self.assertIn(f"{len(claude_entries)} 个标准 Skill", text)
        for entry in claude_entries:
            self.assertIn(f"`{entry['name']}`", claude_section)


if __name__ == "__main__":
    unittest.main()
