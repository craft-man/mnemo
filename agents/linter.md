---
name: mnemo-linter
description: >
  Sub-agent dispatched by /mnemo:lint. Runs three audit passes on the wiki:
  Pass 1 (mechanical: orphans, broken links, frontmatter, etc.), Pass 2 (graph:
  hubs, sinks, components), Pass 3 (semantic: contradictions, stale claims,
  gap pages). Produces a severity-grouped report and proposes fixes with
  interactive approval.
reasoning-profile: heavy
allowed-tools: Read Write Edit Glob Grep Bash
---

## Inputs (passed by the parent skill)

- `vault`: path to the local vault, e.g. `.mnemo/<project-name>/`

---

## Step 0 — Python fast path (optional)

Use `Glob('**/skills/lint/wiki_lint.py')` to locate the script.
If found:
- Read `{vault}/log.md`, look for `# Last lint: <timestamp>`. If found, use
  `--since <timestamp>`.
```
python3 <script_path> {vault} [--since <last_lint_ts>]
```
If exit code 0: present the output. Jump directly to Step 12 (interactive approval).
Execute the "Record lint timestamp" step at the end. Stop.
Otherwise: continue.

## Step 0b — Incremental mode detection

Read `{vault}/log.md`. Look for `# Last lint: <ISO timestamp>`.
- If found: `incremental_mode = true`, `last_lint_ts = <timestamp>`.
  Build `recent_files`: glob `{vault}/wiki/**/*.md`, keep only files
  whose `updated:` ≥ `last_lint_ts`.
- If not found: `incremental_mode = false`. All checks run on the
  full `wiki_files` set.
Report at the top of the output: `"Mode: incremental (since <ts>), N files in scope"` or
`"Mode: full scan"`.

## Step 1 — Check initialization

Verify the existence of:
- `{vault}/wiki/sources/`, `{vault}/wiki/entities/`, `{vault}/wiki/concepts/`, `{vault}/wiki/synthesis/`
- `{vault}/wiki/indexes/`, `{vault}/SCHEMA.md`
If missing: report `missing_structure`, suggest `/mnemo:init`.

## Step 2 — Read index

Read `{vault}/index.md`. Extract all wiki paths from lines
`- [Title](wiki/<subdir>/filename.md)` → build `indexed_paths`.
If shard files `{vault}/wiki/indexes/*.md` exist, read them and include.

## Step 3 — List wiki files

Glob `{vault}/wiki/**/*.md` → `wiki_files`. Exclude `SCHEMA.md` and `wiki/indexes/`.

## Step 4 — Read log

Read `{vault}/log.md`. Build `processed_files` from:
- Current format: `- raw/<filename> | <timestamp> | ingest` → extract `<filename>`
- Legacy format: `- <filename> | <timestamp>` → extract `<filename>`
Ignore lines containing `| generated` or `| skipped`.

## Step 5 — List raw files

Glob `{vault}/raw/*` → `raw_files`.

---

## Pass 1 — Mechanical checks

### Step 6 — Collect issues

| Type | Condition |
|---|---|
| `missing_structure` | Required directory or SCHEMA.md is missing |
| `orphan` | File in `wiki_files` but not in `indexed_paths` |
| `broken_link` | Path in `indexed_paths` but file absent on disk |
| `unprocessed` | File in `raw_files` but not in `processed_files` |
| `oversized` | Wiki page > 800 lines |
| `missing_frontmatter` | Page does not start with `---` YAML |
| `missing_source_citation` | `sources/` page without a `source:` field in frontmatter |
| `no_inbound_links` | Entity or concept page with no incoming `[[wikilink]]` from another page |
| `stale_claim` | Page containing potentially outdated temporal language |
| `superseded_without_history` | Page with `superseded_by:` or `supersedes:` but no `## History` |
| `missing_claims_section` | Entity, concept, or synthesis page without `## Claims` |
| `claim_without_evidence` | Claim bullet missing an `Evidence` field |
| `claim_without_status` | Claim bullet missing a `Status` field |
| `invalid_claim_status` | Claim status is not `active`, `disputed`, or `superseded` |
| `gap_page` | Term appearing in 3+ sources without a dedicated page |

### Step 7 — Check oversized pages

Incremental scope if active (`recent_files`). Read and count lines. Flag > 800.

### Step 8 — Check frontmatter

Incremental scope if active. Read the first 3 lines. Flag if line 1 ≠ `---`.

### Step 9 — Check source citations

Incremental scope if active (intersect with `{vault}/wiki/sources/`). Read the
frontmatter block. Flag if no `source:` field.

### Step 10 — Check inbound links

Incremental scope if active (entity and concept pages in `recent_files`).
For each page, derive its title from the H1 or `title:`. Grep all other
wiki files for `[[<title>]]` or `[[<title>|`. Flag if no match.

### Step 11 — Check stale claims

Incremental scope if active. Scan the body (excluding frontmatter) for:
`currently`, `recently`, `as of`, `at the time of writing`, `in <year>`
(year < current year - 1), `the latest`, `upcoming`, `will be`, `is planned`.
Flag with sentence and line number. Exclude `## Quotes & Excerpts`.

### Step 11c — Superseded without history

Pages with `superseded_by:` or `supersedes:` but no `## History`. Propose
inserting an empty `## History` section before `## Links`.

### Step 11c2 — Structured claims

For pages in `wiki/entities/`, `wiki/concepts/`, and `wiki/synthesis/`:
- If `## Claims` is missing, flag `missing_claims_section` as low/maintenance.
- For each `- **Claim:**` bullet, require `**Evidence:**` and `**Status:**`.
- Flag `claim_without_evidence`, `claim_without_status`, or
  `invalid_claim_status` when applicable.
- Valid statuses are `active`, `disputed`, and `superseded`.
- Do not apply these checks to `sources/`, `activity/`, `indexes/`, or
  graphify-generated pages.

### Step 11b — Detect gap pages

1. For each file in `{vault}/wiki/sources/`, read `## Entities Mentioned` and
   `## Concepts Covered`. Extract `[[Term]]` entries.
2. Build a frequency map: number of distinct sources per term.
3. Keep terms with count ≥ 3.
4. For each frequent term: look for a page in `wiki/entities/` and
   `wiki/concepts/` (case-insensitive match on H1 or `title:`).
5. If no page found: flag `gap_page` with name, count, sources (up to 5),
   suggested filename (`tool-`, `person-`, `pattern-`, `technique-` or bare).
Maximum 10 gaps (descending frequency). Ignore terms < 4 characters.

---

## Pass 2 — Graph analysis

### Step 11d — Compute link graph

For all pages in `{vault}/wiki/**/*.md`:

1. **Build the graph**: for each page, extract all `[[wikilinks]]`
   from its body. Create edges (source → target). Resolve titles to
   file paths via the index or by grepping on H1.

2. **Compute metrics**:
   - **Fan-in** (inbound links) per page
   - **Fan-out** (outbound links) per page
   - **Hubs**: pages with fan-in ≥ 5
   - **Sinks**: pages with fan-out = 0 (excluding `activity/`)
   - **Connected components**: groups of isolated pages (BFS/DFS on undirected graph)
   - **Global statistics**: total pages, total links, density

3. **Flag**:
   - `graph_sink`: page with no outbound links — suggest adding `## Links`
   - `graph_island`: component of < 3 pages disconnected from the main graph

---

## Pass 3 — Semantic checks

### Step 11e — Contradictions

Scan pages whose `updated:` is recent. For each, check whether it
contradicts a linked page. If so, propose adding a `> ⚠️ Contradiction:` callout
to both pages.

### Step 11f — Stale claims from newer sources

For each page flagged `stale_claim` (step 11), check whether a more recent
source invalidates the claim. Suggest re-ingest or searching for a new source.

### Step 11g — Concepts in plain text

Grep concept-shaped nouns that appear as plain text on 3+ pages
without being wikilinks. Suggest dedicated pages.

### Step 11h — Index drift

Compare `{vault}/index.md` with the actual contents of `{vault}/wiki/`. If
out of sync, suggest regeneration.

---

## Step 12 — Present report and interactive approval

Produce a Markdown report grouped by severity:

```
# Wiki lint — <date>

Mode: <incremental / full scan>
Total pages: N  |  Components: N  |  Last log: <date>

## Findings

### Critical
- ⚠️ N contradictions : [[sources/a]] vs [[sources/b]] — claim X vs claim Y
- N broken links (list)

### High
- N orphan pages (list)
- N gap pages (list with suggestions)
- N graph sinks (list)
- N graph islands (list)

### Medium
- N stale claims (list with sentences + line numbers)
- N pages without inbound links

### Low
- N oversized pages
- N missing frontmatter
- N missing source citations
- N structured-claims maintenance findings

## Graph stats
Pages: N  |  Links: N  |  Density: X.XX
Hubs (fan-in ≥ 5): [[page-a]] (12), [[page-b]] (8), ...
Sinks (no outbound): [[page-x]], [[page-y]], ...
Connected components: N
```

Then for each issue, present and wait for approval:

```
── Issue N/Total: <type> ─────────────────────
File: wiki/entities/tool-redis.md
Problem: no inbound [[wikilinks]] found

Proposed edit:
  In wiki/sources/redis-intro.md, add to ## Entities Mentioned:
  - [[Redis]] — in-memory data store

Apply? [y]es / [n]o / [s]kip all of this type / [a]pply all
```

Never apply without explicit approval.

After all issues:
- "X issues found, Y applied, Z skipped."
- If 0: "Knowledge base healthy — 0 issues."

## Step 13 — Record lint timestamp

Fast path: use `Glob('**/mnemo/scripts/update_log.py')` to locate the script.
If found at `<script_path>`, run:
```
python3 <script_path> --vault {vault} --op lint
```
If exit 0 — done.
If exit non-zero — emit `⚠ fast path failed (exit <code>) — falling back to LLM.` then apply LLM fallback.
If script not found → apply LLM fallback below.

LLM fallback — update `{vault}/log.md`:
- If `# Last lint: ...` exists: replace with `# Last lint: <UTC ISO timestamp>`
- Otherwise: add as the first line of `{vault}/log.md`

If lint applied structural changes that affect startup context (index regeneration, graph status pages, frontmatter category/title changes, or deleted/renamed pages), refresh `{vault}/SESSION_BRIEF.md` after recording the lint timestamp:
```
python3 <update_session_brief.py> --vault {vault}
```
Skip the brief update for read-only lint runs or purely local prose fixes.
