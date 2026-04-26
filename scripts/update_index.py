#!/usr/bin/env python3
"""Regenerate wiki/index.md from the frontmatter of every wiki page.
Python 3.10+ stdlib only.

Usage:
  python scripts/update_index.py --vault .mnemo/myproject [--dry-run] [--json]

Inspired by github.com/alirezarezvani/claude-skills — adapted to mnemo conventions:
  - Categories: sources, entities, concepts, synthesis
  - Link format: [Title](wiki/category/file.md)  (not Obsidian wikilinks)
  - Excludes wiki/indexes/ and wiki/activity/
  - Shards at 150 pages into wiki/indexes/<category>.md
"""
from __future__ import annotations
import argparse
import datetime
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
CATEGORY_ORDER = ["sources", "entities", "concepts", "synthesis", "other"]
FOLDER_TO_CATEGORY: dict[str, str] = {
    "sources": "sources",
    "entities": "entities",
    "concepts": "concepts",
    "synthesis": "synthesis",
}
EXCLUDED_DIRS = {"indexes", "activity"}
EXCLUDED_FILES = {"index.md", "log.md"}


def parse_frontmatter(text: str) -> dict[str, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip("'\"")
    return fm


def infer_title(path: Path, fm: dict[str, str]) -> str:
    if "title" in fm:
        return fm["title"]
    return path.stem.replace("-", " ").replace("_", " ").title()


def scan_wiki(vault: Path) -> dict[str, list[dict]]:
    wiki = vault / "wiki"
    if not wiki.exists():
        print(f"[error] {wiki} not found", file=sys.stderr)
        sys.exit(1)

    pages: dict[str, list[dict]] = defaultdict(list)
    for md in sorted(wiki.rglob("*.md")):
        rel = md.relative_to(wiki)
        if rel.name in EXCLUDED_FILES:
            continue
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue

        text = md.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)

        category = fm.get("category", "").lower()
        if not category and len(rel.parts) > 1:
            category = FOLDER_TO_CATEGORY.get(rel.parts[0], "other")
        category = category or "other"

        pages[category].append({
            "path": f"wiki/{rel.as_posix()}",
            "title": infer_title(md, fm),
            "summary": fm.get("summary", ""),
            "updated": fm.get("updated", ""),
        })

    for cat in pages:
        pages[cat].sort(key=lambda p: p["title"].lower())
    return pages


def _format_entry(e: dict) -> str:
    summary = f" — {e['summary']}" if e["summary"] else ""
    meta = f" _(upd {e['updated']})_" if e["updated"] else ""
    return f"- [{e['title']}]({e['path']}){summary}{meta}"


def render_index(pages: dict[str, list[dict]]) -> str:
    today = datetime.date.today().isoformat()
    total = sum(len(v) for v in pages.values())
    lines = ["# Index", "", f"_Auto-generated {today} • {total} pages_", ""]
    for cat in CATEGORY_ORDER:
        entries = pages.get(cat, [])
        label = f"## {cat.capitalize()}" + (f" ({len(entries)})" if entries else "")
        lines.append(label)
        lines.append("")
        for e in entries:
            lines.append(_format_entry(e))
        if entries:
            lines.append("")
    return "\n".join(lines)


def render_shard(entries: list[dict], category: str) -> str:
    today = datetime.date.today().isoformat()
    lines = [
        f"# {category.capitalize()} Index",
        "",
        f"_Auto-generated {today} • {len(entries)} pages_",
        "",
    ]
    for e in entries:
        lines.append(_format_entry(e))
    lines.append("")
    return "\n".join(lines)


def render_sharded_master(pages: dict[str, list[dict]]) -> str:
    today = datetime.date.today().isoformat()
    total = sum(len(v) for v in pages.values())
    lines = ["# Index", "", f"_Auto-generated {today} • {total} pages — sharded_", ""]
    for cat in CATEGORY_ORDER:
        entries = pages.get(cat, [])
        if not entries:
            continue
        lines.append(f"## {cat.capitalize()}")
        lines.append("")
        lines.append(f"- [{cat.capitalize()} Index](wiki/indexes/{cat}.md) ({len(entries)} pages)")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Regenerate wiki/index.md from every wiki page's YAML frontmatter."
    )
    p.add_argument("--vault", required=True, help="Vault root directory")
    p.add_argument("--dry-run", action="store_true", help="Print to stdout, do not write")
    p.add_argument("--json", action="store_true", help="Emit JSON summary")
    args = p.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.exists():
        msg = f"vault not found: {vault}"
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"[error] {msg}", file=sys.stderr)
        sys.exit(1)

    pages = scan_wiki(vault)
    total = sum(len(v) for v in pages.values())
    sharded = total > 150

    content = render_sharded_master(pages) if sharded else render_index(pages)
    summary = {
        "status": "ok",
        "vault": str(vault),
        "total_pages": total,
        "by_category": {k: len(v) for k, v in pages.items()},
        "sharded": sharded,
        "dry_run": args.dry_run,
    }

    if args.dry_run:
        if args.json:
            summary["content_preview"] = content[:500]
            print(json.dumps(summary, indent=2))
        else:
            print(content)
        return

    index_path = vault / "index.md"
    try:
        index_path.write_text(content, encoding="utf-8")
        if sharded:
            indexes_dir = vault / "wiki" / "indexes"
            indexes_dir.mkdir(exist_ok=True)
            for cat, entries in pages.items():
                if entries and cat in set(CATEGORY_ORDER):
                    (indexes_dir / f"{cat}.md").write_text(render_shard(entries, cat), encoding="utf-8")
    except OSError as e:
        msg = str(e)
        if args.json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"[error] {msg}", file=sys.stderr)
        sys.exit(1)

    summary["index_path"] = str(index_path)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        suffix = " — sharded" if sharded else ""
        print(f"[ok] wrote {index_path} ({total} pages{suffix})")


if __name__ == "__main__":
    main()
