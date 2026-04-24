---
name: stats
description: >
  Display size metrics and scaling health for the mnemo wiki: page counts per
  category, total line count, top 5 largest pages, and scaling threshold status
  (flat index, approaching 150-page shard threshold, or sharded). Use when the user
  says "stats", "how big is my wiki", "show me wiki metrics", "how many pages do I
  have", "is my knowledge base getting large", or "check scaling status".
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:stats). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for faster counting
  (scripts/wiki_stats.py).
metadata:
  author: mnemo contributors
  version: "0.5.0"
allowed-tools: Read Glob Bash
---

## Step 0 — Python fast path (optional)

1. Use `Glob('**/mnemo/scripts/wiki_stats.py')` to locate the stats script.
2. If found at `<script_path>`, run:
   ```
   python3 <script_path> .mnemo/<project-name>
   ```
3. If exit code is 0: present the script output and **stop** — do not run steps 1–5.
4. If Python is unavailable or script not found, continue to Step 1 below.

Display metrics for `.mnemo/<project-name>/`.

## Steps

**1. Count pages per category:**
- `sources_count` = count of files matching `.mnemo/<project-name>/wiki/sources/*.md`
- `entities_count` = count of files matching `.mnemo/<project-name>/wiki/entities/*.md`
- `concepts_count` = count of files matching `.mnemo/<project-name>/wiki/concepts/*.md`
- `synthesis_count` = count of files matching `.mnemo/<project-name>/wiki/synthesis/*.md`
- `total_pages` = sum of all four

**2. Count total lines** — for each wiki page, read and count lines. Sum all → `total_lines`.

**3. Find largest pages** — sort all wiki pages by line count descending. Take the top 5.

**4. Check thresholds:**
- `total_pages` >= 150 → "Index sharding active (or recommended)"
- `total_pages` >= 100 → "Approaching index sharding threshold (150 pages)"
- Any page > 400 lines → include in oversized list (warning)
- Any page > 800 lines → include in critical list (should have been split during ingest)

**5. Report:**

```
## Knowledge Base Stats

| Category   | Pages |
|------------|-------|
| Sources    | <sources_count> |
| Entities   | <entities_count> |
| Concepts   | <concepts_count> |
| Synthesis  | <synthesis_count> |
| **Total**  | **<total_pages>** |

**Total lines:** <total_lines>

### Largest pages
1. `wiki/sources/foo.md` — 312 lines
2. ...

### Scaling status
- Index: <sharded | flat | approaching threshold (X/150)>
- Oversized pages (>400 lines): <list paths or "none">
- Critical pages (>800 lines): <list paths or "none">
```
