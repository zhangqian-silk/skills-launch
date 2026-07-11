import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class BrowserUseCatalogTest(unittest.TestCase):
    def test_browser_use_is_listed_with_fallback_copy(self):
        manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        entry = next(
            (skill for skill in manifest["skills"] if skill["name"] == "browser-use"),
            None,
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry["package_type"], "skill")
        self.assertEqual(entry["source"]["kind"], "github_dir")
        self.assertEqual(entry["source"]["repo"], "browser-use/browser-use")
        self.assertEqual(entry["source"]["path"], "skills/browser-use")
        self.assertEqual(entry["fallback"], "skills/browser-use")
        self.assertTrue((ROOT / entry["fallback"] / "SKILL.md").exists())

    def test_agent_browser_is_no_longer_listed(self):
        manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        names = {skill["name"] for skill in manifest["skills"]}

        self.assertNotIn("agent-browser", names)

    def test_root_skill_guides_browser_use_cli_installation(self):
        root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("uv tool install --python 3.12 --upgrade --force browser-use", root_skill)
        self.assertIn("browser-use --doctor", root_skill)
        self.assertIn("browser-use skill install", root_skill)

    def test_readme_guides_browser_use_cli_installation(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("uv tool install --python 3.12 --upgrade --force browser-use", readme)
        self.assertIn("browser-use --doctor", readme)


if __name__ == "__main__":
    unittest.main()
