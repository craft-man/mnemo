---
name: log
description: >
  Query the mnemo audit log (log.md) in natural language. Displays ingest,
  skipped, generated, and lint entries as a sorted markdown table. Supports
  filtering by operation type (op), recency (last N), and date range (since).
  Use when the user says "show the log", "what was ingested", "last 5 entries",
  "show skips", "what happened since Monday", "when was the last lint", or
  "audit log".
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:log). Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.16.3"
allowed-tools: Read Glob Bash
---

Query `log.md` and display matching entries as a markdown table.
No sub-agent is dispatched — the log is small and deterministic.

## Step 0 — Determine vault and locate log.md

1. `<project-name>` = current working directory base name.
2. `<log_path>` = `.mnemo/<project-name>/log.md`.
3. If the file does not exist, check for any subdirectory under `.mnemo/` and
   use its `log.md` if exactly one vault is present.
4. If still not found, output:
   > log.md not found. Run /mnemo:init to initialize the vault.

   Then stop.

## Step 1 — Parse natural language arguments into filters

Parse `$ARGUMENTS` (may be empty) to extract up to three optional filters:

| Filter | Type | NL triggers |
|--------|------|-------------|
| `op`   | `ingest \| skipped \| generated \| lint` | "ingest", "ingests", "skip", "skips", "skipped", "generated", "lint" |
| `last` | integer N | "last" → 1, "last N" |
| `since` | ISO date YYYY-MM-DD | "yesterday" → today - 1 day, "this week" → Monday of current week, "since monday" → Monday of current week, "since YYYY-MM-DD" → that date |

Rules:
- "last" without a number → `last=1`.
- No arguments or "all" → no filters applied.
- If `since` value is present but unrecognized, output:
  > Unrecognized date: "\<value>". Try "since YYYY-MM-DD".

  Then stop.
- Use `Bash` with `date` to compute relative dates (today, yesterday, Monday of
  current week). Example: `date -d "last monday" +%Y-%m-%d` on Linux,
  `date -v-mon +%Y-%m-%d` on macOS. Today's date is available as `$CURRENT_DATE`
  if injected by the harness; otherwise run `date +%Y-%m-%d`.

## Step 2 — Read and parse log.md

Read the full contents of `<log_path>`.

Parse each line according to its type:

**Lint line** — matches `# Last lint: <timestamp>`:
```
path = —
timestamp = <timestamp>   (ISO 8601, e.g. 2026-04-25T14:00:00Z)
op = lint
```

**Entry line** — matches `- <path> | <timestamp> | <op>`:
```
path = <path>
timestamp = <timestamp>
op = <op>   (ingest | skipped | generated)
```

Silently ignore any line that matches neither pattern (blank lines, headers,
malformed entries).

## Step 3 — Apply filters

Apply filters in this order:

1. **op filter** — if `op` is set, keep only entries where `entry.op == op`.
2. **since filter** — if `since` is set, keep only entries where
   `entry.timestamp >= since` (compare date prefix YYYY-MM-DD).
3. **Sort** — sort remaining entries by timestamp descending (most recent first).
4. **last filter** — if `last` is set, keep only the first `last` entries.

If no entries remain after filtering:
> No matching entries in log.md.

Then stop.

## Step 4 — Format and display

Output a markdown table:

```
| Date | File | Operation |
|---|---|---|
| 2026-04-25 14:00 | — | lint |
| 2026-04-24 11:00 | raw/notes.md | skipped |
| 2026-04-24 10:00 | raw/paper.pdf | ingest |
```

Format rules:
- **Date** column: display `YYYY-MM-DD HH:MM` (drop seconds and timezone).
  If timestamp has no time component, display `YYYY-MM-DD`.
- **File** column: display `path` as-is (use `—` for lint entries).
- **Operation** column: display `op` lowercase as-is.
- Table is sorted most recent first (already done in Step 3).
