# Ingest Workflow Reference

## Overview

Ingest transforms raw source files (articles, papers, notes, transcripts) into a structured, interlinked wiki. Each source produces: one source summary page, one or more entity pages, one or more concept pages, and enrichment edits on up to 15 related existing pages.

The workflow is idempotent: the log prevents any file from being processed twice.

---

## Pre-Conditions

- Knowledge base initialized (`wiki/sources/` exists).
- `SCHEMA.md` defines domain entity types and concept taxonomy.
- `log.md` records all previously processed filenames.

---

## Step-by-Step Workflow

### 1. Check log

Read `log.md`. Build a set of processed filenames. Any file in `raw/` whose name appears in this set is skipped.

### 2. Read SCHEMA.md

Load domain conventions before synthesizing. SCHEMA.md defines which entity types and concept categories apply to this wiki (e.g., `Person`, `Tool`, `Pattern`, `Technique`).

### 3. Chunk large files

- Files ≤ 500 lines: read in full.
- Files > 500 lines: read in ~200-line chunks, accumulate key points and entity/concept names per chunk, then consolidate before writing any pages.

### 4. Write the source page

Path: `wiki/sources/<slug>.md`

Sections: Summary (2–4 sentences), Key Points (bullets), Entities Mentioned (wikilinks), Concepts Covered (wikilinks), Quotes & Excerpts, Links.

### 5. Write or update entity pages

For each significant entity found in the source:
- **New entity**: create `wiki/entities/<type>-<slug>.md`. Verify the source page already lists this entity in `## Entities Mentioned` before creating.
- **Existing entity**: surgical edit — append `- [[Source Title]]` to `## Sources`, update `updated:` field in frontmatter.

### 6. Write or update concept pages

Same pattern as entities, in `wiki/concepts/<category>-<slug>.md`.

### 7. Enrich existing graph (step 5e)

After creating source/entity/concept pages:

1. Build a term set: entity/concept names from steps 5–6 + 5–8 key nouns from the source summary.
2. Find 10–15 related existing pages (2+ term matches) using `wiki_search.py` or `Grep`.
3. Exclude pages already updated in steps 5–6.
4. For each candidate, evaluate 4 criteria:
   - Source provides a **new concrete example** of the entity or concept on this page.
   - Source **refines or contradicts** a claim on this page.
   - Source introduces a **closely related technique** not yet mentioned.
   - Source is by an **author or project already referenced** on this page.
5. If any criterion is met: one surgical append (wikilink bullet to `## Sources`, `## Related Sources`, `## See Also`, or `## Links`). Never rewrite page body.
6. If fewer than 3 candidates found, skip enrichment entirely.

### 8. Update index

- Total pages < 150: append to `index.md` under the matching category heading.
- Total pages ≥ 150: append to the category shard in `wiki/indexes/<category>.md`. Ensure `index.md` links to the shard.

### 9. Update log

Append: `- <filename.ext> | <UTC ISO timestamp>`

---

## Surgical Edit Rules

- **Never rewrite a page body**. Only targeted string replacements (append bullets, update fields).
- **One edit per page per ingest run**. Do not accumulate multiple bullets in one run.
- **Always re-read the raw file** before updating an existing page — never synthesize from memory alone.
- **Check for duplicates** before appending. If the source is already listed, skip.

---

## Output Report

After completing all files:

```
Source pages created: [list]
Entity pages created/updated: [list]
Concept pages created/updated: [list]
Existing pages enriched: [list] (or "none")
Enrichment candidates evaluated but skipped: N
Files skipped (already in log): N
Size warnings: [list]
```
