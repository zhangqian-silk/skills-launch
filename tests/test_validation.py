import copy
import importlib.util
import io
import json
import shutil
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock


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

    def changed_manifest(self, path, value):
        manifest = copy.deepcopy(self.manifest)
        target = manifest
        for part in path[:-1]:
            target = target[part]
        target[path[-1]] = value
        return manifest

    def make_sample_repository(self, root, skill_text=None, directory="sample", agent="codex"):
        original = root / "originals/sample-source"
        original.mkdir(parents=True)
        skill = root / "distributions" / agent / "skills" / directory
        skill.mkdir(parents=True)
        if skill_text is None:
            skill_text = (
                "---\n"
                "name: sample\n"
                "description: Use for sample tasks.\n"
                "---\n\n"
                "# Sample\n"
            )
        (skill / "SKILL.md").write_text(skill_text, encoding="utf-8")
        manifest = {
            "version": 2,
            "sources": [{
                "name": "sample-source",
                "source": {
                    "kind": "github_file",
                    "repo": "owner/repository",
                    "ref": "main",
                    "path": "skills/sample/SKILL.md",
                },
                "original": "originals/sample-source",
            }],
            "distributions": {
                "claude": [],
                "codex": [],
            },
        }
        manifest["distributions"][agent] = [{
            "name": "sample",
            "sources": ["sample-source"],
            "path": f"distributions/{agent}/skills/{directory}",
        }]
        return manifest, skill

    def assert_validation_error(self, manifest, expected, root=ROOT):
        errors = self.installer.validate_manifest(manifest, root)
        self.assertIsInstance(errors, list)
        self.assertTrue(any(expected in error for error in errors), errors)

    def test_repository_manifest_and_distributions_validate(self):
        self.assertEqual(self.installer.validate_manifest(self.manifest, ROOT), [])

    def test_malformed_json_shapes_return_errors_instead_of_raising(self):
        cases = (
            ("null manifest", None, "manifest must be an object"),
            ("array manifest", [], "manifest must be an object"),
            ("invalid version", self.changed_manifest(["version"], "2"), "manifest version must be 2"),
            ("sources not list", self.changed_manifest(["sources"], {}), "sources must be a list"),
            (
                "distributions not object",
                self.changed_manifest(["distributions"], []),
                "distributions must be an object",
            ),
            (
                "source not object",
                self.changed_manifest(["sources", 0], "frontend-design"),
                "sources[0] must be an object",
            ),
            (
                "source spec not object",
                self.changed_manifest(["sources", 0, "source"], []),
                "sources[0].source must be an object",
            ),
            (
                "agent entries not list",
                self.changed_manifest(["distributions", "codex"], {}),
                "distributions.codex must be a list",
            ),
            (
                "distribution not object",
                self.changed_manifest(["distributions", "codex", 0], "frontend-design"),
                "distributions.codex[0] must be an object",
            ),
            (
                "aliases not list",
                self.changed_manifest(["distributions", "codex", 0, "aliases"], "ui-ux-pro-max"),
                "aliases must be a list",
            ),
            (
                "distribution sources not list",
                self.changed_manifest(["distributions", "codex", 0, "sources"], "frontend-design"),
                "sources must be a list",
            ),
            (
                "dependencies not list",
                self.changed_manifest(["distributions", "codex", 1, "dependencies"], {}),
                "dependencies must be a list",
            ),
            (
                "dependency not object",
                self.changed_manifest(["distributions", "codex", 1, "dependencies", 0], "browser-use"),
                "dependencies[0] must be an object",
            ),
        )
        for label, manifest, expected in cases:
            with self.subTest(label=label):
                self.assert_validation_error(manifest, expected)

    def test_required_manifest_values_are_non_empty_strings(self):
        cases = (
            ("source name", ["sources", 0, "name"], " ", "sources[0].name must be a non-empty string"),
            (
                "original path",
                ["sources", 0, "original"],
                3,
                "sources[0].original must be a non-empty string",
            ),
            (
                "source kind",
                ["sources", 0, "source", "kind"],
                "",
                "sources[0].source.kind must be a non-empty string",
            ),
            (
                "source repo",
                ["sources", 0, "source", "repo"],
                None,
                "sources[0].source.repo must be a non-empty string",
            ),
            (
                "source ref",
                ["sources", 0, "source", "ref"],
                [],
                "sources[0].source.ref must be a non-empty string",
            ),
            (
                "source path",
                ["sources", 0, "source", "path"],
                {},
                "sources[0].source.path must be a non-empty string",
            ),
            (
                "distribution name",
                ["distributions", "codex", 0, "name"],
                False,
                "distributions.codex[0].name must be a non-empty string",
            ),
            (
                "distribution path",
                ["distributions", "codex", 0, "path"],
                " ",
                "distributions.codex[0].path must be a non-empty string",
            ),
            (
                "empty source mapping",
                ["distributions", "codex", 0, "sources"],
                [],
                "sources must not be empty",
            ),
            (
                "invalid source mapping",
                ["distributions", "codex", 0, "sources"],
                [""],
                "sources[0] must be a non-empty string",
            ),
            (
                "invalid alias",
                ["distributions", "codex", 0, "aliases"],
                [1],
                "aliases[0] must be a non-empty string",
            ),
            (
                "dependency command",
                ["distributions", "codex", 1, "dependencies", 0, "command"],
                "",
                "dependencies[0].command must be a non-empty string",
            ),
            (
                "dependency install",
                ["distributions", "codex", 1, "dependencies", 0, "install"],
                None,
                "dependencies[0].install must be a non-empty string",
            ),
            (
                "dependency verify",
                ["distributions", "codex", 1, "dependencies", 0, "verify"],
                [],
                "dependencies[0].verify must be a non-empty string",
            ),
        )
        for label, path, value, expected in cases:
            with self.subTest(label=label):
                self.assert_validation_error(self.changed_manifest(path, value), expected)

    def test_distributions_require_exact_agent_keys(self):
        manifest = copy.deepcopy(self.manifest)
        del manifest["distributions"]["claude"]
        self.assert_validation_error(manifest, "exactly claude and codex")

    def test_duplicate_source_distribution_and_alias_bindings_are_rejected(self):
        cases = []

        duplicate_source = copy.deepcopy(self.manifest)
        duplicate_source["sources"].append(copy.deepcopy(duplicate_source["sources"][0]))
        cases.append(("source", duplicate_source, "source names must be unique"))

        duplicate_distribution = copy.deepcopy(self.manifest)
        duplicate_distribution["distributions"]["codex"].append(
            copy.deepcopy(duplicate_distribution["distributions"]["codex"][0])
        )
        cases.append(("distribution", duplicate_distribution, "distribution names must be unique"))

        duplicate_alias = copy.deepcopy(self.manifest)
        duplicate_alias["distributions"]["codex"][1]["aliases"].append("ui-ux-pro-max")
        cases.append(("alias duplicate", duplicate_alias, "aliases must be unique"))

        shadowing_alias = copy.deepcopy(self.manifest)
        shadowing_alias["distributions"]["codex"][0]["aliases"].append("find-skills")
        cases.append(("alias shadow", shadowing_alias, "aliases must be unique"))

        for label, manifest, expected in cases:
            with self.subTest(label=label):
                self.assert_validation_error(manifest, expected)

    def test_unknown_source_mapping_is_rejected(self):
        manifest = self.changed_manifest(
            ["distributions", "codex", 0, "sources"],
            ["missing-source"],
        )
        self.assert_validation_error(manifest, "unknown source")

    def test_unsupported_source_kind_is_rejected(self):
        manifest = self.changed_manifest(["sources", 0, "source", "kind"], "archive")
        self.assert_validation_error(manifest, "unsupported source kind")

    def test_repository_path_traversal_is_rejected_as_noncanonical(self):
        cases = (
            ("original", ["sources", 0, "original"]),
            ("distribution", ["distributions", "codex", 0, "path"]),
        )
        for label, path in cases:
            with self.subTest(label=label):
                manifest = self.changed_manifest(path, "../outside")
                self.assert_validation_error(manifest, "must be exactly")

    def test_source_and_distribution_paths_use_exact_namespaces(self):
        cases = (
            (
                "repository root as original",
                ["sources", 0, "original"],
                ".",
                "original must be exactly originals/frontend-design",
            ),
            (
                "distribution as original",
                ["sources", 0, "original"],
                "distributions/claude/skills/frontend-design",
                "original must be exactly originals/frontend-design",
            ),
            (
                "mismatched original name",
                ["sources", 0, "original"],
                "originals/doc-coauthoring",
                "original must be exactly originals/frontend-design",
            ),
            (
                "original as distribution",
                ["distributions", "codex", 0, "path"],
                "originals/frontend-design",
                "path must be exactly distributions/codex/skills/frontend-design",
            ),
            (
                "wrong agent namespace",
                ["distributions", "claude", 0, "path"],
                "distributions/codex/skills/frontend-design",
                "path must be exactly distributions/claude/skills/frontend-design",
            ),
            (
                "mismatched distribution name",
                ["distributions", "codex", 0, "path"],
                "distributions/codex/skills/doc-coauthoring",
                "path must be exactly distributions/codex/skills/frontend-design",
            ),
        )
        for label, path, value, expected in cases:
            with self.subTest(label=label):
                self.assert_validation_error(self.changed_manifest(path, value), expected)

    def test_source_and_distribution_namespaces_reject_symlinks(self):
        for label in ("original", "distribution", "nested distribution entry"):
            with self.subTest(label=label), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                manifest, skill = self.make_sample_repository(root)
                if label == "original":
                    original = root / "originals/sample-source"
                    shutil.rmtree(original)
                    original.symlink_to(root, target_is_directory=True)
                    expected = "source 'sample-source' namespace contains symlink"
                elif label == "distribution":
                    shutil.rmtree(skill)
                    skill.symlink_to(root / "originals/sample-source", target_is_directory=True)
                    expected = "codex/sample namespace contains symlink"
                else:
                    (skill / "linked-skill.md").symlink_to(
                        root / "originals/sample-source/SKILL.md"
                    )
                    expected = "codex/sample distribution tree contains symlink"
                self.assert_validation_error(manifest, expected, root)

    def test_source_and_distribution_names_are_safe_lowercase_hyphen_names(self):
        cases = (
            (["sources", 0, "name"], "Frontend-Design", "source name"),
            (["sources", 0, "name"], "../frontend-design", "source name"),
            (["distributions", "codex", 0, "name"], ".", "distribution name"),
            (["distributions", "claude", 0, "name"], "frontend_design", "distribution name"),
        )
        for path, value, expected in cases:
            with self.subTest(value=value):
                self.assert_validation_error(self.changed_manifest(path, value), expected)

    def test_missing_original_and_distribution_directories_are_rejected(self):
        for label, expected in (
            ("original", "missing original directory"),
            ("distribution", "missing distribution skill"),
        ):
            with self.subTest(label=label), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                manifest, skill = self.make_sample_repository(root)
                if label == "original":
                    shutil.rmtree(root / "originals/sample-source")
                else:
                    shutil.rmtree(skill)
                self.assert_validation_error(manifest, expected, root)

    def test_distribution_path_must_match_entry_name(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, directory="other-directory")
            self.assert_validation_error(
                manifest,
                "path must be exactly distributions/codex/skills/sample",
                root,
            )

    def test_dependency_requires_command_install_and_verify(self):
        manifest = copy.deepcopy(self.manifest)
        del manifest["distributions"]["codex"][1]["dependencies"][0]["verify"]
        self.assert_validation_error(manifest, "dependencies[0].verify must be a non-empty string")

    def test_codex_frontmatter_name_matches_manifest_and_directory(self):
        text = "---\nname: other\ndescription: Use for sample tasks.\n---\n\n# Sample\n"
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, text)
            self.assert_validation_error(manifest, "frontmatter name must match", root)

    def test_claude_frontmatter_name_matches_manifest_and_directory(self):
        text = "---\nname: other\ndescription: Use for sample tasks.\n---\n\n# Sample\n"
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, text, agent="claude")
            self.assert_validation_error(manifest, "frontmatter name must match", root)

    def test_codex_frontmatter_description_is_a_non_empty_string(self):
        text = "---\nname: sample\ndescription: \n---\n\n# Sample\n"
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, text)
            self.assert_validation_error(manifest, "description must be a non-empty string", root)

    def test_codex_frontmatter_contains_only_name_and_description(self):
        text = (
            "---\nname: sample\ndescription: Use for sample tasks.\nmodel: custom\n---\n\n# Sample\n"
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, text)
            self.assert_validation_error(manifest, "frontmatter must contain only name and description", root)

    def test_codex_line_limit_is_enforced(self):
        text = "---\nname: sample\ndescription: Use for sample tasks.\n---\n" + "line\n" * 247
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, text)
            self.assert_validation_error(manifest, "exceeds 250 lines", root)

    def test_codex_provenance_text_is_rejected(self):
        text = (
            "---\nname: sample\ndescription: Use for sample tasks.\n---\n\n"
            "Adapted from upstream.\n"
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, _skill = self.make_sample_repository(root, text)
            self.assert_validation_error(manifest, "forbidden text", root)

    def test_forbidden_distribution_files_are_rejected(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root)
            (skill / "README.md").write_text("source history", encoding="utf-8")
            self.assert_validation_error(manifest, "contains forbidden file: README.md", root)

    def test_maintenance_executables_are_forbidden_in_distributions(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root)
            data = skill / "data"
            data.mkdir()
            (data / "_sync_all.py").write_text("print('maintenance')\n", encoding="utf-8")
            self.assert_validation_error(
                manifest,
                "contains forbidden maintenance executable: data/_sync_all.py",
                root,
            )

    def test_unreferenced_packaged_data_is_rejected(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root)
            data = skill / "data"
            data.mkdir()
            (data / "unused.csv").write_text("value\nunused\n", encoding="utf-8")
            self.assert_validation_error(
                manifest,
                "does not reference packaged data resource: data/unused.csv",
                root,
            )

    def test_referenced_and_dynamically_loaded_packaged_data_are_accepted(self):
        text = (
            "---\nname: sample\ndescription: Use for sample tasks.\n---\n\n"
            "Read runtime values from `data/used.csv`.\n"
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root, text)
            data = skill / "data"
            stacks = data / "stacks"
            stacks.mkdir(parents=True)
            (data / "used.csv").write_text("value\nused\n", encoding="utf-8")
            (stacks / "react.csv").write_text("value\nreact\n", encoding="utf-8")
            scripts = skill / "scripts"
            scripts.mkdir()
            (scripts / "reader.py").write_text(
                "from pathlib import Path\n"
                "list((Path(__file__).parent.parent / 'data' / 'stacks').glob('*.csv'))\n",
                encoding="utf-8",
            )
            self.assertEqual(self.installer.validate_manifest(manifest, root), [])

    def test_license_companions_are_legal_distribution_resources(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root)
            (skill / "LICENSE.txt").write_text("license terms\n", encoding="utf-8")
            self.assertEqual(self.installer.validate_manifest(manifest, root), [])

    def test_local_frontmatter_license_reference_must_exist_in_skill_root(self):
        text = (
            "---\n"
            "name: sample\n"
            "description: Use for sample tasks.\n"
            "license: Complete terms in LICENSE.txt\n"
            "---\n\n"
            "# Sample\n"
        )
        for agent in ("claude", "codex"):
            with self.subTest(agent=agent), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                manifest, _skill = self.make_sample_repository(root, text, agent=agent)
                self.assert_validation_error(
                    manifest,
                    f"{agent}/sample license references missing file: LICENSE.txt",
                    root,
                )

    def test_present_license_reference_and_literal_identifier_are_accepted(self):
        cases = (
            ("Complete terms in LICENSE.txt", True),
            ("MIT", False),
        )
        for license_value, create_file in cases:
            with self.subTest(license=license_value), TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                text = (
                    "---\n"
                    "name: sample\n"
                    "description: Use for sample tasks.\n"
                    f"license: {license_value}\n"
                    "---\n\n"
                    "# Sample\n"
                )
                manifest, skill = self.make_sample_repository(root, text, agent="claude")
                if create_file:
                    (skill / "LICENSE.txt").write_text("license terms\n", encoding="utf-8")
                self.assertEqual(self.installer.validate_manifest(manifest, root), [])

    def test_reference_filename_mention_without_markdown_link_is_rejected(self):
        text = (
            "---\nname: sample\ndescription: Use for sample tasks.\n---\n\n"
            "Read `references/guide.md` for details.\n"
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root, text)
            references = skill / "references"
            references.mkdir()
            (references / "guide.md").write_text("# Guide\n", encoding="utf-8")
            self.assert_validation_error(manifest, "does not link reference: guide.md", root)

    def test_nested_reference_directory_is_rejected(self):
        text = (
            "---\nname: sample\ndescription: Use for sample tasks.\n---\n\n"
            "Read the [guide](references/guide.md).\n"
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root, text)
            references = skill / "references"
            references.mkdir()
            (references / "guide.md").write_text("# Guide\n", encoding="utf-8")
            nested = references / "nested"
            nested.mkdir()
            (nested / "extra.md").write_text("# Extra\n", encoding="utf-8")
            self.assert_validation_error(manifest, "references must be one level deep", root)

    def test_direct_markdown_reference_link_with_fragment_is_accepted(self):
        text = (
            "---\nname: sample\ndescription: Use for sample tasks.\n---\n\n"
            "Read the [guide](./references/guide.md#usage).\n"
        )
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest, skill = self.make_sample_repository(root, text)
            references = skill / "references"
            references.mkdir()
            (references / "guide.md").write_text("# Guide\n", encoding="utf-8")
            self.assertEqual(self.installer.validate_manifest(manifest, root), [])

    def test_validate_cli_reports_invalid_manifest_without_traceback(self):
        stderr = io.StringIO()
        stdout = io.StringIO()
        with mock.patch.object(self.installer, "load_manifest", return_value=[]):
            with redirect_stderr(stderr), redirect_stdout(stdout):
                result = self.installer.main(["validate"])
        self.assertEqual(result, 1)
        self.assertIn("Error: manifest must be an object", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
