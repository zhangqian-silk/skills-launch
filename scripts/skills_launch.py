#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "skills.json"
USER_AGENT = "skills-launch"


class SkillLaunchError(Exception):
    pass


def load_manifest():
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_skill(manifest, name):
    for skill in manifest["skills"]:
        aliases = skill.get("aliases", [])
        if skill["name"] == name or name in aliases:
            return skill
    available = ", ".join(skill["name"] for skill in manifest["skills"])
    raise SkillLaunchError(f"Unknown skill '{name}'. Available skills: {available}")


def request_url(url, *, output_path=None, expect_json=False):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if output_path:
                with output_path.open("wb") as handle:
                    shutil.copyfileobj(response, handle)
                return None
            data = response.read()
    except urllib.error.HTTPError as error:
        raise SkillLaunchError(f"{url} returned HTTP {error.code}") from error
    except urllib.error.URLError as error:
        raise SkillLaunchError(f"{url} failed: {error.reason}") from error

    if expect_json:
        return json.loads(data.decode("utf-8"))
    return data


def copy_directory_clean(source, destination):
    source = Path(source)
    destination = Path(destination)
    if not source.exists():
        raise SkillLaunchError(f"Cannot find source directory: {source}")
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def clean_directory(path):
    path = Path(path)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def github_contents_url(repo, ref, path):
    base = f"https://api.github.com/repos/{repo}/contents"
    if path:
        encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
        base = f"{base}/{encoded_path}"
    return f"{base}?ref={urllib.parse.quote(ref)}"


def save_github_directory_via_api(repo, ref, path, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    items = request_url(github_contents_url(repo, ref, path), expect_json=True)
    if isinstance(items, dict):
        items = [items]

    for item in items:
        target_path = destination / item["name"]
        if item["type"] == "dir":
            save_github_directory_via_api(repo, ref, item["path"], target_path)
        elif item["type"] == "file":
            request_url(item["download_url"], output_path=target_path)


def run_git(arguments):
    completed = subprocess.run(
        ["git", *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        output = completed.stdout.strip()
        raise SkillLaunchError(f"git {' '.join(arguments)} failed: {output}")


def save_github_directory_via_git(repo, ref, path, destination):
    if not path:
        raise SkillLaunchError("Sparse checkout requires a non-empty path.")

    with tempfile.TemporaryDirectory(prefix="skills-launch-git-") as temp_dir:
        temp_path = Path(temp_dir)
        run_git(["-C", str(temp_path), "init"])
        run_git(["-C", str(temp_path), "remote", "add", "origin", f"https://github.com/{repo}.git"])
        run_git(["-C", str(temp_path), "sparse-checkout", "init", "--cone"])
        run_git(["-C", str(temp_path), "sparse-checkout", "set", path])
        run_git(["-C", str(temp_path), "pull", "--depth=1", "origin", ref])
        copy_directory_clean(temp_path / Path(*path.split("/")), destination)


def save_github_directory_via_zip(repo, ref, path, destination):
    with tempfile.TemporaryDirectory(prefix="skills-launch-zip-") as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "source.zip"
        extract_root = temp_path / "source"
        zip_ref = urllib.parse.quote(ref, safe="")
        request_url(f"https://codeload.github.com/{repo}/zip/{zip_ref}", output_path=zip_path)

        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_root)
            for member in archive.infolist():
                permissions = (member.external_attr >> 16) & 0o777
                extracted_path = extract_root / member.filename
                if permissions and extracted_path.exists():
                    extracted_path.chmod(permissions)

        roots = [entry for entry in extract_root.iterdir() if entry.is_dir()]
        if not roots:
            raise SkillLaunchError("Downloaded archive did not contain a repository root.")

        source_directory = roots[0] if not path else roots[0] / Path(*path.split("/"))
        copy_directory_clean(source_directory, destination)


def save_github_source(source, destination):
    destination = Path(destination)
    clean_directory(destination)

    if source["kind"] == "github_file":
        raw_path = "/".join(urllib.parse.quote(part) for part in source["path"].split("/"))
        raw_url = f"https://raw.githubusercontent.com/{source['repo']}/{source['ref']}/{raw_path}"
        request_url(raw_url, output_path=destination / Path(source["path"]).name)
        return

    if source["kind"] == "github_dir":
        if not source.get("path"):
            save_github_directory_via_zip(source["repo"], source["ref"], "", destination)
            return

        try:
            save_github_directory_via_api(source["repo"], source["ref"], source.get("path", ""), destination)
            return
        except SkillLaunchError as api_error:
            print(
                f"Warning: GitHub contents API failed for {source['repo']}:{source.get('path', '')}. "
                f"Trying git sparse checkout. {api_error}",
                file=sys.stderr,
            )

        try:
            save_github_directory_via_git(source["repo"], source["ref"], source.get("path", ""), destination)
            return
        except SkillLaunchError as git_error:
            print(
                f"Warning: git sparse checkout failed for {source['repo']}:{source.get('path', '')}. "
                f"Trying repository archive. {git_error}",
                file=sys.stderr,
            )

        save_github_directory_via_zip(source["repo"], source["ref"], source.get("path", ""), destination)
        return

    raise SkillLaunchError(f"Unsupported source kind: {source['kind']}")


def default_target_dir(package_type):
    home = Path.home()
    if package_type in {"claude_plugin", "skill_suite"}:
        if package_type == "skill_suite" and os.environ.get("AGENT_SUITES_DIR"):
            return Path(os.environ["AGENT_SUITES_DIR"])
        if os.environ.get("AGENT_PLUGINS_DIR"):
            return Path(os.environ["AGENT_PLUGINS_DIR"])
        if os.environ.get("CLAUDE_HOME"):
            return Path(os.environ["CLAUDE_HOME"]) / "plugins"
        if os.environ.get("CODEX_HOME"):
            return Path(os.environ["CODEX_HOME"]) / "plugins"
        return home / ".codex" / "plugins"

    if os.environ.get("AGENT_SKILLS_DIR"):
        return Path(os.environ["AGENT_SKILLS_DIR"])
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]) / "skills"
    return home / ".codex" / "skills"


def install_skill(args):
    manifest = load_manifest()
    skill = get_skill(manifest, args.name)
    target_dir = Path(args.target_dir) if args.target_dir else default_target_dir(skill.get("package_type", "skill"))
    destination = target_dir / skill["name"]

    if destination.exists() and not args.force:
        raise SkillLaunchError(f"Target already exists: {destination}. Re-run with --force to replace it.")

    installed_from = "fallback"
    with tempfile.TemporaryDirectory(prefix="skills-launch-") as temp_dir:
        upstream_directory = Path(temp_dir) / skill["name"]
        if not args.use_fallback_only:
            try:
                save_github_source(skill["source"], upstream_directory)
                copy_directory_clean(upstream_directory, destination)
                installed_from = "upstream"
            except SkillLaunchError as error:
                print(
                    f"Warning: Could not install '{skill['name']}' from upstream "
                    f"{skill['source']['repo']}:{skill['source'].get('path', '')}. {error}",
                    file=sys.stderr,
                )
                copy_directory_clean(REPOSITORY_ROOT / skill["fallback"], destination)
        else:
            copy_directory_clean(REPOSITORY_ROOT / skill["fallback"], destination)

    print(f"Installed '{skill['name']}' ({skill.get('package_type', 'skill')}) from {installed_from} to {destination}")


def install_all(args):
    manifest = load_manifest()
    skills = manifest["skills"]
    if args.package_type != "all":
        skills = [skill for skill in skills if skill.get("package_type", "skill") == args.package_type]

    for skill in skills:
        if skill.get("package_type") == "claude_plugin":
            target_dir = args.plugins_dir or str(default_target_dir("claude_plugin"))
        elif skill.get("package_type") == "skill_suite":
            target_dir = args.suites_dir or str(default_target_dir("skill_suite"))
        else:
            target_dir = args.skills_dir or str(default_target_dir("skill"))
        install_skill(
            argparse.Namespace(
                name=skill["name"],
                target_dir=target_dir,
                force=args.force,
                use_fallback_only=args.use_fallback_only,
            )
        )


def sync_upstreams(args):
    manifest = load_manifest()
    names = args.names or [skill["name"] for skill in manifest["skills"]]
    failures = []

    for name in names:
        skill = get_skill(manifest, name)
        destination = REPOSITORY_ROOT / skill["fallback"]
        with tempfile.TemporaryDirectory(prefix="skills-launch-sync-") as temp_dir:
            temp_skill = Path(temp_dir) / skill["name"]
            print(f"Syncing {skill['name']} from {skill['source']['repo']}:{skill['source'].get('path', '')}")
            try:
                save_github_source(skill["source"], temp_skill)
                copy_directory_clean(temp_skill, destination)
            except SkillLaunchError as error:
                failures.append(
                    f"Failed to sync '{skill['name']}' from {skill['source']['repo']}:"
                    f"{skill['source'].get('path', '')}: {error}"
                )

    if failures:
        for failure in failures:
            print(f"Warning: {failure}", file=sys.stderr)
        raise SkillLaunchError(
            f"Sync finished with {len(failures)} failure(s). Existing fallback copies were preserved for failed entries."
        )

    print(f"Synced {len(names)} skill source(s).")


def validate(_args):
    manifest = load_manifest()
    errors = []
    names = set()

    for skill in manifest["skills"]:
        name = skill.get("name")
        if not name:
            errors.append("A manifest entry is missing name.")
            continue
        if name in names:
            errors.append(f"Duplicate skill name: {name}")
        names.add(name)

        package_type = skill.get("package_type")
        if package_type not in {"skill", "claude_plugin", "skill_suite"}:
            errors.append(f"{name}: package_type must be skill, claude_plugin, or skill_suite.")

        source = skill.get("source") or {}
        for field in ("kind", "repo", "ref"):
            if not source.get(field):
                errors.append(f"{name}: source.{field} is required.")
        if source.get("kind") not in {"github_file", "github_dir"}:
            errors.append(f"{name}: source.kind must be github_file or github_dir.")

        fallback = skill.get("fallback")
        if not fallback:
            errors.append(f"{name}: fallback is required.")
            continue

        fallback_path = REPOSITORY_ROOT / fallback
        if not fallback_path.exists():
            errors.append(f"{name}: fallback directory does not exist: {fallback}")
            continue

        if package_type == "skill" and not (fallback_path / "SKILL.md").exists():
            errors.append(f"{name}: skill fallback is missing SKILL.md.")
        if package_type == "claude_plugin" and not (fallback_path / ".claude-plugin" / "plugin.json").exists():
            errors.append(f"{name}: Claude plugin fallback is missing .claude-plugin/plugin.json.")
        if package_type == "skill_suite" and not (fallback_path / ".codex-plugin" / "plugin.json").exists():
            errors.append(f"{name}: skill suite fallback is missing .codex-plugin/plugin.json.")

    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(manifest['skills'])} manifest entries.")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Install and maintain the skills-launch catalog.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install one skill, plugin, or skill suite.")
    install_parser.add_argument("name")
    install_parser.add_argument("--target-dir")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--use-fallback-only", action="store_true")
    install_parser.set_defaults(func=install_skill)

    install_all_parser = subparsers.add_parser("install-all", help="Install every listed entry.")
    install_all_parser.add_argument("--skills-dir")
    install_all_parser.add_argument("--plugins-dir")
    install_all_parser.add_argument("--suites-dir")
    install_all_parser.add_argument(
        "--package-type",
        choices=("all", "skill", "claude_plugin", "skill_suite"),
        default="all",
    )
    install_all_parser.add_argument("--force", action="store_true")
    install_all_parser.add_argument("--use-fallback-only", action="store_true")
    install_all_parser.set_defaults(func=install_all)

    sync_parser = subparsers.add_parser("sync", help="Sync fallback copies from upstream.")
    sync_parser.add_argument("names", nargs="*")
    sync_parser.set_defaults(func=sync_upstreams)

    validate_parser = subparsers.add_parser("validate", help="Validate manifest and fallback copies.")
    validate_parser.set_defaults(func=validate)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except SkillLaunchError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return result or 0


if __name__ == "__main__":
    raise SystemExit(main())
