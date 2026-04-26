#!/usr/bin/env python3
"""Bump mnemo version across all tracked locations and optionally create a git tag.

Usage:
    python3 scripts/bump_version.py 0.8.0
    python3 scripts/bump_version.py 0.8.0 --tag
    python3 scripts/bump_version.py 0.8.0 --tag --push
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent


def current_version() -> str:
    plugin = ROOT / ".claude-plugin" / "plugin.json"
    return json.loads(plugin.read_text(encoding="utf-8"))["version"]


def bump_plugin_json(old: str, new: str) -> Path:
    path = ROOT / ".claude-plugin" / "plugin.json"
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
    parser.add_argument("--tag", action="store_true", help="Create a git tag vX.Y.Z")
    parser.add_argument("--push", action="store_true", help="Push tag to origin (implies --tag)")
    args = parser.parse_args()

    new = args.version
    old = current_version()

    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        sys.exit(f"error: version must be X.Y.Z, got: {new!r}")

    if old == new:
        sys.exit(f"error: already at version {new}")

    print(f"Bumping {old} -> {new}\n")

    changed: list[Path] = []

    path = bump_plugin_json(old, new)
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
    git_commit(changed, new)
    print(f"  commit created")

    if args.tag or args.push:
        git_tag(new, push=args.push)

    print(f"\nDone. Edit CHANGELOG.md to add release notes, then push.")


if __name__ == "__main__":
    main()
