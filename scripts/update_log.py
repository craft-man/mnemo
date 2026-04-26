#!/usr/bin/env python3
"""Append a log entry to log.md. Python 3.10+ stdlib only.

Usage:
  python scripts/update_log.py --vault .mnemo/myproject \
      --file wiki/sources/foo.md --op ingest [--timestamp ISO]

Special op 'lint': updates the '# Last lint: <timestamp>' header line
instead of appending a bullet entry.
"""
import argparse
import datetime
import pathlib
import sys

VALID_OPS = {"ingest", "generated", "skipped", "lint", "init"}


def _now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def _ensure_log(log_path: pathlib.Path) -> None:
    if not log_path.exists():
        log_path.write_text("# Log\n", encoding="utf-8")


def append_entry(log_path: pathlib.Path, file: str, op: str, ts: str) -> None:
    _ensure_log(log_path)
    entry = f"- {file} | {ts} | {op}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(entry)


def update_lint_header(log_path: pathlib.Path, ts: str) -> None:
    _ensure_log(log_path)
    header = f"# Last lint: {ts}\n"
    text = log_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# Last lint:"):
            lines[i] = header
            log_path.write_text("".join(lines), encoding="utf-8")
            return
    log_path.write_text(header + text, encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Append a log entry to log.md.")
    p.add_argument("--vault", required=True, help="Vault root directory")
    p.add_argument("--file", required=False, default="", help="Wiki file path (relative to vault)")
    p.add_argument("--op", required=True, help=f"Operation type: {', '.join(sorted(VALID_OPS))}")
    p.add_argument("--timestamp", default=None, help="ISO 8601 UTC timestamp (default: now)")
    args = p.parse_args()

    vault = pathlib.Path(args.vault).expanduser().resolve()
    if not vault.exists():
        print(f"[error] vault not found: {vault}", file=sys.stderr)
        sys.exit(1)

    if args.op not in VALID_OPS:
        print(
            f"[error] invalid op '{args.op}'. Valid: {', '.join(sorted(VALID_OPS))}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.op != "lint" and not args.file:
        print("[error] --file is required for non-lint ops", file=sys.stderr)
        sys.exit(1)

    if args.op != "lint" and ("|" in args.file or "\n" in args.file):
        print("[error] --file must not contain '|' or newline characters", file=sys.stderr)
        sys.exit(1)

    ts = args.timestamp or _now_utc()
    log_path = vault / "log.md"

    try:
        if args.op == "lint":
            update_lint_header(log_path, ts)
        else:
            append_entry(log_path, args.file, args.op, ts)
    except OSError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[ok] log updated — {args.op}")


if __name__ == "__main__":
    main()
