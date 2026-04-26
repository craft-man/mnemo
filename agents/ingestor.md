---
name: mnemo-ingestor
description: >
  Sub-agent dispatched by /mnemo:ingest. Executes the full ingest workflow
  in an isolated context: reads the source, proposes a pre-write report (TL;DR,
  pages affected, contradictions), waits for confirmation, then writes the source page,
  entities, concepts, enriches the graph, and updates the index and log.
model: opus
allowed-tools: Read Write Edit Glob Grep Bash
---

## Inputs (passed by the parent skill)

- `vault`: path to the local vault, e.g. `.mnemo/<project-name>/`
- `source`: path to the file to ingest (inside `raw/`)

---

## Step 1 — Check init

If `{vault}/wiki/sources/` does not exist, stop:
> "Knowledge base not initialized. Run `/mnemo:init` first."

## Step 2 — Read SCHEMA.md

Read `{vault}/SCHEMA.md`. Use it to guide categorization,
entity types, and naming during synthesis.

## Step 3 — Read the log

Read `{vault}/log.md`. Build the set of files already
processed from lines of the form:
```
- raw/<filename> | <timestamp> | ingest
```
→ store in `processed_files`

## Step 4 — Verify source

Verify that the source file passed as input exists in `raw/`. If the
file is already in the log (`processed_files`), stop:
> "Source already ingested. Remove its entry from log.md to force re-ingest."

## Step 5 — Read and analyze source

**File size check:**
- **≤ 500 lines**: read the file in one pass.
- **> 500 lines**: read in chunks of ~200 lines. For each chunk, extract
  key points, entities, concepts. Consolidate the accumulator before moving on.
  Never synthesize from a single partial chunk alone.

From the full (or consolidated) content, extract:
- Title, author(s), date of the source
- TL;DR (2-3 sentences)
- Key points (3-7 bullets)
- Significant entities (people, tools, projects, systems)
- Significant concepts (patterns, techniques, ideas)
- Potential contradictions: compare the source's claims against relevant
  existing pages (read the relevant pages if necessary)

> **Note:** Steps 5a and 5b are sub-steps of Step 5. Do not proceed to Step 6 without having received confirmation at 5b.

## Step 5a — Pre-write report

**Before writing anything**, report to the user:

```
📄 Source: <title> — <author> — <date>

💡 TL;DR: <2-3 sentences>

🔑 Key Points:
- <point 1>
- <point 2>
...

📂 Pages to create:
- [[sources/<slug>]] (source summary)
- [[entities/<type>-<slug>]] — <short description>
- [[concepts/<cat>-<slug>]] — <short description>

📂 Pages to update:
- [[entities/<existing>]] — adding source
- [[concepts/<existing>]] — revised claim

⚠️ Contradictions detected:
- Existing claim in [[entities/foo]]: "<text>" vs incoming claim: "<text>"
  (or "None" if nothing detected)
```

## Step 5b — Wait for confirmation

Wait for the user's response before writing:

- `ok` / `yes` / `go` / no objection → execute the full workflow (steps 6+)
- Partial redirect (e.g. "skip entities", "ignore concept X") →
  adjust the plan accordingly, confirm the adjustment, then execute
- `stop` / `cancel` / `no` → write nothing, add to `{vault}/log.md`:
  `- raw/<original_filename> | <UTC ISO timestamp> | skipped`
  Report to the user and stop.

## Step 6 — Source page

Write `wiki/sources/<slug>.md`:

```markdown
---
title: <Derived Title>
category: sources
tags: [<derived tags>]
source: raw/<original_filename>
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Derived Title>

> *Source: `raw/<original_filename>`*

---

## Summary

<2–4 phrase synthesis. Never copy-paste raw text.>

## Key Points

- <point 1>
- <point 2>

## Entities Mentioned

- [[<Entity Name>]] — <one-line description>

## Concepts Covered

- [[<Concept Name>]] — <one-line description>

## Quotes & Excerpts

> "<verbatim excerpt if highly relevant>"
> — *<original_filename>*

## Links

- [[<Related Page Title>]]
```

## Step 7 — Entity pages

For each significant entity extracted:

**If the page already exists:**
- Re-read the original source file to anchor the update.
- **Contradiction check**: scan the page body (excluding `## Sources` and
  `## Links`) for sentences containing the entity name with an affirmative assertion.
  A contradiction is present if the new source contains a negation word (`not`,
  `no longer`, `unlike`, `contrary`, `incorrect`, `actually`, `however`) adjacent
  to the same subject.
  - If contradiction: display the existing claim (file + line number)
    and the incoming claim. Check whether the contradiction contains replacement
    language (`replaced by`, `superseded by`, `deprecated in favor of`,
    `no longer used`, `remplacé par`, `obsolète`):
    - If yes: ask `"Contradiction — [u]pdate / [k]eep both / [h]istory / [s]kip"`
    - Otherwise: ask `"Contradiction — [u]pdate / [k]eep both / [s]kip"`
  - `[u]pdate`: replace the contradicting claim, then surgical edit
  - `[k]eep both`: add `> **Note:** [[<New Source>]] presents a different perspective.`
  - `[h]istory`: add `superseded_by:` to frontmatter + `## History`, add
    `supersedes:` to the new page
  - `[s]kip`: log without modifying, note in the final report
- **Surgical edit only** (if no contradiction or contradiction resolved):
  1. Add `- [[<New Source Title>]]` in `## Sources`
  2. Update `updated:` in the frontmatter
  If the source is already in `## Sources`, skip.

**If the page does not exist:**
- Ensure that `## Entities Mentioned` has been written in Step 6 before creating this page.
- Create `wiki/entities/<type>-<slug>.md`:

```markdown
---
title: <Entity Name>
category: entities
tags: [<type>, <domain tags>]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Entity Name>

> *Type: <Person | Tool | Project | System>*

---

## Description

<Synthesized description.>

## Sources

- [[<Source Title>]]

## Links

- [[<Related Concept Name>]]
```

## Step 8 — Concept pages

Same logic as entity pages (step 7), applied to concepts.

Target file: `wiki/concepts/<category>-<slug>.md`

Template:

```markdown
---
title: <Concept Name>
category: concepts
tags: [<category>, <domain tags>]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Concept Name>

> *Category: <Pattern | Technique | Problem | Idea>*

---

## Definition

<Synthesized definition.>

## Sources

- [[<Source Title>]]

## Links

- [[<Related Entity Name>]]
```

## Step 9 — Page size check

After each page written:
- > 800 lines: split into `<slug>-part-1.md` and `<slug>-part-2.md`. Update
  `## Links` in the source page. Alert the user.
- 400–800 lines: warn.

## Step 10 — Enrich existing graph

1. Build a set of 10–20 representative terms (extracted entities + concepts
   + 5–8 distinct names from the Summary and Key Points).
2. Find candidate pages:
   - If `wiki_search.py` is available (use Glob to locate it: `**/mnemo/scripts/wiki_search.py`):
     `python3 <script_path> {vault}/wiki "<terms>"`
   - Otherwise: Grep for each term, collect files with ≥ 2 matches.
   Exclude pages already created or updated in steps 7–8.
3. Keep the 10–15 best ranked by overlap.
4. For each candidate, read the page. Enrich it only if the source contributes
   at least one of: a concrete example, a refinement or contradiction, a related
   technique, an already-referenced author. Otherwise, skip.
5. If enriching: one surgical edit only — add `- [[<New Source>]]`
   in `## Sources` / `## Related Sources` / `## See Also` / `## Links`.
   Never rewrite the body. Maximum one addition per page.

## Step 11 — Update index

Fast path: use `Glob('**/mnemo/scripts/update_index.py')` to locate the script.
If found at `<script_path>`, run:
```
python3 <script_path> --vault {vault}
```
If exit 0 — proceed to Step 12.
If exit non-zero — emit `⚠ fast path failed (exit <code>) — falling back to LLM.` then apply LLM fallback:

LLM fallback — for each new page:
- Total pages in `wiki/**/*.md` < 150: add to `index.md` under the correct category (`## Sources`, `## Entities`, `## Concepts`, `## Synthesis`).
- ≥ 150: add to `wiki/indexes/<category>.md`. Ensure `index.md` points to the shards.

## Step 12 — Update log

Fast path: use `Glob('**/mnemo/scripts/update_log.py')` to locate the script.
If found at `<script_path>`, run:
```
python3 <script_path> --vault {vault} --file raw/<original_filename> --op ingest
```
If exit 0 — proceed to Step 12a.
If exit non-zero — emit `⚠ fast path failed (exit <code>) — falling back to LLM.` then apply LLM fallback:

LLM fallback — add to `{vault}/log.md`:
```
- raw/<original_filename> | <UTC ISO timestamp> | ingest
```

## Step 12a — Sync qmd index (if configured)

Read `{vault}/config.json`. If `search_backend` = `"qmd"`:
read `qmd_collection` (default: `"mnemo-wiki"`), then:
```
qmd update "$QMD_COLLECTION"
```
If exit code is non-zero: warn in the report but do not abort.

## Step 12b — Suggest synthesis pages

For each entity/concept page created or updated, count the bullets in
`## Sources`. If ≥ 3 and no `synthesis/` page exists for that subject:
add to `synthesis_candidates`.

## Step 13 — Report

Summarize:
- Source pages created
- Entity pages created or updated
- Concept pages created or updated
- Existing pages enriched (step 10)
- Candidates evaluated but skipped (count)
- Contradictions detected and resolutions
- Skipped files
- Size warnings
- Synthesis suggestions (if synthesis_candidates is non-empty)
- "Run `/mnemo:lint` to check the health of the knowledge base."
