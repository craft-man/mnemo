---
name: save
description: >
  Save AI-generated content — summaries, comparisons, analyses, insights — as a
  permanent, categorized wiki page with YAML frontmatter. Routes to sources,
  entities, concepts, or synthesis based on content type. Use when the user says
  "save this", "add this to my wiki", "store this analysis", "keep this insight",
  "create a wiki page for this", or "persist this summary". Asks for a title and
  category before writing.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:save). Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.8.0"
allowed-tools: Read Write Glob
---

Arguments: $ARGUMENTS

## Flag: `--global`

If `--global` is present in `$ARGUMENTS`, substitute every `.mnemo/<project-name>/` path below with `~/.mnemo/`. All reads, writes, index updates, and log entries operate on the global knowledge base. Strip `--global` from `$ARGUMENTS` before using it as the page title.

Save generated content to the wiki.

## Steps

**1. Get title** — use `$ARGUMENTS` as the title if provided. Otherwise ask the user. Reject vague titles like "notes" or "stuff".

**2. Determine category** — ask the user which category best fits (unless obvious from context):
- `synthesis` — cross-source analyses, comparisons, summaries (default for AI-generated insights)
- `concepts` — definitions, patterns, techniques
- `entities` — a specific person, tool, or project

**3. Slugify** — derive filename: lowercase, spaces and underscores → hyphens, remove non-alphanumeric chars except hyphens. Example: `"Python vs. JS (2024)"` → `python-vs-js-2024.md`.

**4. Check for existing page** — check if `.mnemo/<project-name>/wiki/<category>/<slug>.md` exists. If yes, confirm overwrite with the user. On overwrite: keep the original `created:` date, set `updated:` to today's date.

**5. Write YAML frontmatter + page** — write `.mnemo/<project-name>/wiki/<category>/<slug>.md`:

```markdown
---
title: <Title>
category: <category>
tags: [<ask user or derive from content>]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <Title>

> *Generated — <YYYY-MM-DD HH:MM UTC>*

---

<content>

## Links

- [[<Related Page Title>]]
```

**6. Check page size** — count lines. If > 800: warn the user and offer to split. If 400–800: note the page is large.

**6b. Enrich existing graph** — after writing the page, link related existing pages back to it:

1. **Build a term set** — collect 10–20 representative terms from the saved content:
   - All `[[wikilinks]]` found in the saved page body
   - The 5–8 most distinctive non-stopword nouns from the page title and first two paragraphs

2. **Find related candidates** — two options (use whichever is faster):
   - **If `wiki_search.py` is available**: run `python3 <script_path> .mnemo/<project-name>/wiki "<terms joined by space>"` and collect the top results.
   - **Otherwise**: for each term in the term set, Grep `.mnemo/<project-name>/wiki/**/*.md` for that term (case-insensitive). Collect file paths matching 2+ terms.

   Exclude the newly saved page itself.

3. **Select top 10 candidates** — rank by term-set overlap count. Take the top 10 (or all if fewer). If fewer than 3 candidates, skip step 6b entirely.

4. **For each candidate — evaluate and edit:**

   a. Read the candidate page.

   b. Add a backlink only if ANY of these is true:
      - The saved page provides a **direct analysis, comparison, or synthesis** involving an entity or concept on this page.
      - The saved page **contradicts or refines** a claim on this page.
      - The saved page is a **synthesis page** and this candidate is one of the entities/concepts it covers.

   c. If none apply — **skip**. Never add a link just because terms overlap.

   d. If yes — one surgical edit:
      - If a `## See Also`, `## Synthesis`, or `## Links` section exists: append `- [[<Saved Page Title>]]` as a new bullet.
      - If none: append `\n## See Also\n\n- [[<Saved Page Title>]]` before the end of the file.

      **Never rewrite the page body. One append per candidate, maximum.**

5. Report enriched pages: list names (or "none enriched").

**7. Update index** — if the file is new (not an overwrite):
- Count total pages in `.mnemo/<project-name>/wiki/**/*.md`.
- If total < 150: append to `.mnemo/<project-name>/index.md` under the `## <Category>` heading (capitalize the category name).
- If total >= 150: append to `.mnemo/<project-name>/wiki/indexes/<category>.md` (create if needed). Ensure `index.md` links to it: `- [<Category> Index](wiki/indexes/<category>.md)`.

**8. Update log** — append to `.mnemo/<project-name>/log.md`:
```
- wiki/<category>/<slug>.md | <UTC ISO timestamp> | generated
```

**9. Confirm:** file path created, category, new vs. overwrite, index entry added.
