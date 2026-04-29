#!/usr/bin/env python3
"""Create a local mnemo project vault.

Non-interactive. JSON is written to stdout; diagnostics go to stderr.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DIRS = [
    "raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/synthesis",
    "wiki/activity",
    "wiki/indexes",
]

INDEX_TEMPLATE = """# Index

## Sources

## Entities

## Concepts

## Synthesis
"""

LOG_TEMPLATE = "# Log\n"

SCHEMA_TEMPLATE = """# Knowledge Base Schema

> Starter schema. The schema skill must replace these placeholders during init.

## Domain
<!-- Describe the subject matter of this knowledge base. -->

## Entity Types
- **Person** -- researchers, authors, contributors
- **Tool** -- software, libraries, frameworks
- **Project** -- codebases, products, initiatives

## Concept Taxonomy
- **Pattern** -- reusable design or architectural pattern
- **Technique** -- method or approach
- **Problem** -- known failure mode or challenge

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md`
- Concept pages: `wiki/concepts/<category>-<name>.md`
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax -- always the exact H1 title of the target page.
"""


def _write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def create_vault(project_root: Path, project_name: str | None = None) -> dict:
    project_root = project_root.resolve()
    name = project_name or project_root.name
    vault = project_root / ".mnemo" / name
    if vault.exists():
        return {"status": "already_exists", "vault": str(vault), "project_name": name}

    created_dirs: list[str] = []
    for rel in DIRS:
        path = vault / rel
        path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(rel)

    created_files = []
    for rel, content in {
        "index.md": INDEX_TEMPLATE,
        "log.md": LOG_TEMPLATE,
        "SCHEMA.md": SCHEMA_TEMPLATE,
    }.items():
        if _write_if_missing(vault / rel, content):
            created_files.append(rel)

    return {
        "status": "created",
        "vault": str(vault),
        "project_name": name,
        "created_dirs": created_dirs,
        "created_files": created_files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create .mnemo/<project>/ vault structure.")
    parser.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--project-name", default=None, help="Vault name. Defaults to project directory name.")
    args = parser.parse_args(argv)

    try:
        result = create_vault(Path(args.project_root), args.project_name)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
