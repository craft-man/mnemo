#!/usr/bin/env python3
"""Write SCHEMA.md from values already validated by the schema skill."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _items(value: str, fallback: list[str]) -> list[str]:
    parsed = [item.strip() for item in value.split(",") if item.strip()]
    return parsed or fallback


def _line(name: str, kind: str) -> str:
    return f"- **{name}** -- {kind} category validated during schema setup"


def write_schema(vault: Path, domain: str, entity_types: str, concept_categories: str) -> dict:
    vault = vault.resolve()
    if not vault.exists():
        raise FileNotFoundError(f"vault not found: {vault}")
    entities = _items(entity_types, ["Person", "Tool", "Project"])
    concepts = _items(concept_categories, ["Pattern", "Technique", "Problem"])
    content = f"""# Knowledge Base Schema

## Domain
{domain.strip() or "General knowledge base for this project."}

## Entity Types
{chr(10).join(_line(item, "entity") for item in entities)}

## Concept Taxonomy
{chr(10).join(_line(item, "concept") for item in concepts)}

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md` (e.g. `tool-redis.md`)
- Concept pages: `wiki/concepts/<category>-<name>.md` (e.g. `pattern-saga.md`)
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax -- always the exact H1 title of the target page. Obsidian-compatible.
"""
    path = vault / "SCHEMA.md"
    path.write_text(content, encoding="utf-8")
    return {"status": "written", "path": str(path), "entity_types": entities, "concept_categories": concepts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write validated mnemo schema values.")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--entity-types", required=True)
    parser.add_argument("--concept-categories", required=True)
    args = parser.parse_args(argv)
    try:
        result = write_schema(Path(args.vault), args.domain, args.entity_types, args.concept_categories)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
