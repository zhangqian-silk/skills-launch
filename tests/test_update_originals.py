import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_updater():
    path = ROOT / "scripts/update_originals.py"
    spec = importlib.util.spec_from_file_location("update_originals", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UpdateOriginalsTest(unittest.TestCase):
    def setUp(self):
        self.updater = load_updater()

    def test_affected_skills_uses_source_mapping(self):
        manifest = {
            "skills": [
                {
                    "name": "browser-workflows",
                    "sources": ["browser-use", "webapp-testing"],
                    "path": "skills/browser-workflows",
                },
                {
                    "name": "unrelated-skill",
                    "sources": ["unrelated-source"],
                    "path": "skills/unrelated-skill",
                },
            ]
        }
        self.assertEqual(
            self.updater.affected_skills(manifest, "browser-use"),
            [("browser-workflows", "skills/browser-workflows")],
        )

    def test_update_replaces_only_original_and_reports_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            original.mkdir(parents=True)
            (original / "changed.md").write_text("old\n", encoding="utf-8")
            (original / "deleted.md").write_text("delete\n", encoding="utf-8")
            skill = root / "skills/sample"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("maintained\n", encoding="utf-8")
            source = {"name": "sample", "original": "originals/sample"}

            def fetch(_source, destination):
                destination.mkdir(parents=True)
                (destination / "changed.md").write_text("new\n", encoding="utf-8")
                (destination / "added.md").write_text("add\n", encoding="utf-8")

            result = self.updater.update_original(source, root, fetcher=fetch)

            self.assertTrue(result.changed)
            self.assertEqual(result.added, ("added.md",))
            self.assertEqual(result.modified, ("changed.md",))
            self.assertEqual(result.deleted, ("deleted.md",))
            self.assertEqual((original / "changed.md").read_text(encoding="utf-8"), "new\n")
            self.assertEqual((skill / "SKILL.md").read_text(encoding="utf-8"), "maintained\n")

    def test_failed_update_preserves_existing_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            original.mkdir(parents=True)
            (original / "SKILL.md").write_text("old\n", encoding="utf-8")
            source = {"name": "sample", "original": "originals/sample"}

            def fail(_source, _destination):
                raise RuntimeError("offline")

            with self.assertRaisesRegex(RuntimeError, "offline"):
                self.updater.update_original(source, root, fetcher=fail)
            self.assertEqual((original / "SKILL.md").read_text(encoding="utf-8"), "old\n")

    def test_unchanged_update_does_not_replace_original(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            original.mkdir(parents=True)
            current = original / "SKILL.md"
            current.write_text("same\n", encoding="utf-8")
            source = {"name": "sample", "original": "originals/sample"}

            def fetch(_source, destination):
                destination.mkdir(parents=True)
                (destination / "SKILL.md").write_text("same\n", encoding="utf-8")

            result = self.updater.update_original(source, root, fetcher=fetch)
            self.assertFalse(result.changed)
            self.assertEqual(current.read_text(encoding="utf-8"), "same\n")


if __name__ == "__main__":
    unittest.main()
