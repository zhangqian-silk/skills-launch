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
SUPPORTED_AGENTS = ("claude", "codex")
CODEX_FORBIDDEN_TEXT = (
    "Claude.ai",
    "model: opus",
    "create_file",
    "str_replace",
    ".claude/",
    "github.com",
    "Adapted from",
    "ADAPTATIONS.md",
    "originals/",
)
FORBIDDEN_DISTRIBUTION_FILES = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
    "ADAPTATION.md",
    "source-context.md",
}


class SkillLaunchError(Exception):
    pass


def load_manifest():
    with MANIFEST_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_source(manifest, name):
    for source in manifest["sources"]:
        if source["name"] == name:
            return source
    available = ", ".join(source["name"] for source in manifest["sources"])
    raise SkillLaunchError(f"Unknown source '{name}'. Available sources: {available}")


def get_distribution(manifest, agent, name):
    if agent not in SUPPORTED_AGENTS:
        raise SkillLaunchError(f"Unsupported agent '{agent}'. Choose: {', '.join(SUPPORTED_AGENTS)}")
    entries = manifest["distributions"][agent]
    for entry in entries:
        if entry["name"] == name or name in entry.get("aliases", []):
            return entry
    available = ", ".join(entry["name"] for entry in entries)
    raise SkillLaunchError(f"Unknown {agent} skill '{name}'. Available skills: {available}")


def repository_path(relative):
    path = (REPOSITORY_ROOT / relative).resolve()
    root = REPOSITORY_ROOT.resolve()
    if path != root and root not in path.parents:
        raise SkillLaunchError(f"Repository path escapes the repository: {relative}")
    return path


def frontmatter_keys(text):
    if not text.startswith("---\n"):
        return []
    end = text.find("\n---\n", 4)
    if end < 0:
        return []
    return [
        line.split(":", 1)[0].strip()
        for line in text[4:end].splitlines()
        if ":" in line and not line.startswith((" ", "\t"))
    ]


def resolve_within(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise SkillLaunchError(f"path escapes repository: {relative}")
    return path


def validate_manifest(manifest, root=REPOSITORY_ROOT):
    errors = []
    if manifest.get("version") != 2:
        errors.append("manifest version must be 2")
    sources = manifest.get("sources", [])
    source_names = [source.get("name") for source in sources]
    if len(source_names) != len(set(source_names)):
        errors.append("source names must be unique")
    source_set = set(source_names)
    for source in sources:
        for field in ("name", "source", "original"):
            if not source.get(field):
                errors.append(f"source is missing {field}: {source.get('name', '<unknown>')}")
        source_spec = source.get("source", {})
        for field in ("kind", "repo", "ref", "path"):
            if field not in source_spec:
                errors.append(f"{source.get('name', '<unknown>')} source is missing {field}")
        if source_spec.get("kind") not in {"github_file", "github_dir"}:
            errors.append(f"unsupported source kind: {source_spec.get('kind')}")
        try:
            original = resolve_within(root, source.get("original", ""))
        except SkillLaunchError as error:
            errors.append(str(error))
            continue
        if not original.is_dir():
            errors.append(f"missing original directory: {source.get('original')}")

    distributions = manifest.get("distributions", {})
    if set(distributions) != set(SUPPORTED_AGENTS):
        errors.append("distributions must contain exactly claude and codex")
    for agent in SUPPORTED_AGENTS:
        entries = distributions.get(agent, [])
        names = [entry.get("name") for entry in entries]
        if len(names) != len(set(names)):
            errors.append(f"{agent} distribution names must be unique")
        aliases = [alias for entry in entries for alias in entry.get("aliases", [])]
        if set(names) & set(aliases) or len(aliases) != len(set(aliases)):
            errors.append(f"{agent} aliases must be unique and not shadow names")
        for entry in entries:
            name = entry.get("name", "<unknown>")
            unknown = set(entry.get("sources", [])) - source_set
            if unknown:
                errors.append(f"{agent}/{name} references unknown source: {', '.join(sorted(unknown))}")
            try:
                path = resolve_within(root, entry.get("path", ""))
            except SkillLaunchError as error:
                errors.append(str(error))
                continue
            if not path.is_dir() or not (path / "SKILL.md").is_file():
                errors.append(f"missing distribution skill: {agent}/{name}")
                continue
            if path.name != name:
                errors.append(f"{agent}/{name} directory name must match skill name")
            for dependency in entry.get("dependencies", []):
                missing = {"command", "install", "verify"} - set(dependency)
                if missing:
                    errors.append(f"{agent}/{name} dependency is missing: {', '.join(sorted(missing))}")
            for forbidden_file in FORBIDDEN_DISTRIBUTION_FILES:
                if (path / forbidden_file).exists():
                    errors.append(f"{agent}/{name} contains forbidden file: {forbidden_file}")
            text = (path / "SKILL.md").read_text(encoding="utf-8")
            if agent == "codex":
                if frontmatter_keys(text) != ["name", "description"]:
                    errors.append(f"{agent}/{name} frontmatter must contain only name and description")
                if len(text.splitlines()) > 250:
                    errors.append(f"{agent}/{name} SKILL.md exceeds 250 lines")
                for forbidden in CODEX_FORBIDDEN_TEXT:
                    if forbidden in text:
                        errors.append(f"{agent}/{name} contains forbidden text: {forbidden}")
            references = path / "references"
            if references.is_dir():
                if any(child.is_dir() for child in references.iterdir()):
                    errors.append(f"{agent}/{name} references must be one level deep")
                for reference in references.iterdir():
                    if reference.is_file() and reference.name not in text:
                        errors.append(f"{agent}/{name} does not link reference: {reference.name}")
    return errors


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


def default_target_dir(agent):
    if os.environ.get("AGENT_SKILLS_DIR"):
        return Path(os.environ["AGENT_SKILLS_DIR"])
    if agent == "codex":
        if os.environ.get("CODEX_HOME"):
            return Path(os.environ["CODEX_HOME"]) / "skills"
        return Path.home() / ".agents" / "skills"
    if os.environ.get("CLAUDE_HOME"):
        return Path(os.environ["CLAUDE_HOME"]) / "skills"
    return Path.home() / ".claude" / "skills"


def copy_directory_atomic(source, destination, force=False):
    source = Path(source)
    destination = Path(destination)
    if not source.is_dir():
        raise SkillLaunchError(f"Cannot find distribution directory: {source}")
    if destination.exists() and not force:
        raise SkillLaunchError(f"Target already exists: {destination}. Re-run with --force to replace it.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{destination.name}-", dir=destination.parent) as temp_dir:
        staged = Path(temp_dir) / "payload"
        shutil.copytree(source, staged)
        backup = Path(temp_dir) / "previous"
        had_previous = destination.exists()
        try:
            if had_previous:
                destination.rename(backup)
            staged.rename(destination)
        except Exception:
            if had_previous and backup.exists() and not destination.exists():
                backup.rename(destination)
            raise


def report_dependencies(entry):
    for dependency in entry.get("dependencies", []):
        if shutil.which(dependency["command"]):
            continue
        print(f"Warning: '{entry['name']}' requires missing command '{dependency['command']}'.", file=sys.stderr)
        print(f"Install: {dependency['install']}", file=sys.stderr)
        print(f"Verify: {dependency['verify']}", file=sys.stderr)


def install_skill(args):
    manifest = load_manifest()
    entry = get_distribution(manifest, args.agent, args.name)
    target_dir = Path(args.target_dir) if args.target_dir else default_target_dir(args.agent)
    destination = target_dir / entry["name"]
    source = repository_path(entry["path"])

    copy_directory_atomic(source, destination, force=args.force)
    report_dependencies(entry)
    print(f"Installed '{entry['name']}' for {args.agent} from local distribution to {destination}")


def install_all(args):
    manifest = load_manifest()
    target_dir = Path(args.target_dir) if args.target_dir else default_target_dir(args.agent)
    for entry in manifest["distributions"][args.agent]:
        install_skill(
            argparse.Namespace(
                name=entry["name"],
                agent=args.agent,
                target_dir=str(target_dir),
                force=args.force,
            )
        )


def sync_upstreams(args):
    manifest = load_manifest()
    names = args.names or [source["name"] for source in manifest["sources"]]
    failures = []

    for name in names:
        source = get_source(manifest, name)
        destination = repository_path(source["original"])
        with tempfile.TemporaryDirectory(prefix="skills-launch-sync-") as temp_dir:
            temp_source = Path(temp_dir) / source["name"]
            print(f"Syncing {source['name']} from {source['source']['repo']}:{source['source'].get('path', '')}")
            try:
                save_github_source(source["source"], temp_source)
                if not temp_source.is_dir() or not any(temp_source.iterdir()):
                    raise SkillLaunchError(f"Downloaded source '{source['name']}' was empty.")
                copy_directory_atomic(temp_source, destination, force=True)
            except SkillLaunchError as error:
                failures.append(
                    f"Failed to sync '{source['name']}' from {source['source']['repo']}:"
                    f"{source['source'].get('path', '')}: {error}"
                )

    if failures:
        for failure in failures:
            print(f"Warning: {failure}", file=sys.stderr)
        raise SkillLaunchError(
            f"Sync finished with {len(failures)} failure(s). Existing originals were preserved for failed entries."
        )

    print(f"Synced {len(names)} skill source(s).")


def validate(_args):
    manifest = load_manifest()
    errors = validate_manifest(manifest, REPOSITORY_ROOT)

    if errors:
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1

    distributions = manifest["distributions"]
    print(
        f"Validated {len(manifest.get('sources', []))} sources, "
        f"{len(distributions['claude'])} Claude skills, and "
        f"{len(distributions['codex'])} Codex skills."
    )
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="Install and maintain the skills-launch catalog.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install one agent-specific local skill distribution.")
    install_parser.add_argument("name")
    install_parser.add_argument("--agent", choices=SUPPORTED_AGENTS, required=True)
    install_parser.add_argument("--target-dir")
    install_parser.add_argument("--force", action="store_true")
    install_parser.set_defaults(func=install_skill)

    install_all_parser = subparsers.add_parser("install-all", help="Install every distribution for one agent.")
    install_all_parser.add_argument("--agent", choices=SUPPORTED_AGENTS, required=True)
    install_all_parser.add_argument("--target-dir")
    install_all_parser.add_argument("--force", action="store_true")
    install_all_parser.set_defaults(func=install_all)

    sync_parser = subparsers.add_parser("sync", help="Sync original source copies from upstream.")
    sync_parser.add_argument("names", nargs="*")
    sync_parser.set_defaults(func=sync_upstreams)

    validate_parser = subparsers.add_parser("validate", help="Validate sources and agent distributions.")
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
