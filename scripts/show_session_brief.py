#!/usr/bin/env python3
"""Print the compact mnemo startup context for a vault.

Read-only helper for agents and users that need to load mnemo context manually.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _regen_command(vault: Path) -> str:
    return f"python scripts/update_session_brief.py --vault {vault}"


def _stale_sources(vault: Path, brief: Path) -> list[Path]:
    try:
        brief_mtime = brief.stat().st_mtime
    except OSError:
        return []

    stale: list[Path] = []
    for name in ("index.md", "log.md", "config.json"):
        path = vault / name
        try:
            if path.exists() and path.stat().st_mtime > brief_mtime:
                stale.append(path)
        except OSError:
            continue
    return stale


def _print_warning(message: str) -> None:
    print(f"[warning] {message}", file=sys.stderr)


def show_session_brief(vault: Path, include_code: bool) -> int:
    vault = vault.expanduser().resolve()
    brief = vault / "SESSION_BRIEF.md"

    if not vault.exists():
        print(f"[error] vault not found: {vault}", file=sys.stderr)
        return 1

    if not brief.exists():
        print(f"[error] missing session brief: {brief}", file=sys.stderr)
        print(f"Run: {_regen_command(vault)}", file=sys.stderr)
        return 1

    stale = _stale_sources(vault, brief)
    if stale:
        names = ", ".join(path.name for path in stale)
        _print_warning(f"SESSION_BRIEF.md may be stale; newer file(s): {names}")
        _print_warning(f"Regenerate with: {_regen_command(vault)}")

    try:
        print(brief.read_text(encoding="utf-8", errors="replace"), end="")
    except OSError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if include_code:
        graph_report = vault.parent.parent / "graphify-out" / "GRAPH_REPORT.md"
        print("\n\n---\n\n# Codebase Context\n")
        if graph_report.exists():
            try:
                print(graph_report.read_text(encoding="utf-8", errors="replace"), end="")
            except OSError as exc:
                print(f"[error] {exc}", file=sys.stderr)
                return 1
        else:
            print("graphify-out/GRAPH_REPORT.md not present")

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Print SESSION_BRIEF.md for a mnemo vault.")
    parser.add_argument("--vault", required=True, help="Vault root directory")
    parser.add_argument("--code", action="store_true", help="Append graphify-out/GRAPH_REPORT.md when present")
    args = parser.parse_args()
    raise SystemExit(show_session_brief(Path(args.vault), args.code))


if __name__ == "__main__":
    main()
