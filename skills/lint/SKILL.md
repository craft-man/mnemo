---
name: lint
description: >
  Audit the mnemo knowledge base for structural issues: orphaned pages, broken
  index links, missing YAML frontmatter, missing source citations, oversized pages,
  pages with no inbound wikilinks, stale temporal claims, superseded pages missing
  a History section, and unprocessed raw files.
  Presents each finding as a proposed edit awaiting user approval. Use when the user
  says "check my wiki", "audit the knowledge base", "lint my notes", "find broken
  links", or "health check". Run periodically and after any batch ingest.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:lint). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for faster auditing
  (scripts/wiki_lint.py).
metadata:
  author: mnemo contributors
  version: "0.6.0"
allowed-tools: Read Write Edit Glob Grep Bash
---

## Step 0 — Python fast path (optional)

1. Use `Glob('**/mnemo/scripts/wiki_lint.py')` to locate the lint script.
2. If found at `<script_path>`:
   - Before invoking, pre-read `.mnemo/<project-name>/log.md` and look for a line `# Last lint: <timestamp>`. If found, append `--since <timestamp>` to the command below.
   ```
   python3 <script_path> .mnemo/<project-name> [--since <last_lint_ts>]
   ```
3. If exit code is 0: present the script output. Then proceed directly to **Step 12** (interactive approval of proposed edits) — skip steps 0b and 1–11. After step 12 completes, still execute the **Record lint timestamp** step at the end.
4. If Python is unavailable or script not found, continue to Step 0b below.

## Step 0b — Incremental mode detection

Before step 1, check whether a previous lint run has been recorded:

1. Read `.mnemo/<project-name>/log.md`. Look for a line of the form `# Last lint: <ISO timestamp>`.
2. If found: set `incremental_mode = true`, `last_lint_ts = <timestamp>`.
   - Build `recent_files`: glob `.mnemo/<project-name>/wiki/**/*.md`, read the `updated:` field from each page's YAML frontmatter. Keep only files where `updated:` ≥ `last_lint_ts`. This is the scoped file set for per-file content checks.
   - Structural checks (`missing_structure`, `orphan`, `broken_link`, `unprocessed`, `gap_page`) always run against the full knowledge base regardless of mode.
3. If not found: set `incremental_mode = false`. All checks run against the full `wiki_files` set (full scan).
4. Report mode at the start of the audit output: `"Mode: incremental (since <last_lint_ts>), <N> files in scope"` or `"Mode: full scan"`.

Audit `.mnemo/<project-name>/` and report issues as proposed edits.

## Steps

**1. Check initialization** — verify these paths exist:
- `.mnemo/<project-name>/wiki/sources/`
- `.mnemo/<project-name>/wiki/entities/`
- `.mnemo/<project-name>/wiki/concepts/`
- `.mnemo/<project-name>/wiki/synthesis/`
- `.mnemo/<project-name>/wiki/indexes/`
- `.mnemo/<project-name>/SCHEMA.md`

If any are missing, report as `missing_structure` and offer to run `/mnemo:init`.

**2. Read index** — read `.mnemo/<project-name>/index.md`. Extract all wiki paths from lines of the form `- [Title](wiki/<subdir>/filename.md)` → build `indexed_paths` set. If shard files exist in `wiki/indexes/` (`sources.md`, `entities.md`, `concepts.md`, `synthesis.md`), read and include those too.

**3. List wiki files** — glob `.mnemo/<project-name>/wiki/**/*.md` → build `wiki_files` set (relative paths like `wiki/sources/foo.md`). Exclude `SCHEMA.md` and files under `wiki/indexes/`.

**4. Read log** — read `.mnemo/<project-name>/log.md`. Build `processed_files` as the set of raw source filenames that have been ingested. Parse both formats:
- **Current format**: `- raw/<filename> | <timestamp> | ingest` → extract `<filename>`
- **Legacy format**: `- <filename> | <timestamp>` (no third field, no path prefix) → extract `<filename>`

Ignore lines containing `| generated` — those are save-created pages, not raw source files.

**5. List raw files** — glob `.mnemo/<project-name>/raw/*` → build `raw_files` set.

**6. Detect all issues (collect, don't act yet):**

| Issue type | Condition |
|---|---|
| `missing_structure` | Required dir or SCHEMA.md does not exist |
| `orphan` | File in `wiki_files` but not in `indexed_paths` |
| `broken_link` | Path in `indexed_paths` but file does not exist on disk |
| `unprocessed` | File in `raw_files` but not in `processed_files` |
| `oversized` | Wiki page exceeds 800 lines |
| `missing_frontmatter` | Wiki page does not start with `---` YAML frontmatter block |
| `missing_source_citation` | Page in `wiki/sources/` has no `source:` field in frontmatter |
| `no_inbound_links` | Entity or concept page has no `[[wikilink]]` pointing to it from any other page |
| `stale_claim` | Wiki page contains temporal language that may be outdated (see step 10) |
| `superseded_without_history` | Entity or concept page has `superseded_by:` or `supersedes:` in frontmatter but no `## History` section |
| `gap_page` | Term appears in 3+ source pages but has no dedicated entity or concept page (see step 11b) |

**7. Check oversized pages** — **Incremental scope**: if `incremental_mode` is active, use `recent_files` instead of all `wiki_files`. For each file in scope, read and count lines. Flag any exceeding 800 as `oversized`.

**8. Check frontmatter** — **Incremental scope**: if `incremental_mode` is active, use `recent_files`. For each file in scope, read the first 3 lines. If line 1 is not `---`, flag as `missing_frontmatter`.

**9. Check source citations** — **Incremental scope**: if `incremental_mode` is active, intersect `recent_files` with `wiki/sources/`. For each file in scope, read its YAML frontmatter block (lines between the two `---` delimiters). If no `source:` field is present, flag as `missing_source_citation`.

**10. Check inbound links** — **Incremental scope**: if `incremental_mode` is active, restrict to entity and concept pages in `recent_files` (only newly created or recently updated pages risk being orphaned). For each file in scope:
- Derive its page title from its H1 or frontmatter `title:` field.
- Grep all other wiki files for `[[<title>]]` or `[[<title>|`.
- If no other file references it, flag as `no_inbound_links`.

**11. Check stale claims** — **Incremental scope**: if `incremental_mode` is active, use `recent_files`. For each file in scope, scan its body (not frontmatter) for temporal language patterns:
- Phrases: `currently`, `recently`, `as of`, `at the time of writing`, `in <year>` where year < (current year - 1), `the latest`, `upcoming`, `will be`, `is planned`
- If found, flag as `stale_claim` with the matched phrase and the line number.
- Do not flag content inside `## Quotes & Excerpts` sections (verbatim citations are expected to be historical).

**11c. Superseded without history** — entity or concept pages with `superseded_by:` or `supersedes:` in frontmatter but no `## History` section. Offer to insert an empty `## History` section before `## Links`.

**11b. Detect page gaps (`suggest-pages`)** — identify topics that appear frequently across sources but have no dedicated page:

1. For each file in `wiki/sources/`, read the `## Entities Mentioned` and `## Concepts Covered` sections. Extract all `[[Term]]` wikilinks.
2. Build a frequency map: for each term, count how many distinct source pages reference it.
3. Keep terms with count ≥ 3.
4. For each high-frequency term: check whether a matching entity or concept page exists anywhere in `wiki/entities/` or `wiki/concepts/` (case-insensitive match on the H1 title or frontmatter `title:`).
5. If no page exists for a term with count ≥ 3, flag as `gap_page`:
   - Term name
   - Count of source pages referencing it
   - List of those source pages (up to 5)
   - Suggested filename (slugified, prefixed with inferred type: `tool-`, `person-`, `pattern-`, `technique-`, or bare slug if type is ambiguous)

Flag at most 10 gaps (highest frequency first). Do not flag terms shorter than 4 characters.

**12. Present as proposed edits — grouped by issue, one at a time:**

For each issue found, present it in this format and **wait for user approval before applying**:

```
── Issue N/Total: <issue_type> ─────────────────────
File: wiki/entities/tool-redis.md
Problem: no inbound [[wikilinks]] found

Proposed edit:
  In wiki/sources/redis-intro.md, add to ## Entities Mentioned:
  - [[Redis]] — in-memory data store

Apply? [y]es / [n]o / [s]kip all of this type / [a]pply all
```

For `gap_page` issues, the proposed edit is to run `/mnemo:ingest` (if the topic appears in raw/ sources) or `/mnemo:save` to create the page manually. Present as:

```
── Issue N/Total: gap_page ─────────────────────
Term: "Redis"
Referenced in 4 source pages: source-a.md, source-b.md, source-c.md, source-d.md
No dedicated entity or concept page found.

Suggested action:
  Create wiki/entities/tool-redis.md  (or run /mnemo:save "Redis")

Create now? [y]es / [n]o / [s]kip all gaps
```

If the user answers `[y]es`, invoke the save skill by reading `skills/save/SKILL.md` and following its instructions, with the suggested title pre-filled and source pages as context for the page body.

**Never apply any edit without explicit user approval.**

After all issues are reviewed:
- Summary: "X issues found, Y applied, Z skipped."
- If 0 issues: "Knowledge base is healthy — 0 issues."

**Record lint timestamp** — update `.mnemo/<project-name>/log.md`:
- If a `# Last lint: ...` line already exists: replace it in place with `# Last lint: <current UTC ISO timestamp>`.
- If no such line exists: prepend it as the first line of `log.md`.

This timestamp is what step 0b reads on the next run to scope incremental checks.
