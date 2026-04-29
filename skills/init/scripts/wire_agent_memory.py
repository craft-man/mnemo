#!/usr/bin/env python3
"""Wire mnemo startup guidance into a project agent memory file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _has_stanza(path: Path) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8", errors="replace")
    return "## mnemo" in content or "## Knowledge Base (mnemo)" in content


def _stanza(project_name: str, graphify: bool) -> str:
    lines = [
        "## mnemo",
        "",
        f"This project has a mnemo knowledge base in `.mnemo/{project_name}/`.",
        "",
        "At the start of every session:",
        "- Read the user profile if it exists at `~/.mnemo/wiki/entities/person-user.md`",
        f"- Read `.mnemo/{project_name}/SESSION_BRIEF.md` if it exists",
        "- Read `graphify-out/GRAPH_REPORT.md` only if the task concerns codebase structure",
        "- Use that context before answering project-specific questions or making implementation decisions",
        "",
        "During the session:",
        "- Query it with `/mnemo:query <term>` before answering factual questions",
        "- Ingest new sources with `/mnemo:ingest`",
        f"- When a spec or plan is finalized, move it to `.mnemo/{project_name}/raw/` and run `/mnemo:ingest`",
    ]
    if graphify:
        lines.extend([
            "- Treat `graphify-out/GRAPH_REPORT.md` as the canonical starting point for project structure when it exists",
            "- Refresh graphify after significant code changes to keep the knowledge graph up to date",
        ])
    return "\n".join(lines) + "\n"


def _append(path: Path, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8").rstrip()
        path.write_text(existing + "\n\n" + content, encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")


def _ensure_claude_stop_hook(project_root: Path) -> bool:
    settings = project_root / ".claude" / "settings.local.json"
    if not (project_root / "CLAUDE.md").exists():
        return False
    settings.parent.mkdir(parents=True, exist_ok=True)
    command = "echo 'mnemo: run /mnemo:mine to capture durable session insights.'"
    hook = {"matcher": "", "hooks": [{"type": "command", "command": command}]}
    data = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"warning: invalid JSON, skipped hook: {settings}", file=sys.stderr)
            return False
    stop_hooks = data.setdefault("hooks", {}).setdefault("Stop", [])
    if any(item.get("command") == command for entry in stop_hooks for item in entry.get("hooks", [])):
        return False
    stop_hooks.append(hook)
    settings.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def wire(project_root: Path, project_name: str, graphify: bool) -> dict:
    project_root = project_root.resolve()
    candidates = [project_root / "AGENTS.md", project_root / "CLAUDE.md"]
    target = next((path for path in candidates if path.exists()), candidates[0])
    if _has_stanza(target):
        hook_written = _ensure_claude_stop_hook(project_root)
        return {"status": "unchanged", "path": str(target), "hook_written": hook_written}
    _append(target, _stanza(project_name, graphify))
    hook_written = _ensure_claude_stop_hook(project_root)
    return {"status": "updated", "path": str(target), "hook_written": hook_written}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add mnemo guidance to AGENTS.md or CLAUDE.md.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--graphify", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = wire(Path(args.project_root), args.project_name, args.graphify)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
