import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentBrowserCatalogTest(unittest.TestCase):
    def test_agent_browser_is_listed_with_fallback_copy(self):
        manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        entry = next(
            (skill for skill in manifest["skills"] if skill["name"] == "agent-browser"),
            None,
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry["package_type"], "skill")
        self.assertEqual(entry["source"]["kind"], "github_dir")
        self.assertEqual(entry["source"]["repo"], "vercel-labs/agent-browser")
        self.assertEqual(entry["source"]["path"], "skills/agent-browser")
        self.assertEqual(entry["fallback"], "skills/agent-browser")
        self.assertTrue((ROOT / entry["fallback"] / "SKILL.md").exists())

    def test_root_skill_guides_agent_browser_cli_installation(self):
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("agent-browser", root_skill)
        self.assertIn("npm i -g agent-browser", root_skill)
        self.assertIn("agent-browser install", root_skill)


if __name__ == "__main__":
    unittest.main()
