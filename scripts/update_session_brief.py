#!/usr/bin/env python3
"""Generate a compact session startup brief for a mnemo vault.

Usage:
  python scripts/update_session_brief.py --vault .mnemo/myproject
  python scripts/update_session_brief.py --vault .mnemo/myproject --summary "..."
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

MAX_CANONICAL = 12
DEFAULT_MAX_LOG = 8


def _today() -> str:
    return dt.date.today().isoformat()


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _index_entries(index_path: Path, limit: int = MAX_CANONICAL) -> list[str]:
    if not index_path.exists():
        return []
    entries: list[str] = []
    try:
        lines = index_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("- ["):
            continue
        if "](wiki/" not in stripped:
            continue
        entries.append(stripped)
        if len(entries) >= limit:
            break
    return entries


def _recent_log_entries(log_path: Path, max_log: int) -> list[str]:
    if not log_path.exists() or max_log <= 0:
        return []
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    entries = [line.strip() for line in lines if line.strip().startswith("- ") and "|" in line]
    return entries[-max_log:]


def _count_pages(vault: Path) -> int:
    wiki = vault / "wiki"
    if not wiki.exists():
        return 0
    return sum(1 for path in wiki.rglob("*.md") if "activity" not in path.parts and "indexes" not in path.parts)


def _project_name(vault: Path) -> str:
    return vault.name if vault.name else "mnemo"


def _normalize_summary(summary: str | None, vault: Path) -> str:
    if summary:
        return summary.strip()
    schema = vault / "SCHEMA.md"
    if schema.exists():
        try:
            text = schema.read_text(encoding="utf-8", errors="replace")
        except OSError:
            text = ""
        match = re.search(r"## Domain\s+(.+?)(?:\n## |\Z)", text, re.DOTALL)
        if match:
            domain = " ".join(line.strip() for line in match.group(1).splitlines() if line.strip() and not line.strip().startswith("<!--"))
            if domain:
                return domain[:300]
    return f"mnemo knowledge base for {_project_name(vault)}."


def render_brief(vault: Path, summary: str | None, max_log: int) -> str:
    config = _read_json(vault / "config.json")
    backend = config.get("search_backend", "unknown")
    qmd_collection = config.get("qmd_collection", "")
    page_count = _count_pages(vault)
    canonical = _index_entries(vault / "index.md")
    recent = _recent_log_entries(vault / "log.md", max_log)
    graph_report = vault.parent.parent / "graphify-out" / "GRAPH_REPORT.md"
    graph_line = "- Codebase map: `graphify-out/GRAPH_REPORT.md` (read only when the task concerns code structure)" if graph_report.exists() else "- Codebase map: not present"

    lines = [
        "# Session Brief",
        "",
        f"_Auto-generated {_today()} by `scripts/update_session_brief.py`. Keep this file compact._",
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
        _normalize_summary(summary, vault),
        "",
        "## Search",
        "",
        f"- Backend: `{backend}`",
    ]
    if qmd_collection:
        lines.append(f"- qmd collection: `{qmd_collection}`")
    lines.extend([
        f"- Indexed wiki pages: {page_count}",
        "",
        "## Canonical Pages",
        "",
    ])
    lines.extend(canonical or ["- No index entries yet."])
    lines.extend([
        "",
        "## Recent Changes",
        "",
    ])
    lines.extend(recent or ["- No log entries yet."])
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate SESSION_BRIEF.md for a mnemo vault.")
    parser.add_argument("--vault", required=True, help="Vault root directory")
    parser.add_argument("--summary", default=None, help="Optional short project summary")
    parser.add_argument("--max-log", type=int, default=DEFAULT_MAX_LOG, help="Recent log entries to include")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.exists():
        print(f"[error] vault not found: {vault}", file=sys.stderr)
        sys.exit(1)

    content = render_brief(vault, args.summary, args.max_log)
    out = vault / "SESSION_BRIEF.md"
    try:
        out.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"[ok] wrote {out}")


if __name__ == "__main__":
    main()
