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
