import importlib.util
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("skills_launch_sync", ROOT / "scripts/skills_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SyncTest(unittest.TestCase):
    def test_sync_replaces_only_original_after_successful_download(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            distribution = root / "distributions/codex/skills/sample"
            original.mkdir(parents=True)
            distribution.mkdir(parents=True)
            (original / "SKILL.md").write_text("old", encoding="utf-8")
            (distribution / "SKILL.md").write_text("optimized", encoding="utf-8")
            manifest = {
                "sources": [{
                    "name": "sample",
                    "source": {"kind": "github_file", "repo": "o/r", "ref": "main", "path": "SKILL.md"},
                    "original": "originals/sample",
                }]
            }

            def download(_source, destination):
                destination.mkdir(parents=True, exist_ok=True)
                (destination / "SKILL.md").write_text("new", encoding="utf-8")

            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source", side_effect=download):
                installer.sync_upstreams(Namespace(names=["sample"]))

            self.assertEqual((original / "SKILL.md").read_text(encoding="utf-8"), "new")
            self.assertEqual((distribution / "SKILL.md").read_text(encoding="utf-8"), "optimized")

    def test_failed_sync_preserves_existing_original(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            original = root / "originals/sample"
            original.mkdir(parents=True)
            (original / "SKILL.md").write_text("old", encoding="utf-8")
            manifest = {"sources": [{"name": "sample", "source": {"repo": "o/r", "path": "x"}, "original": "originals/sample"}]}
            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source", side_effect=installer.SkillLaunchError("offline")):
                with self.assertRaises(installer.SkillLaunchError):
                    installer.sync_upstreams(Namespace(names=["sample"]))
            self.assertEqual((original / "SKILL.md").read_text(encoding="utf-8"), "old")


if __name__ == "__main__":
    unittest.main()
