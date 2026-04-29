#!/usr/bin/env python3
"""Create the global mnemo user profile only when it is absent."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

DIRS = ["raw", "wiki/sources", "wiki/entities", "wiki/concepts", "wiki/synthesis", "wiki/activity", "wiki/indexes"]


def _ensure_global(root: Path) -> None:
    for rel in DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text((root / "index.md").read_text(encoding="utf-8") if (root / "index.md").exists() else "# Index\n\n## Sources\n\n## Entities\n\n## Concepts\n\n## Synthesis\n", encoding="utf-8")
    (root / "log.md").write_text((root / "log.md").read_text(encoding="utf-8") if (root / "log.md").exists() else "# Log\n", encoding="utf-8")


def write_profile(home: Path, role: str, technical_level: str, language: str, domains: str, proactivity: str, register: str) -> dict:
    global_root = home.expanduser().resolve() / ".mnemo"
    _ensure_global(global_root)
    profile = global_root / "wiki" / "entities" / "person-user.md"
    if profile.exists():
        return {"status": "unchanged", "path": str(profile)}
    today = dt.date.today().isoformat()
    profile.write_text(f"""---
title: User Profile
category: entities
tags: [user, profile]
created: {today}
updated: {today}
---

# User Profile

## Role
{role.strip() or "Solo developer"}

## Technical Level
{technical_level.strip() or "CLI comfortable"}

## Language
{language.strip() or "English"}

## Domains
{domains.strip() or "General knowledge"}

## Proactivity
{proactivity.strip() or "Moderate"}

## Register
{register.strip() or "Direct"}

## Links
""", encoding="utf-8")
    return {"status": "created", "path": str(profile)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create ~/.mnemo user profile if absent.")
    parser.add_argument("--home", default=str(Path.home()), help="Home directory. Defaults to current user home.")
    parser.add_argument("--role", required=True)
    parser.add_argument("--technical-level", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--domains", required=True)
    parser.add_argument("--proactivity", required=True)
    parser.add_argument("--register", required=True)
    args = parser.parse_args(argv)
    try:
        result = write_profile(Path(args.home), args.role, args.technical_level, args.language, args.domains, args.proactivity, args.register)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
