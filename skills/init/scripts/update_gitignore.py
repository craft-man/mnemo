#!/usr/bin/env python3
"""Add .mnemo/ to .gitignore after the skill has obtained consent."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def update(project_root: Path, accept: bool) -> dict:
    project_root = project_root.resolve()
    if not accept:
        return {"status": "skipped", "reason": "declined"}
    gitignore = project_root / ".gitignore"
    entry = ".mnemo/"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if entry in {line.strip() for line in content.splitlines()}:
            return {"status": "unchanged", "path": str(gitignore)}
        gitignore.write_text(content.rstrip("\n") + "\n\n# mnemo knowledge base\n.mnemo/\n", encoding="utf-8")
    else:
        gitignore.write_text("# mnemo knowledge base\n.mnemo/\n", encoding="utf-8")
    return {"status": "updated", "path": str(gitignore)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Optionally add .mnemo/ to .gitignore.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--accept", action="store_true", help="Consent already collected by the skill.")
    args = parser.parse_args(argv)
    try:
        result = update(Path(args.project_root), args.accept)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
