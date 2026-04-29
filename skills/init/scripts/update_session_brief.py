#!/usr/bin/env python3
"""Generate a compact SESSION_BRIEF.md for a mnemo vault."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _domain(vault: Path, fallback: str | None) -> str:
    if fallback:
        return fallback.strip()
    schema = vault / "SCHEMA.md"
    if schema.exists():
        text = schema.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"## Domain\s+(.+?)(?:\n## |\Z)", text, re.DOTALL)
        if match:
            lines = [line.strip() for line in match.group(1).splitlines()]
            lines = [line for line in lines if line and not line.startswith("<!--")]
            if lines:
                return " ".join(lines)[:300]
    return f"mnemo knowledge base for {vault.name}."


def _index_entries(vault: Path, limit: int) -> list[str]:
    index = vault / "index.md"
    if not index.exists():
        return []
    entries = []
    for line in index.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("- [") and "](wiki/" in stripped:
            entries.append(stripped)
        if len(entries) >= limit:
            break
    return entries


def _recent_log(vault: Path, limit: int) -> list[str]:
    log = vault / "log.md"
    if not log.exists():
        return []
    entries = [line.strip() for line in log.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip().startswith("- ") and "|" in line]
    return entries[-limit:]


def _page_count(vault: Path) -> int:
    wiki = vault / "wiki"
    if not wiki.exists():
        return 0
    return sum(1 for path in wiki.rglob("*.md") if "activity" not in path.parts and "indexes" not in path.parts)


def render(vault: Path, summary: str | None, max_log: int) -> str:
    config = _read_json(vault / "config.json")
    graph_report = vault.parent.parent / "graphify-out" / "GRAPH_REPORT.md"
    graph_line = "- Codebase map: `graphify-out/GRAPH_REPORT.md` (read only when the task concerns code structure)" if graph_report.exists() else "- Codebase map: not present"
    lines = [
        "# Session Brief",
        "",
        f"_Auto-generated {dt.date.today().isoformat()} by `skills/init/scripts/update_session_brief.py`. Keep this file compact._",
        "",
        "## Startup Reads",
        "",
        "- Read this file first.",
        "- Read `~/.mnemo/wiki/entities/person-user.md` if user preferences matter.",
        graph_line,
        "- Use `/mnemo:query <term>` for factual lookup instead of loading the whole wiki.",
        "",
        "## Project Summary",
        "",
        _domain(vault, summary),
        "",
        "## Search",
        "",
        f"- Backend: `{config.get('search_backend', 'unknown')}`",
    ]
    if config.get("qmd_collection"):
        lines.append(f"- qmd collection: `{config['qmd_collection']}`")
    lines.extend([f"- Indexed wiki pages: {_page_count(vault)}", "", "## Canonical Pages", ""])
    lines.extend(_index_entries(vault, 12) or ["- No index entries yet."])
    lines.extend(["", "## Recent Changes", ""])
    lines.extend(_recent_log(vault, max_log) or ["- No log entries yet."])
    lines.extend([
        "",
        "## Active Threads",
        "",
        "- None recorded in the brief. Use `/mnemo:mine` or `/mnemo:save` for durable decisions.",
        "",
        "## Guardrails",
        "",
        "- Do not load all wiki pages at session startup.",
        "- Treat `raw/` as immutable source input; synthesize into `wiki/`.",
        "- Update `index.md` and `log.md` before regenerating this brief.",
        "- Prefer qmd for medium and large wikis; BM25 is the no-dependency fallback.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate SESSION_BRIEF.md for a mnemo vault.")
    parser.add_argument("--vault", required=True)
    parser.add_argument("--summary", default=None)
    parser.add_argument("--max-log", type=int, default=8)
    args = parser.parse_args(argv)
    vault = Path(args.vault).expanduser().resolve()
    if not vault.exists():
        print(f"error: vault not found: {vault}", file=sys.stderr)
        return 1
    out = vault / "SESSION_BRIEF.md"
    out.write_text(render(vault, args.summary, args.max_log), encoding="utf-8")
    print(json.dumps({"status": "updated", "path": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
