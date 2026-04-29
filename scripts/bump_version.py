#!/usr/bin/env python3
"""Bump mnemo version across all tracked locations and optionally create a git commit/tag.

Usage:
    python3 scripts/bump_version.py 0.8.0
    python3 scripts/bump_version.py 0.8.0 --commit
    python3 scripts/bump_version.py 0.8.0 --commit --tag
    python3 scripts/bump_version.py 0.8.0 --commit --tag --push
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent
PLUGIN_MANIFESTS = (
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".codex-plugin" / "plugin.json",
)


def current_version() -> str:
    versions = {
        path.relative_to(ROOT).as_posix(): json.loads(path.read_text(encoding="utf-8"))["version"]
        for path in PLUGIN_MANIFESTS
    }
    distinct = set(versions.values())
    if len(distinct) != 1:
        details = ", ".join(f"{name}={version}" for name, version in versions.items())
        sys.exit(f"error: plugin manifest versions are out of sync: {details}")
    return next(iter(distinct))


def bump_plugin_json(path: Path, new: str) -> Path:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["version"] = new
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def bump_readme(old: str, new: str) -> Path:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    updated = text.replace(
        f"https://img.shields.io/badge/version-{old}-blue",
        f"https://img.shields.io/badge/version-{new}-blue",
    )
    if updated == text:
        print(f"  [warn] README.md badge not found for {old}")
    path.write_text(updated, encoding="utf-8")
    return path


def bump_skills(old: str, new: str) -> list[Path]:
    changed = []
    for skill_file in sorted(ROOT.glob("skills/*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        updated = re.sub(
            rf'^(\s*version:\s*"){re.escape(old)}"',
            rf'\g<1>{new}"',
            text,
            flags=re.MULTILINE,
        )
        if updated != text:
            skill_file.write_text(updated, encoding="utf-8")
            changed.append(skill_file)
        else:
            print(f"  [warn] no version found in {skill_file.relative_to(ROOT)}")
    return changed


def bump_changelog(new: str) -> Path:
    path = ROOT / "CHANGELOG.md"
    text = path.read_text(encoding="utf-8")
    today = date.today().isoformat()
    placeholder = f"## [{new}] — {today}\n\n### Added\n\n-\n\n### Changed\n\n-\n\n---\n\n"
    # Insert after the first "---" separator line
    updated = re.sub(r"(---\n\n)", r"\1" + placeholder, text, count=1)
    path.write_text(updated, encoding="utf-8")
    return path


def git_commit(files: list[Path], new: str) -> None:
    rel = [str(p.relative_to(ROOT)) for p in files]
    subprocess.run(["git", "add", *rel], cwd=ROOT, check=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore: bump version to {new}"],
        cwd=ROOT,
        check=True,
    )


def git_tag(new: str, push: bool) -> None:
    tag = f"v{new}"
    subprocess.run(["git", "tag", tag], cwd=ROOT, check=True)
    print(f"  tag created: {tag}")
    if push:
        subprocess.run(["git", "push", "origin", tag], cwd=ROOT, check=True)
        print(f"  tag pushed: {tag}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump mnemo version everywhere.")
    parser.add_argument("version", help="New version, e.g. 0.8.0")
    parser.add_argument("--commit", action="store_true", help="Create a git commit for the bump")
    parser.add_argument("--tag", action="store_true", help="Create a git tag vX.Y.Z")
    parser.add_argument("--push", action="store_true", help="Push tag to origin (implies --tag)")
    args = parser.parse_args()

    new = args.version
    old = current_version()

    if args.push:
        args.tag = True

    if args.tag and not args.commit:
        sys.exit("error: --tag/--push require --commit so the tag points at the bumped version commit")

    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        sys.exit(f"error: version must be X.Y.Z, got: {new!r}")

    if old == new:
        sys.exit(f"error: already at version {new}")

    print(f"Bumping {old} -> {new}\n")

    changed: list[Path] = []

    for plugin_path in PLUGIN_MANIFESTS:
        path = bump_plugin_json(plugin_path, new)
        print(f"  {path.relative_to(ROOT)}")
        changed.append(path)

    path = bump_readme(old, new)
    print(f"  {path.relative_to(ROOT)}")
    changed.append(path)

    skill_files = bump_skills(old, new)
    for p in skill_files:
        print(f"  {p.relative_to(ROOT)}")
    changed.extend(skill_files)

    path = bump_changelog(new)
    print(f"  {path.relative_to(ROOT)}  (fill in the release notes)")
    changed.append(path)

    print()
    if args.commit:
        git_commit(changed, new)
        print("  commit created")

        if args.tag:
            git_tag(new, push=args.push)

        print("\nDone.")
    else:
        print("  no commit created")
        print("\nDone. Fill in CHANGELOG.md, review the diff, then create your commit manually.")


if __name__ == "__main__":
    main()
