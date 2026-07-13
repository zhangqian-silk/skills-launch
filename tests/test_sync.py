import importlib.util
import io
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
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

    def test_sync_rejects_malicious_original_path_before_downloading(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repository"
            root.mkdir()
            marker = root / "existing.txt"
            marker.write_text("unchanged", encoding="utf-8")
            manifest = {
                "sources": [{
                    "name": "sample",
                    "source": {
                        "kind": "github_file",
                        "repo": "o/r",
                        "ref": "main",
                        "path": "SKILL.md",
                    },
                    "original": ".",
                }]
            }
            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source") as download:
                with self.assertRaises(installer.SkillLaunchError):
                    installer.sync_upstreams(Namespace(names=["sample"]))

            download.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
            self.assertEqual(list(root.iterdir()), [marker])

    def test_sync_rejects_symlinked_original_before_downloading(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "repository"
            originals = root / "originals"
            originals.mkdir(parents=True)
            (originals / "sample-source").symlink_to(root, target_is_directory=True)
            marker = root / "existing.txt"
            marker.write_text("unchanged", encoding="utf-8")
            manifest = {
                "sources": [{
                    "name": "sample-source",
                    "source": {
                        "kind": "github_file",
                        "repo": "o/r",
                        "ref": "main",
                        "path": "SKILL.md",
                    },
                    "original": "originals/sample-source",
                }]
            }
            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source") as download:
                with self.assertRaises(installer.SkillLaunchError):
                    installer.sync_upstreams(Namespace(names=["sample-source"]))

            download.assert_not_called()
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
            self.assertTrue((originals / "sample-source").is_symlink())

    def test_sync_aggregates_operational_failure_and_continues_later_sources(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "originals/first"
            second = root / "originals/second"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "SKILL.md").write_text("old-first", encoding="utf-8")
            (second / "SKILL.md").write_text("old-second", encoding="utf-8")
            manifest = {
                "sources": [
                    {
                        "name": "first",
                        "source": {
                            "kind": "github_file",
                            "repo": "o/first",
                            "ref": "main",
                            "path": "SKILL.md",
                        },
                        "original": "originals/first",
                    },
                    {
                        "name": "second",
                        "source": {
                            "kind": "github_file",
                            "repo": "o/second",
                            "ref": "main",
                            "path": "SKILL.md",
                        },
                        "original": "originals/second",
                    },
                ]
            }
            attempted = []

            def download(source, destination):
                attempted.append(source["repo"])
                if source["repo"] == "o/first":
                    raise OSError("archive extraction failed")
                destination.mkdir(parents=True)
                (destination / "SKILL.md").write_text("new-second", encoding="utf-8")

            stderr = io.StringIO()
            stdout = io.StringIO()
            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source", side_effect=download):
                with redirect_stderr(stderr), redirect_stdout(stdout):
                    result = installer.main(["sync", "first", "second"])

            self.assertEqual(result, 1)
            self.assertEqual(attempted, ["o/first", "o/second"])
            self.assertEqual((first / "SKILL.md").read_text(encoding="utf-8"), "old-first")
            self.assertEqual((second / "SKILL.md").read_text(encoding="utf-8"), "new-second")
            self.assertIn("Failed to sync 'first'", stderr.getvalue())
            self.assertIn("archive extraction failed", stderr.getvalue())
            self.assertIn("Sync finished with 1 failure(s)", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())
            self.assertIn("Syncing first", stdout.getvalue())
            self.assertIn("Syncing second", stdout.getvalue())

    def test_sync_aggregates_malformed_source_and_continues_valid_source(self):
        installer = load_installer()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "originals/first"
            second = root / "originals/second"
            first.mkdir(parents=True)
            second.mkdir(parents=True)
            (first / "SKILL.md").write_text("old-first", encoding="utf-8")
            (second / "SKILL.md").write_text("old-second", encoding="utf-8")
            manifest = {
                "sources": [
                    {"name": "first", "original": "originals/first"},
                    None,
                    {},
                    {
                        "name": "second",
                        "source": {
                            "kind": "github_file",
                            "repo": "o/second",
                            "ref": "main",
                            "path": "SKILL.md",
                        },
                        "original": "originals/second",
                    },
                ]
            }

            def download(source, destination):
                destination.mkdir(parents=True)
                (destination / "SKILL.md").write_text("new-second", encoding="utf-8")

            stderr = io.StringIO()
            with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                installer, "load_manifest", return_value=manifest
            ), mock.patch.object(installer, "save_github_source", side_effect=download):
                with redirect_stderr(stderr), redirect_stdout(io.StringIO()):
                    result = installer.main(["sync", "first", "second"])

            self.assertEqual(result, 1)
            self.assertEqual((first / "SKILL.md").read_text(encoding="utf-8"), "old-first")
            self.assertEqual((second / "SKILL.md").read_text(encoding="utf-8"), "new-second")
            self.assertIn("Failed to sync 'first'", stderr.getvalue())
            self.assertIn("missing source metadata", stderr.getvalue())
            self.assertIn("Sync finished with 1 failure(s)", stderr.getvalue())
            self.assertNotIn("Traceback", stderr.getvalue())

    def test_sync_does_not_catch_process_control_exceptions(self):
        installer = load_installer()
        for exception in (KeyboardInterrupt(), SystemExit(9)):
            with self.subTest(exception=type(exception).__name__), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                original = root / "originals/sample"
                original.mkdir(parents=True)
                (original / "SKILL.md").write_text("old", encoding="utf-8")
                manifest = {
                    "sources": [{
                        "name": "sample",
                        "source": {
                            "kind": "github_file",
                            "repo": "o/r",
                            "ref": "main",
                            "path": "SKILL.md",
                        },
                        "original": "originals/sample",
                    }]
                }
                with mock.patch.object(installer, "REPOSITORY_ROOT", root), mock.patch.object(
                    installer, "load_manifest", return_value=manifest
                ), mock.patch.object(installer, "save_github_source", side_effect=exception):
                    with self.assertRaises(type(exception)):
                        installer.sync_upstreams(Namespace(names=["sample"]))
                self.assertEqual((original / "SKILL.md").read_text(encoding="utf-8"), "old")


if __name__ == "__main__":
    unittest.main()
