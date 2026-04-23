# Page Conventions Reference

## Frontmatter (Required on Every Page)

```yaml
---
title: Page Title
category: sources | entities | concepts | synthesis
tags: [tag1, tag2]
source: raw/filename.ext   # required for sources/ pages only
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

**Rules:**
- Every wiki page must start with YAML frontmatter — no exceptions.
- `source:` is required for all `wiki/sources/` pages.
- `created:` is set once at creation and never changed.
- `updated:` is set to today on every surgical edit.
- `tags:` should use terms from the domain taxonomy in `SCHEMA.md`.

---

## Page Body Structure

```markdown
# Page Title   ← H1 exactly once, matches frontmatter title

> *Source: `raw/filename.ext`*  ← attribution (or generation timestamp for synthesis)

---

## Section Heading   ← H2 for all sections

Body text referencing [[Related Concept]] and [[Entity Name]].

## Links

- [[Related Page Title]]
- [[Another Page Title]]
```

**Rules:**
- H1 = page title only. Never use H1 for sections.
- Always end with a `## Links` section.
- Wikilinks: `[[Exact H1 Title]]` — always the exact H1 title of the target page, not a filename.
- Wikilinks are Obsidian-compatible.

---

## File Naming Conventions

| Category | Pattern | Example |
|---|---|---|
| `sources/` | `kebab-case.md` | `python-asyncio-guide.md` |
| `entities/` | `<type>-<name>.md` | `tool-redis.md`, `person-karpathy.md` |
| `concepts/` | `<category>-<name>.md` | `pattern-saga.md`, `technique-rag.md` |
| `synthesis/` | `kebab-case.md` | `btree-vs-hash-comparison.md` |

Entity `<type>` matches the entity types defined in `SCHEMA.md` (e.g., `tool`, `person`, `project`, `system`).  
Concept `<category>` matches the concept taxonomy in `SCHEMA.md` (e.g., `pattern`, `technique`, `problem`, `idea`).

---

## Page Title Conventions

| Item | Convention | Example |
|---|---|---|
| Page title (H1 and frontmatter) | Title Case | `Redis — In-Memory Data Store` |
| Index entry | `- [Title](wiki/<subdir>/file.md)` | `- [Redis](wiki/entities/tool-redis.md)` |
| Log entry | `- filename \| ISO timestamp` | `- notes.md \| 2026-04-22T14:00:00+00:00` |

---

## Page Size Limits

- **Soft cap — 400 lines**: warn, consider splitting.
- **Hard cap — 800 lines**: must split into `<slug>-part-1.md` and `<slug>-part-2.md`.

---

## Category Semantics

| Category | What goes here |
|---|---|
| `sources/` | One page per ingested raw source. Summarizes content, lists entities/concepts found. |
| `entities/` | Specific people, tools, projects, or systems. Accumulates source references over time. |
| `concepts/` | Abstract ideas, patterns, techniques, problems. Accumulates source references over time. |
| `synthesis/` | Cross-source analyses, comparisons, AI-generated insights. Saved via `/mnemo:save`. |

---

## Prohibited Patterns

- No wiki pages outside `wiki/`.
- No sources page without `source:` in frontmatter.
- No H1 for section headings — only for the page title.
- No duplicate content — query first, then decide to save.
- No wikilink to a page that doesn't exist yet (create the page first, then link).
