#!/usr/bin/env python3
import argparse
import json
import os
import re
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


def parse_scalar(value):
    value = value.strip()
    if not value:
        return None
    if value.startswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value.lower() in {"null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def parse_frontmatter(text):
    if not text.startswith("---\n"):
        return [], {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return [], {}
    keys = []
    values = {}
    for line in text[4:end].splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        keys.append(key)
        values[key] = parse_scalar(raw_value)
    return keys, values


def frontmatter_keys(text):
    keys, _values = parse_frontmatter(text)
    return keys


def is_non_empty_string(value):
    return isinstance(value, str) and bool(value.strip())


def has_markdown_reference_link(text, filename):
    reference = rf"(?:\./)?references/{re.escape(filename)}"
    pattern = rf"(?<!!)\[[^\]\n]*\]\(\s*{reference}(?:#[^)\s]*)?\s*\)"
    return re.search(pattern, text) is not None


def resolve_within(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path != root and root not in path.parents:
        raise SkillLaunchError(f"path escapes repository: {relative}")
    return path


def validate_manifest(manifest, root=REPOSITORY_ROOT):
    errors = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]

    if manifest.get("version") != 2:
        errors.append("manifest version must be 2")

    sources_value = manifest.get("sources")
    if not isinstance(sources_value, list):
        errors.append("sources must be a list")
        sources = []
    else:
        sources = sources_value

    source_names = []
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue

        name = source.get("name")
        if not is_non_empty_string(name):
            errors.append(f"{label}.name must be a non-empty string")
        else:
            source_names.append(name)

        original_value = source.get("original")
        if not is_non_empty_string(original_value):
            errors.append(f"{label}.original must be a non-empty string")
        else:
            try:
                original = resolve_within(root, original_value)
                if not original.is_dir():
                    errors.append(f"missing original directory: {original_value}")
            except SkillLaunchError as error:
                errors.append(str(error))
            except (OSError, RuntimeError, ValueError) as error:
                errors.append(f"invalid original path {original_value!r}: {error}")

        source_spec = source.get("source")
        if not isinstance(source_spec, dict):
            errors.append(f"{label}.source must be an object")
            continue
        for field in ("kind", "repo", "ref", "path"):
            if not is_non_empty_string(source_spec.get(field)):
                errors.append(f"{label}.source.{field} must be a non-empty string")
        kind = source_spec.get("kind")
        if is_non_empty_string(kind) and kind not in {"github_file", "github_dir"}:
            errors.append(f"unsupported source kind: {kind}")

    if len(source_names) != len(set(source_names)):
        errors.append("source names must be unique")
    source_set = set(source_names)

    distributions_value = manifest.get("distributions")
    if not isinstance(distributions_value, dict):
        errors.append("distributions must be an object")
        distributions = {}
    else:
        distributions = distributions_value
    if isinstance(distributions_value, dict) and set(distributions) != set(SUPPORTED_AGENTS):
        errors.append("distributions must contain exactly claude and codex")

    for agent in SUPPORTED_AGENTS:
        entries_value = distributions.get(agent, [])
        if not isinstance(entries_value, list):
            errors.append(f"distributions.{agent} must be a list")
            entries = []
        else:
            entries = entries_value

        names = []
        aliases = []
        for index, entry in enumerate(entries):
            label = f"distributions.{agent}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{label} must be an object")
                continue

            name_value = entry.get("name")
            valid_name = is_non_empty_string(name_value)
            if not valid_name:
                errors.append(f"{label}.name must be a non-empty string")
                name = "<unknown>"
            else:
                name = name_value
                names.append(name)

            aliases_value = entry.get("aliases", [])
            if not isinstance(aliases_value, list):
                errors.append(f"{label}.aliases must be a list")
            else:
                for alias_index, alias in enumerate(aliases_value):
                    if not is_non_empty_string(alias):
                        errors.append(
                            f"{label}.aliases[{alias_index}] must be a non-empty string"
                        )
                    else:
                        aliases.append(alias)

            mapped_sources_value = entry.get("sources")
            mapped_sources = []
            if not isinstance(mapped_sources_value, list):
                errors.append(f"{label}.sources must be a list")
            elif not mapped_sources_value:
                errors.append(f"{label}.sources must not be empty")
            else:
                for source_index, source_name in enumerate(mapped_sources_value):
                    if not is_non_empty_string(source_name):
                        errors.append(
                            f"{label}.sources[{source_index}] must be a non-empty string"
                        )
                    else:
                        mapped_sources.append(source_name)
                unknown = set(mapped_sources) - source_set
                if unknown:
                    errors.append(
                        f"{agent}/{name} references unknown source: {', '.join(sorted(unknown))}"
                    )

            dependencies_value = entry.get("dependencies", [])
            if not isinstance(dependencies_value, list):
                errors.append(f"{label}.dependencies must be a list")
            else:
                for dependency_index, dependency in enumerate(dependencies_value):
                    dependency_label = f"{label}.dependencies[{dependency_index}]"
                    if not isinstance(dependency, dict):
                        errors.append(f"{dependency_label} must be an object")
                        continue
                    for field in ("command", "install", "verify"):
                        if not is_non_empty_string(dependency.get(field)):
                            errors.append(
                                f"{dependency_label}.{field} must be a non-empty string"
                            )

            path_value = entry.get("path")
            if not is_non_empty_string(path_value):
                errors.append(f"{label}.path must be a non-empty string")
                continue
            try:
                path = resolve_within(root, path_value)
            except SkillLaunchError as error:
                errors.append(str(error))
                continue
            except (OSError, RuntimeError, ValueError) as error:
                errors.append(f"invalid distribution path {path_value!r}: {error}")
                continue
            try:
                if not path.is_dir() or not (path / "SKILL.md").is_file():
                    errors.append(f"missing distribution skill: {agent}/{name}")
                    continue
                if not valid_name or path.name != name:
                    errors.append(f"{agent}/{name} directory name must match skill name")
                for forbidden_file in FORBIDDEN_DISTRIBUTION_FILES:
                    if (path / forbidden_file).exists():
                        errors.append(f"{agent}/{name} contains forbidden file: {forbidden_file}")
                text = (path / "SKILL.md").read_text(encoding="utf-8")
            except (OSError, UnicodeError, ValueError) as error:
                errors.append(f"cannot inspect distribution skill {agent}/{name}: {error}")
                continue

            if agent == "codex":
                frontmatter_names, frontmatter = parse_frontmatter(text)
                if frontmatter_names != ["name", "description"]:
                    errors.append(f"{agent}/{name} frontmatter must contain only name and description")
                frontmatter_name = frontmatter.get("name")
                if (
                    not is_non_empty_string(frontmatter_name)
                    or frontmatter_name != name
                    or frontmatter_name != path.name
                ):
                    errors.append(
                        f"{agent}/{name} frontmatter name must match manifest entry and directory name"
                    )
                if not is_non_empty_string(frontmatter.get("description")):
                    errors.append(f"{agent}/{name} description must be a non-empty string")
                if len(text.splitlines()) > 250:
                    errors.append(f"{agent}/{name} SKILL.md exceeds 250 lines")
                for forbidden in CODEX_FORBIDDEN_TEXT:
                    if forbidden in text:
                        errors.append(f"{agent}/{name} contains forbidden text: {forbidden}")

            references = path / "references"
            try:
                if references.is_dir():
                    children = list(references.iterdir())
                    if any(child.is_dir() for child in children):
                        errors.append(f"{agent}/{name} references must be one level deep")
                    for reference in children:
                        if reference.is_file() and not has_markdown_reference_link(
                            text, reference.name
                        ):
                            errors.append(
                                f"{agent}/{name} does not link reference: {reference.name}"
                            )
            except (OSError, ValueError) as error:
                errors.append(f"cannot inspect references for {agent}/{name}: {error}")

        if len(names) != len(set(names)):
            errors.append(f"{agent} distribution names must be unique")
        if set(names) & set(aliases) or len(aliases) != len(set(aliases)):
            errors.append(f"{agent} aliases must be unique and not shadow names")
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
