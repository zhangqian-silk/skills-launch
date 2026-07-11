import importlib.util
import json
import os
import shutil
import tempfile
import unittest
import zipfile
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_installer_module():
    module_path = ROOT / "scripts" / "skills_launch.py"
    spec = importlib.util.spec_from_file_location("skills_launch", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SuperpowersSuiteCatalogTest(unittest.TestCase):
    def test_superpowers_suite_replaces_standalone_subset(self):
        manifest = json.loads((ROOT / "skills.json").read_text(encoding="utf-8"))
        entries = {entry["name"]: entry for entry in manifest["skills"]}

        self.assertIn("superpowers", entries)
        self.assertNotIn("brainstorming", entries)
        self.assertNotIn("test-driven-development", entries)

        suite = entries["superpowers"]
        self.assertEqual(suite["package_type"], "skill_suite")
        self.assertEqual(suite["source"]["kind"], "github_dir")
        self.assertEqual(suite["source"]["repo"], "obra/superpowers")
        self.assertEqual(suite["source"]["path"], "")
        self.assertEqual(suite["fallback"], "suites/superpowers")

    def test_superpowers_fallback_contains_suite_manifest_and_core_skill(self):
        fallback = ROOT / "suites" / "superpowers"

        self.assertTrue((fallback / ".codex-plugin" / "plugin.json").is_file())
        self.assertTrue((fallback / "skills" / "using-superpowers" / "SKILL.md").is_file())

    def test_skill_suite_defaults_to_plugin_directory(self):
        installer = load_installer_module()

        with mock.patch.dict(os.environ, {"CODEX_HOME": "/tmp/codex-home"}, clear=True):
            target = installer.default_target_dir("skill_suite")

        self.assertEqual(target, Path("/tmp/codex-home/plugins"))

    def test_repository_root_source_uses_archive_download(self):
        installer = load_installer_module()
        source = {
            "kind": "github_dir",
            "repo": "obra/superpowers",
            "ref": "main",
            "path": "",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.object(installer, "save_github_directory_via_api") as via_api:
                with mock.patch.object(installer, "save_github_directory_via_zip") as via_zip:
                    installer.save_github_source(source, Path(temp_dir) / "superpowers")

        via_api.assert_not_called()
        via_zip.assert_called_once()

    def test_archive_download_preserves_executable_files(self):
        installer = load_installer_module()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fixture = temp_path / "fixture.zip"
            destination = temp_path / "installed"
            executable = zipfile.ZipInfo("superpowers-main/hooks/session-start")
            executable.create_system = 3
            executable.external_attr = 0o100755 << 16
            with zipfile.ZipFile(fixture, "w") as archive:
                archive.writestr(executable, "#!/bin/sh\n")

            def copy_fixture(_url, *, output_path=None, expect_json=False):
                self.assertFalse(expect_json)
                shutil.copyfile(fixture, output_path)

            with mock.patch.object(installer, "request_url", side_effect=copy_fixture):
                installer.save_github_directory_via_zip(
                    "obra/superpowers",
                    "main",
                    "",
                    destination,
                )

            self.assertTrue(os.access(destination / "hooks" / "session-start", os.X_OK))

    def test_install_all_routes_skill_suite_to_suites_directory(self):
        installer = load_installer_module()
        args = Namespace(
            package_type="all",
            skills_dir="/tmp/skills",
            plugins_dir="/tmp/plugins",
            suites_dir="/tmp/suites",
            force=False,
            use_fallback_only=True,
        )

        with mock.patch.object(
            installer,
            "load_manifest",
            return_value={"skills": [{"name": "superpowers", "package_type": "skill_suite"}]},
        ):
            with mock.patch.object(installer, "install_skill") as install_skill:
                installer.install_all(args)

        self.assertEqual(install_skill.call_args.args[0].target_dir, "/tmp/suites")


if __name__ == "__main__":
    unittest.main()
