import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CodexCatalogTest(unittest.TestCase):
    def test_claude_code_review_plugin_is_not_listed(self):
        manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        names = {skill["name"] for skill in manifest["skills"]}

        self.assertNotIn("code-review", names)
        self.assertFalse((ROOT / "skills" / "code-review").exists())

    def test_readme_does_not_recommend_claude_code_review_plugin(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertNotIn("anthropics/claude-plugins-official/tree/main/plugins/code-review", readme)


if __name__ == "__main__":
    unittest.main()
