import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("skills_launch_validation", ROOT / "scripts/skills_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ValidationTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()
        self.manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))

    def test_repository_manifest_and_distributions_validate(self):
        self.assertEqual(self.installer.validate_manifest(self.manifest, ROOT), [])

    def test_unknown_source_mapping_is_rejected(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["distributions"]["codex"][0]["sources"] = ["missing-source"]
        errors = self.installer.validate_manifest(manifest, ROOT)
        self.assertTrue(any("unknown source" in error for error in errors), errors)

    def test_repository_path_escape_is_rejected(self):
        manifest = json.loads(json.dumps(self.manifest))
        manifest["sources"][0]["original"] = "../outside"
        errors = self.installer.validate_manifest(manifest, ROOT)
        self.assertTrue(any("escapes repository" in error for error in errors), errors)

    def test_codex_provenance_text_is_rejected(self):
        manifest = {
            "version": 2,
            "sources": [],
            "distributions": {"claude": [], "codex": [{
                "name": "sample", "sources": [], "path": "dist/sample"
            }]},
        }
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "dist/sample"
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(
                "---\nname: sample\ndescription: Use for sample tasks.\n---\n\nAdapted from upstream.\n",
                encoding="utf-8",
            )
            errors = self.installer.validate_manifest(manifest, root)
        self.assertTrue(any("forbidden text" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
