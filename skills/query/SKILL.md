---
name: query
description: >
  Search the mnemo wiki knowledge base. Uses qmd (hybrid BM25 + vector semantic
  search) if configured at init, otherwise falls back to BM25 ranked retrieval.
  Supports tag:, since:, category:, backlinks:, and top-linked modifiers. Use when
  the user asks "what does my wiki say about X", "search my notes for Y", "find pages
  about Z", "query the knowledge base", "what do I know about X", or "look up X in my
  second brain". Falls back to global knowledge base if local returns no results.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:query). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for faster BM25
  (scripts/wiki_search.py).
metadata:
  author: mnemo contributors
  version: "0.4.2"
allowed-tools: Read Glob Grep Bash
---

## Step 0 — Route by search backend

Read `.mnemo/config.json` (if it exists). Determine the active backend name:

1. If the `search_backend` field is present, use its value.
2. Else if the `semantic_search` field is present, use its value (backward compatibility).
3. Else default to `"bm25"`.

Route by backend name:
- **`"qmd"`** — attempt the qmd path below.
- **`"bm25"`** — skip to Step 0b.
- **Any other value** — warn: `"Unknown search backend '<name>' in config.json — falling back to BM25."` then skip to Step 0b.

**qmd path**: verify qmd is available (`qmd --version`). If available:

Read `qmd_collection` from `config.json` (default: `"mnemo-wiki"` if absent). Set `$QMD_COLLECTION` to this value.

Then run:
```
qmd query --collection "$QMD_COLLECTION" "$ARGUMENTS"
```
If exit code is 0: present the results directly and **stop** — skip steps 0b through 8. If qmd is unavailable or returns a non-zero exit code, warn the user and fall through to Step 0b.

---

## Step 0b — Python fast path (optional)

Before running the instruction-based search below, attempt the faster Python path:

1. Use `Glob('**/mnemo/scripts/wiki_search.py')` to locate the search script.
2. If found at `<script_path>`, run:
   ```
   python3 <script_path> .mnemo/wiki "$ARGUMENTS"
   ```
   Append any modifiers extracted from `$ARGUMENTS` as CLI flags:
   - `category:<value>` → `--type <value>`
   - `tag:<value>` → `--tag <value>`
   - `since:<date>` → `--since <date>`
   - `backlinks:<title>` → `--backlinks "<title>"`
   - `top-linked` → `--top-linked`
3. If exit code is 0, present the script output directly and **stop** — do not run steps 1–8.
4. If Python is unavailable, the script is not found, or exit code is non-zero, continue to Step 1 below.

Arguments: $ARGUMENTS

Search the knowledge base for "$ARGUMENTS".

## Step 1 — Parse all modifiers

Extract all modifiers from `$ARGUMENTS` before searching. The remaining text after removing modifiers is the **search term** (may be empty if only modifiers are given).

| Modifier | Syntax | Effect |
|---|---|---|
| Category filter | `category:sources` `category:entities` `category:concepts` `category:synthesis` | Restrict to that subdir |
| Tag filter | `tag:<value>` | Only pages whose frontmatter `tags:` contains `<value>` |
| Date filter | `since:<YYYY-MM-DD>` | Only pages whose frontmatter `created:` is on or after that date |
| Backlinks | `backlinks:<Page Title>` | Find all pages containing `[[<Page Title>]]` — ignore search term |
| Top-linked | `top-linked` | Rank all pages by number of inbound `[[wikilinks]]` — ignore search term |

Multiple modifiers can be combined: `tag:redis since:2026-01-01 performance`

---

## Step 2 — Handle special modes first

**If `backlinks:<Page Title>` is present:**
- Grep all `.mnemo/wiki/**/*.md` files for `[[<Page Title>]]` or `[[<Page Title>|`.
- List every matching file with a snippet showing the wikilink in context.
- Report: "Pages linking to [[<Page Title>]]: N found." Skip steps 3–7.

**If `top-linked` is present:**
- For each page in `wiki/entities/` and `wiki/concepts/`, count how many other wiki files contain `[[<its title>]]`.
- Sort descending. Report the top 10 with their inbound link count.
- Apply `category:` and `tag:` filters if also present.
- Skip steps 3–7.

---

## Step 3 — Build the candidate pool (index-first, bounded)

Read `.mnemo/index.md`. If shard files exist in `wiki/indexes/` (`sources.md`, `entities.md`, `concepts.md`, `synthesis.md`), read the relevant ones based on the `category:` filter (or all if no filter).

From the index entries, apply filters in order:

1. **Tag filter** — if `tag:<value>` is set: read each candidate's YAML frontmatter (lines between `---` delimiters only, not the body). Keep only pages whose `tags:` list contains `<value>` (case-insensitive).
2. **Date filter** — if `since:<YYYY-MM-DD>` is set: from the remaining candidates, keep only pages whose frontmatter `created:` date is ≥ the given date.
3. **Term match** — if a search term remains: from the remaining candidates, score each by whether the search term appears in the index title (weight 2) or frontmatter `tags:` (weight 1). Keep the top 5 by score.

If no search term (only filters), keep all candidates that pass the filters (up to 10).

---

## Step 4 — Read candidate pages

Read the candidate pages identified in step 3 (up to 5, or 10 for filter-only queries). Extract snippets (~200 chars around the first occurrence of the search term, or the first body paragraph if no search term).

---

## Step 5 — Evaluate coverage

If candidates sufficiently answer the query (≥ 2 strong matches or filter-only mode), go to step 7.

If coverage is insufficient (< 2 strong matches and a search term exists), proceed to step 6.

---

## Step 6 — BM25-style full-text fallback

- Break the search term into individual terms (ignore words shorter than 3 chars).
- For each term, scan body content of unread wiki files (scoped to target subdirs).
- Score each file: +2 per term matched in H1 title, +1 per term matched in body, +1 per term matched in `tags:`.
- Read the top 5 scoring files not already read.
- Label these results as "BM25-style matches".

---

## Step 7 — Global fallback

If no local results after steps 3–6, repeat steps 3–6 in `~/.mnemo/` if it exists.

Then proceed to Step 8 to present results.

---

## Step 8 — Present results (Layer 1 — compact index)

Present a compact summary first. Do **not** dump full page bodies unless the user asks.

```
## Results for "<original query>"
Filters active: tag:redis, since:2026-01-01   ← omit line if no filters
Pages read: N   |   Activity logs included: yes/no

1. **[[Title]]** `concepts` — *one-line snippet (≤120 chars)*
2. **[[Title]]** `entities` — *one-line snippet*
3. **[[Title]]** `synthesis` — *one-line snippet*
```

Rules for Layer 1:
- One line per result. Title + category badge + snippet only.
- Snippet = first 120 chars of the first body paragraph after the H1.
- Number each result so the user can request expansion by number.
- If no results: say so explicitly. Never invent content.
- Always offer: "Type a number to expand, or ask a follow-up question."

*(`Activity logs included` reflects whether `$INCLUDE_ACTIVITY` was set to true by Step 0c — set to "yes" if activity intent was detected, "no" otherwise.)*

---

## Step 9 — Layer 2: expand on demand

Trigger: user types a result number (e.g. "2"), "expand 2", "show me #3", "détaille le 1", "mostra il 2", "zeig mir 3", "muéstrame el 2", or any equivalent in any language.

Action: re-read the full page for that result number and present:
- Full frontmatter (title, category, tags, created)
- Full page body
- All wikilinks in `## Links`

Do not re-run the search. Use the page path already found in Steps 0, 0b, or 3–6 (whichever ran).

If the requested number is outside the result set (e.g., user asks for result 7 but only 3 were returned): say so and offer the valid range.
