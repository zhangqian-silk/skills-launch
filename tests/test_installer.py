import importlib.util
import os
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location("skills_launch", ROOT / "scripts/skills_launch.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.installer = load_installer()

    def test_distribution_lookup_resolves_alias_within_agent(self):
        manifest = {
            "distributions": {
                "codex": [{"name": "browser-workflows", "aliases": ["browser-use"]}],
                "claude": [{"name": "browser-use"}],
            }
        }
        self.assertEqual(
            self.installer.get_distribution(manifest, "codex", "browser-use")["name"],
            "browser-workflows",
        )
        self.assertEqual(
            self.installer.get_distribution(manifest, "claude", "browser-use")["name"],
            "browser-use",
        )

    def test_default_targets_are_agent_specific(self):
        with mock.patch.dict(os.environ, {"CODEX_HOME": "/tmp/codex"}, clear=True):
            self.assertEqual(self.installer.default_target_dir("codex"), Path("/tmp/codex/skills"))
        with mock.patch.dict(os.environ, {"CLAUDE_HOME": "/tmp/claude"}, clear=True):
            self.assertEqual(self.installer.default_target_dir("claude"), Path("/tmp/claude/skills"))

    def test_install_copies_distribution_without_downloading(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "distributions/codex/skills/sample"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text("skill", encoding="utf-8")
            target = root / "target"
            manifest = {
                "distributions": {
                    "codex": [{"name": "sample", "path": "distributions/codex/skills/sample"}]
                }
            }
            args = Namespace(name="sample", agent="codex", target_dir=str(target), force=False)
            with mock.patch.object(self.installer, "REPOSITORY_ROOT", root), mock.patch.object(
                self.installer, "load_manifest", return_value=manifest
            ), mock.patch.object(self.installer, "save_github_source") as download:
                self.installer.install_skill(args)
            download.assert_not_called()
            self.assertEqual((target / "sample/SKILL.md").read_text(encoding="utf-8"), "skill")

    def test_install_commands_reject_malicious_manifest_before_copying(self):
        for command in ("install", "install-all"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir) / "repository"
                root.mkdir()
                marker = root / "existing.txt"
                marker.write_text("unchanged", encoding="utf-8")
                target = Path(temp_dir) / "target"
                manifest = {
                    "distributions": {
                        "codex": [{"name": "sample", "path": "."}],
                        "claude": [],
                    }
                }
                if command == "install":
                    args = Namespace(
                        name="sample",
                        agent="codex",
                        target_dir=str(target),
                        force=False,
                    )
                    invoke = self.installer.install_skill
                else:
                    args = Namespace(agent="codex", target_dir=str(target), force=False)
                    invoke = self.installer.install_all

                with mock.patch.object(self.installer, "REPOSITORY_ROOT", root), mock.patch.object(
                    self.installer, "load_manifest", return_value=manifest
                ):
                    with self.assertRaises(self.installer.SkillLaunchError):
                        invoke(args)

                self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
                self.assertEqual(list(root.iterdir()), [marker])
                self.assertFalse(target.exists())

    def test_install_rejects_symlinked_distribution_and_preserves_existing_target(self):
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir) / "repository"
                original = root / "originals/sample-source"
                distribution = root / "distributions/codex/skills/sample"
                original.mkdir(parents=True)
                (original / "SKILL.md").write_text("upstream", encoding="utf-8")
                if nested:
                    distribution.mkdir(parents=True)
                    (distribution / "SKILL.md").write_text("distribution", encoding="utf-8")
                    (distribution / "linked.md").symlink_to(original / "SKILL.md")
                else:
                    distribution.parent.mkdir(parents=True)
                    distribution.symlink_to(original, target_is_directory=True)
                repository_marker = root / "existing.txt"
                repository_marker.write_text("unchanged", encoding="utf-8")
                target = Path(temp_dir) / "target"
                existing = target / "sample"
                existing.mkdir(parents=True)
                (existing / "SKILL.md").write_text("old-target", encoding="utf-8")
                manifest = {
                    "distributions": {
                        "codex": [{
                            "name": "sample",
                            "path": "distributions/codex/skills/sample",
                        }],
                        "claude": [],
                    }
                }
                args = Namespace(
                    name="sample",
                    agent="codex",
                    target_dir=str(target),
                    force=True,
                )
                with mock.patch.object(self.installer, "REPOSITORY_ROOT", root), mock.patch.object(
                    self.installer, "load_manifest", return_value=manifest
                ):
                    with self.assertRaises(self.installer.SkillLaunchError):
                        self.installer.install_skill(args)

                self.assertEqual(repository_marker.read_text(encoding="utf-8"), "unchanged")
                self.assertEqual(
                    (existing / "SKILL.md").read_text(encoding="utf-8"),
                    "old-target",
                )
                self.assertFalse((existing / "linked.md").exists())

    def test_failed_forced_copy_preserves_existing_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            source.mkdir()
            (source / "SKILL.md").write_text("new", encoding="utf-8")
            destination = root / "target/sample"
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("old", encoding="utf-8")
            with mock.patch("shutil.copytree", side_effect=OSError("copy failed")):
                with self.assertRaises(OSError):
                    self.installer.copy_directory_atomic(source, destination, force=True)
            self.assertEqual((destination / "SKILL.md").read_text(encoding="utf-8"), "old")

    def test_missing_dependency_prints_install_and_verify_commands(self):
        entry = {
            "name": "browser-workflows",
            "dependencies": [{
                "command": "browser-use",
                "install": "uv tool install --python 3.12 --upgrade --force browser-use",
                "verify": "browser-use --doctor",
            }],
        }
        with mock.patch("shutil.which", return_value=None), mock.patch("builtins.print") as output:
            self.installer.report_dependencies(entry)
        rendered = "\n".join(str(call) for call in output.call_args_list)
        self.assertIn("uv tool install --python 3.12 --upgrade --force browser-use", rendered)
        self.assertIn("browser-use --doctor", rendered)


if __name__ == "__main__":
    unittest.main()
