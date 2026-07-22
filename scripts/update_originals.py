#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path
from typing import NamedTuple


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPOSITORY_ROOT / "skills.json"
USER_AGENT = "skills-launch"


class UpdateError(Exception):
    pass


class ChangeSet(NamedTuple):
    changed: bool
    added: tuple[str, ...]
    modified: tuple[str, ...]
    deleted: tuple[str, ...]


def load_manifest(path=MANIFEST_PATH):
    with Path(path).open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if not isinstance(manifest.get("sources"), list):
        raise UpdateError("skills.json must contain a sources list")
    if not isinstance(manifest.get("skills"), list):
        raise UpdateError("skills.json must contain a skills list")
    return manifest


def get_source(manifest, name):
    for source in manifest["sources"]:
        if source.get("name") == name:
            return source
    available = ", ".join(source["name"] for source in manifest["sources"])
    raise UpdateError(f"Unknown original '{name}'. Available: {available}")


def affected_skills(manifest, source_name):
    return [
        (skill["name"], skill["path"])
        for skill in manifest["skills"]
        if source_name in skill.get("sources", [])
    ]


def original_path(source, root=REPOSITORY_ROOT):
    name = source.get("name")
    expected = f"originals/{name}"
    if source.get("original") != expected:
        raise UpdateError(f"Original '{name}' path must be exactly {expected}")
    path = Path(root) / "originals" / name
    if path.is_symlink():
        raise UpdateError(f"Refusing to replace symlinked original: {path}")
    return path


def tree_snapshot(path):
    path = Path(path)
    if not path.is_dir():
        return {}
    snapshot = {}
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file():
            continue
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        executable = bool(candidate.stat().st_mode & 0o111)
        snapshot[candidate.relative_to(path).as_posix()] = (digest, executable)
    return snapshot


def compare_snapshots(before, after):
    before_names = set(before)
    after_names = set(after)
    added = tuple(sorted(after_names - before_names))
    deleted = tuple(sorted(before_names - after_names))
    modified = tuple(sorted(name for name in before_names & after_names if before[name] != after[name]))
    return ChangeSet(bool(added or modified or deleted), added, modified, deleted)


def request_to_file(url, destination):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with Path(destination).open("wb") as output:
                shutil.copyfileobj(response, output)
    except Exception as error:
        raise UpdateError(f"Failed to download {url}: {error}") from error


def extract_github_archive(spec, destination):
    repo = spec["repo"]
    ref = urllib.parse.quote(spec["ref"], safe="")
    source_path = Path(*spec["path"].split("/")) if spec.get("path") else Path()
    with tempfile.TemporaryDirectory(prefix="skills-update-archive-") as temp_dir:
        temp = Path(temp_dir)
        archive_path = temp / "source.zip"
        extract_root = temp / "source"
        request_to_file(f"https://codeload.github.com/{repo}/zip/{ref}", archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(extract_root)
            for member in archive.infolist():
                permissions = (member.external_attr >> 16) & 0o777
                extracted = extract_root / member.filename
                if permissions and extracted.exists():
                    extracted.chmod(permissions)

        roots = [entry for entry in extract_root.iterdir() if entry.is_dir()]
        if len(roots) != 1:
            raise UpdateError(f"Unexpected archive layout for {repo}@{spec['ref']}")
        source = roots[0] / source_path
        if not source.is_dir():
            raise UpdateError(f"Archive does not contain {spec['path']}")
        shutil.copytree(source, destination)


def save_github_source(source, destination):
    spec = source.get("source", {})
    kind = spec.get("kind")
    if kind == "github_dir":
        extract_github_archive(spec, destination)
        return
    if kind == "github_file":
        destination = Path(destination)
        destination.mkdir(parents=True)
        raw_path = "/".join(urllib.parse.quote(part) for part in spec["path"].split("/"))
        raw_url = f"https://raw.githubusercontent.com/{spec['repo']}/{spec['ref']}/{raw_path}"
        request_to_file(raw_url, destination / Path(spec["path"]).name)
        return
    raise UpdateError(f"Unsupported source kind for {source.get('name')}: {kind}")


def replace_directory(source, destination):
    source = Path(source)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{destination.name}-update-",
        dir=destination.parent,
    ) as temp_dir:
        temp = Path(temp_dir)
        staged = temp / "staged"
        backup = temp / "previous"
        shutil.copytree(source, staged)
        had_previous = destination.exists()
        try:
            if had_previous:
                destination.rename(backup)
            staged.rename(destination)
        except Exception:
            if had_previous and backup.exists() and not destination.exists():
                backup.rename(destination)
            raise


def update_original(source, root=REPOSITORY_ROOT, fetcher=save_github_source):
    destination = original_path(source, root)
    before = tree_snapshot(destination)
    with tempfile.TemporaryDirectory(prefix=f"skills-update-{source['name']}-") as temp_dir:
        downloaded = Path(temp_dir) / source["name"]
        fetcher(source, downloaded)
        if not downloaded.is_dir() or not any(downloaded.iterdir()):
            raise UpdateError(f"Downloaded original '{source['name']}' is empty")
        result = compare_snapshots(before, tree_snapshot(downloaded))
        if result.changed:
            replace_directory(downloaded, destination)
        return result


def has_local_changes(source, root=REPOSITORY_ROOT):
    root = Path(root)
    if not (root / ".git").exists():
        return False
    relative = source["original"]
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--", relative],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise UpdateError(completed.stderr.strip() or "git status failed")
    return bool(completed.stdout.strip())


def print_result(source, result, manifest):
    name = source["name"]
    if not result.changed:
        print(f"{name}: no upstream changes")
        return

    print(
        f"{name}: updated originals "
        f"(+{len(result.added)} ~{len(result.modified)} -{len(result.deleted)})"
    )
    for label, paths in (("added", result.added), ("modified", result.modified), ("deleted", result.deleted)):
        for path in paths:
            print(f"  {label}: {path}")

    impacted = affected_skills(manifest, name)
    if impacted:
        print("  maintained skills to review:")
        for skill_name, path in impacted:
            print(f"    - {skill_name}: {path}")
    else:
        print("  maintained skills to review: none")
    print(f"  review: git diff -- {source['original']}")
    print("  skills/ was not modified; adapt changes manually after review")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Update checked-in originals and report maintained Skills affected by upstream changes."
    )
    parser.add_argument("names", nargs="*", help="Original names; omit to update every source.")
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest()
        names = args.names or [source["name"] for source in manifest["sources"]]
        sources = [get_source(manifest, name) for name in names]
        dirty = [source["name"] for source in sources if has_local_changes(source)]
        if dirty:
            raise UpdateError(
                "Commit or discard local original changes before updating: " + ", ".join(dirty)
            )

        failures = []
        for source in sources:
            try:
                result = update_original(source)
                print_result(source, result, manifest)
            except Exception as error:
                failures.append(f"{source['name']}: {error}")
        if failures:
            for failure in failures:
                print(f"Error: {failure}", file=sys.stderr)
            return 1
        return 0
    except (UpdateError, KeyError, TypeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
