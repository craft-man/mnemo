---
name: ingest
description: >
  Process raw files in raw/ into synthesized, categorized wiki pages via LLM
  analysis. Extracts entities and concepts, creates bidirectional wikilinks, and
  enforces source citations. Use when the user says "ingest this", "add this to
  my wiki", "process my notes", "compile this paper into the knowledge base",
  "add to second brain", or drops new files into raw/ and asks to process them.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:ingest). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for BM25 search
  acceleration (scripts/wiki_search.py).
metadata:
  author: mnemo contributors
  version: "0.6.0"
allowed-tools: Read Write Edit Glob Grep Bash
---

Ingest all pending files from `.mnemo/<project-name>/raw/` into the wiki.

## Flag: `--global`

If `--global` is present in the invocation arguments, substitute every `.mnemo/<project-name>/` path below with `~/.mnemo/`. All reads, writes, and log updates operate on the global knowledge base instead of the local one. This is useful for ingesting sources that should be available across multiple projects.

## Steps

**1. Check init** — if `.mnemo/<project-name>/wiki/sources/` does not exist, stop:
> "Knowledge base not initialized. Run `/mnemo:init` first."

**2. Read SCHEMA.md** — read `.mnemo/<project-name>/SCHEMA.md`. Use it to guide categorization, entity types, and naming during synthesis.

**3. Read the log** — read `.mnemo/<project-name>/log.md`. Build a set of already-processed filenames from lines of the form:
```
- filename.ext | 2026-01-15T10:30:00+00:00
```

**4. List raw files** — glob `.mnemo/<project-name>/raw/*`. Skip directories. Skip filenames already in the processed set.

**5. For each unprocessed file — synthesize:**

**File size check first** — count the lines in the file before reading:
- **≤ 500 lines**: read the full file at once, proceed to analysis below.
- **> 500 lines**: read in chunks of ~200 lines. For each chunk:
  - Extract key points, entities, and concepts found in that chunk.
  - Keep a running accumulator (list of key points, entity names, concept names).
  - After all chunks are processed, consolidate the accumulator into a single synthesis before writing any wiki pages.
  - Never synthesize from a partial chunk alone — always consolidate first.

Then perform the following analysis on the full (or consolidated) content:

**a) Source page** — write `wiki/sources/<slug>.md`:

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

<2–4 sentence synthesis of the source's main argument or content. Never copy-paste raw text without synthesis.>

## Key Points

- <extracted key point 1>
- <extracted key point 2>
- <extracted key point 3>

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

**b) Entity pages** — for each significant entity (person, tool, project, system) extracted from the source, using SCHEMA.md entity types as a guide:
- Check if `wiki/entities/<type>-<slug>.md` already exists.
- If it exists:
  - **Re-read the original raw file** (the current file being ingested) to ground the update in the source — never synthesize from memory alone.
  - **Contradiction check** — before making any edit, scan the existing entity page body (skip `## Sources` and `## Links` sections) for sentences containing the entity name alongside an affirmative claim. Compare with the new source content. A contradiction is present when the new source contains a negation word (`not`, `no longer`, `unlike`, `contrary`, `incorrect`, `actually`, `however`) adjacent to the same subject as an existing claim. If found:
    - Surface the conflict: show the existing claim (file + line number) and the conflicting statement from the new source.
    - **Do not proceed with the surgical edit.** Check whether the contradiction contains replacement language (`replaced by`, `superseded by`, `deprecated in favor of`, `no longer used`, `remplacé par`, `obsolète`):
      - If replacement language is present, ask: `"Potential contradiction detected — [u]pdate existing claim / [k]eep both / [h]istory (mark superseded) / [s]kip this file?"`
      - Otherwise, ask: `"Potential contradiction detected — [u]pdate existing claim / [k]eep both / [s]kip this file?"`
    - If `[u]pdate`: apply a targeted replacement fixing the contradicted sentence, then proceed with the surgical edit.
    - If `[k]eep both`: add a `> **Note:** [[<New Source Title>]] presents a differing view.` line below the conflicting sentence, then proceed with the surgical edit.
    - If `[h]istory` (replacement scenario only):
      1. In the existing page's YAML frontmatter, insert `superseded_by: "<New Entity Title>"` after the last existing frontmatter field (before the closing `---`).
      2. Append a `## History` section before `## Links` in the existing page body:
         ```
         ## History

         - **<today-YYYY-MM-DD>**: Replaced by [[<New Entity Title>]] — see [[<New Source Title>]]
         ```
         If a `## History` section already exists, append the new bullet to it instead.
      3. On the new entity page being created for the replacement, add `supersedes: "<Old Entity Title>"` to its frontmatter (insert after the `updated:` field).
      4. Then proceed with the surgical edit (append source bullet, update `updated:` field).
    - If `[s]kip`: log the filename as processed but do not modify the entity page. Note the skipped contradiction in the step 8 report.
  - **Surgical edit only**: two targeted string replacements:
    1. Append `- [[<New Source Title>]]` as a new bullet in the existing `## Sources` section.
    2. Update the `updated:` field in the frontmatter: replace `updated: <old-date>` with `updated: <today-YYYY-MM-DD>`.
    If the source is already listed in `## Sources`, skip both edits.
- If new: create `wiki/entities/<type>-<slug>.md`. **Inbound link required**: the source page (`wiki/sources/<source-slug>.md`) must already list this entity in its `## Entities Mentioned` section — verify before writing. If not present, add it first.

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

<Synthesized description of the entity based on source content.>

## Sources

- [[<Source Title>]]

## Links

- [[<Related Concept Name>]]
```

**c) Concept pages** — for each significant concept (pattern, technique, idea) extracted, using SCHEMA.md concept taxonomy as a guide:
- Check if `wiki/concepts/<category>-<slug>.md` already exists.
- If it exists:
  - **Re-read the original raw file** to ground the update in the source — never synthesize from memory alone.
  - **Contradiction check** — before making any edit, scan the existing concept page body (skip `## Sources` and `## Links` sections) for sentences containing the concept name alongside a definitional or behavioral claim. Compare with the new source content. A contradiction is present when the new source contains a negation word (`not`, `no longer`, `unlike`, `contrary`, `incorrect`, `actually`, `however`) adjacent to the same subject as an existing claim. If found:
    - Surface the conflict: show the existing claim (file + line number) and the conflicting statement from the new source.
    - **Do not proceed with the surgical edit.** Check whether the contradiction contains replacement language (`replaced by`, `superseded by`, `deprecated in favor of`, `no longer used`, `remplacé par`, `obsolète`):
      - If replacement language is present, ask: `"Potential contradiction detected — [u]pdate existing claim / [k]eep both / [h]istory (mark superseded) / [s]kip this file?"`
      - Otherwise, ask: `"Potential contradiction detected — [u]pdate existing claim / [k]eep both / [s]kip this file?"`
    - If `[u]pdate`: apply a targeted replacement fixing the contradicted sentence, then proceed with the surgical edit.
    - If `[k]eep both`: add a `> **Note:** [[<New Source Title>]] presents a differing view.` line below the conflicting sentence, then proceed with the surgical edit.
    - If `[h]istory` (replacement scenario only):
      1. In the existing page's YAML frontmatter, insert `superseded_by: "<New Concept Name>"` after the last existing frontmatter field (before the closing `---`).
      2. Append a `## History` section before `## Links` in the existing page body:
         ```
         ## History

         - **<today-YYYY-MM-DD>**: Replaced by [[<New Concept Name>]] — see [[<New Source Title>]]
         ```
         If a `## History` section already exists, append the new bullet to it instead.
      3. On the new concept page being created for the replacement, add `supersedes: "<Old Concept Name>"` to its frontmatter (insert after the `updated:` field).
      4. Then proceed with the surgical edit (append source bullet, update `updated:` field).
    - If `[s]kip`: log the filename as processed but do not modify the concept page. Note the skipped contradiction in the step 8 report.
  - **Surgical edit only**: two targeted string replacements:
    1. Append `- [[<New Source Title>]]` as a new bullet in the existing `## Sources` section.
    2. Update the `updated:` field in the frontmatter: replace `updated: <old-date>` with `updated: <today-YYYY-MM-DD>`.
    If the source is already listed in `## Sources`, skip both edits.
- If new: create `wiki/concepts/<category>-<slug>.md`. **Inbound link required**: the source page must already list this concept in its `## Concepts Covered` section — verify before writing. If not present, add it first.

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

<Synthesized definition or explanation.>

## Sources

- [[<Source Title>]]

## Links

- [[<Related Entity Name>]]
```

**d) Page size check** — after writing each page:
- Count lines. If > 800: split into `<slug>-part-1.md` and `<slug>-part-2.md`. Update the source page `## Links` to reference both parts. Warn the user.
- If 400–800 lines: warn the user the page is large.

**e) Enrich existing graph** — after source, entity, and concept pages are written, enrich related existing pages:

1. **Build a term set** — collect 10–20 representative terms from the source:
   - The key entities and concepts extracted in steps b and c (their names/titles)
   - The 5–8 most distinctive non-stopword nouns from the source's Summary and Key Points

2. **Find related candidates** — two options (use whichever is faster):
   - **If `wiki_search.py` is available**: run `python3 <script_path> .mnemo/<project-name>/wiki "<terms joined by space>"` and collect the top results.
   - **Otherwise**: for each term in the term set, use Grep to search `.mnemo/<project-name>/wiki/**/*.md` for that term (case-insensitive). Collect file paths that match 2+ terms.

   Exclude pages already created or updated in steps b and c.

3. **Select top 10–15 candidates** — rank by number of term-set overlaps. Take the top 10–15 (or all candidates if fewer than 15 remain after filtering). If fewer than 3 candidates are found, skip step 5e entirely.

4. **For each candidate — evaluate and edit:**

   a. Read the candidate page.

   b. The new source adds value to this page if ANY of these is true:
      - The source provides a **new concrete example** of the entity or concept on this page.
      - The source **refines or contradicts** a claim on this page.
      - The source introduces a **closely related technique or pattern** not yet mentioned.
      - The source is by an **author or project already referenced** on this page.

   c. If none of the above — **skip this page**. Never add a link just because terms overlap.

   d. If yes — make ONE surgical edit, choosing the most appropriate section:
      - If `## Sources` or `## Related Sources` section exists: append `- [[<New Source Title>]]` as a new bullet.
      - If `## See Also` or `## Links` section exists but no Sources section: append `- [[<New Source Title>]]` there.
      - If neither: append `\n## Related Sources\n\n- [[<New Source Title>]]` before the final `## Links` section.

      **Never rewrite the page body. One append per page, maximum.**

5. Collect results for the report:
   - `enriched_pages`: list of pages that received an edit
   - `skipped_candidates`: count of candidates evaluated but not enriched

**6. Update index** — for each new page written:
- Count total pages in `.mnemo/<project-name>/wiki/**/*.md`.
- If total < 150: append to `.mnemo/<project-name>/index.md` under the matching category heading (`## Sources`, `## Entities`, `## Concepts`, `## Synthesis`).
- If total >= 150: append to `.mnemo/<project-name>/wiki/indexes/<category>.md` (create the file if it doesn't exist). Ensure `.mnemo/<project-name>/index.md` has a link to each shard: `- [Sources Index](wiki/indexes/sources.md)` etc.

**7. Update log** — append to `.mnemo/<project-name>/log.md`:
```
- raw/<original_filename> | <UTC ISO timestamp> | ingest
```

**7a. Sync qmd index (if configured)** — read `.mnemo/<project-name>/config.json`. Determine backend: use `search_backend` if present, else `semantic_search` if present, else `"bm25"`. If backend is `"qmd"`: read `qmd_collection` (default `"mnemo-wiki"`), then run:
```
qmd update "$QMD_COLLECTION"
```
This indexes all pages written or modified during this ingest session. If qmd returns a non-zero exit code, warn in the step 8 report ("qmd index sync failed — run `qmd update $QMD_COLLECTION` manually") but do not abort. BM25 search remains available.

**7b. Suggest synthesis pages** — after updating the log, identify entity and concept pages that now have enough sources to justify a synthesis but don't have one yet:

1. For each entity/concept page **created or updated** during steps 5b and 5c in this session:
   - Read its `## Sources` section and count the bullet entries.
   - If count ≥ 3: grep `wiki/synthesis/**/*.md` for the entity/concept name (case-insensitive match on frontmatter `title:` or H1).
   - If no synthesis page found: add to `synthesis_candidates`.

2. If `synthesis_candidates` is non-empty, include in the step 8 report under a dedicated section. Do not create synthesis pages automatically — only surface the suggestion. The user initiates via `/mnemo:save`.

**8. Report:**
- Source pages created: list names
- Entity pages created or updated: list names
- Concept pages created or updated: list names
- Existing pages enriched (step 5e): list names (or "none")
- Enrichment candidates evaluated but skipped: count
- Contradictions detected: list entity/concept name + resolution chosen (update / keep both / skipped), or "none"
- Files skipped (already in log): count
- Any size warnings
- Synthesis opportunities (step 7b) — if any: "The following topics now have 3+ sources and no synthesis page — consider `/mnemo:save` to create one:"
  - [[Entity/Concept Name]] (N sources: [[Source A]], [[Source B]], [[Source C]], …)
- "Run `/mnemo:lint` to verify knowledge base health."
