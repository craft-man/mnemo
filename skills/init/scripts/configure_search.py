#!/usr/bin/env python3
"""Configure mnemo search after the skill has resolved the user's choice."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def _run(args: list[str], cwd: Path | None = None) -> bool:
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 and result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode == 0


def _install_qmd() -> bool:
    if shutil.which("npm"):
        if _run(["npm", "install", "-g", "@tobilu/qmd"]):
            return shutil.which("qmd") is not None
    if shutil.which("bun"):
        if _run(["bun", "install", "-g", "@tobilu/qmd"]):
            return shutil.which("qmd") is not None
    return False


def configure(vault: Path, backend: str, install: bool) -> dict:
    vault = vault.resolve()
    if not vault.exists():
        raise FileNotFoundError(f"vault not found: {vault}")

    config = {"search_backend": "bm25"}
    status = "bm25"
    reason = "requested"

    if backend == "qmd":
        qmd_path = shutil.which("qmd")
        if qmd_path is None and install:
            _install_qmd()
            qmd_path = shutil.which("qmd")
        if qmd_path is None:
            reason = "qmd_unavailable"
        else:
            project_root = vault.parent.parent
            collection_path = f".mnemo/{vault.name}/wiki"
            if _run(["qmd", "collection", "add", "mnemo-wiki", collection_path, "**/*.md"], cwd=project_root):
                config = {"search_backend": "qmd", "qmd_collection": "mnemo-wiki"}
                status = "qmd"
                reason = "configured"
            else:
                reason = "qmd_collection_failed"

    (vault / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return {"status": status, "reason": reason, "vault": str(vault), "config": config}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write mnemo search config.")
    parser.add_argument("--vault", required=True, help="Path to .mnemo/<project>.")
    parser.add_argument("--backend", choices=("qmd", "bm25"), required=True, help="Resolved user choice.")
    parser.add_argument("--install", action="store_true", help="Attempt qmd installation if missing.")
    args = parser.parse_args(argv)
    try:
        result = configure(Path(args.vault), args.backend, args.install)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
