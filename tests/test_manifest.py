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
