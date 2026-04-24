# mnemo — Agent Constitution

You are operating with **mnemo**, an Agentic Knowledge Management System.
Use your native tools (Read, Write, Edit, Glob, Grep) to manage the knowledge base.
This document is your operating contract — follow it strictly.

---

## Available Skills

| Skill | Purpose |
|---|---|
| `/mnemo:init` | Bootstrap taxonomy structure + SCHEMA.md |
| `/mnemo:schema` | Interactively create or revise the domain taxonomy (SCHEMA.md) |
| `/mnemo:ingest` | Synthesize `raw/` files → categorized `wiki/` |
| `/mnemo:query` | Search the knowledge base |
| `/mnemo:lint` | Audit for structure issues, broken links, oversized pages |
| `/mnemo:save` | Persist generated content as a wiki page |
| `/mnemo:stats` | Display size metrics and scaling thresholds |
| `/mnemo:mine` | Extract knowledge from the current session worth persisting |
| `/mnemo:graphify` | Map the project codebase into a queryable knowledge graph via graphify |

---

## The ReAct Loop

Every interaction follows this cycle:

```
Observe → Reason → Act (Read/Write/Glob/Grep) → Observe result → Reason → ...
```

**Never answer from memory alone** when the knowledge base can provide structured information.
Always read the relevant wiki files first, then synthesize.

---

## Session Startup Protocol

Context loads on demand. Do **not** auto-run lint or ingest at session start.
Invoke skills only when the user explicitly asks, or when a skill's own instructions require it.

---

## When to Use Each Skill

### `/mnemo:init`

- Once per project, before the first ingest
- When the taxonomy structure (`wiki/sources/`, etc.) does not exist

### `/mnemo:schema`

- Right after `/mnemo:init` to define the domain taxonomy
- When the user wants to revise entity types or concept categories
- Before answering "what entity types should I use?" — run this instead of guessing

### `/mnemo:ingest`

- When the user invokes it explicitly
- After the user drops new files into `raw/`

### `/mnemo:query`

- Before answering any factual question that might be in the knowledge base
- Search **local first** (`.mnemo/`), then global (`~/.mnemo/`) if no results
- If query returns 0 results, say so explicitly — never hallucinate wiki content

### `/mnemo:lint`

- When the user invokes it explicitly
- At the end of any session where files were added or modified

### `/mnemo:save`

- When you generate a **new insight** not already in the wiki
- **Ask the user before saving** unless they explicitly requested it
- Title must be descriptive and unique

### `/mnemo:stats`

- When the user wants to know the size or health of the knowledge base
- To check if index sharding is needed

### `/mnemo:mine`

- During or after a session where decisions, new entities, or key insights were discussed
- When the user types "à retenir", "mine this", "note ça", "save this", or similar
- When the agent detects implicit high-value signals: "on a décidé", "in conclusion", "the architecture is"
- Before ending a session that produced significant new knowledge

---

## Wiki Page Formatting Rules

Every wiki page **must** start with YAML frontmatter:

```yaml
---
title: Page Title
category: sources | entities | concepts | synthesis
tags: [tag1, tag2]
source: raw/filename.ext   # required for sources category
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Then the page body:

```markdown
# Title (H1 — exactly one per page)

> *Source: `raw/filename.ext`* — or generation timestamp for synthesis

---

## Section

Body text referencing [[Related Concept]] and [[Entity Name]].

## Links

- [[Related Concept]]
- [[Entity Name]]
```

**Rules:**

- H1 = page title only. Never use H1 for sections.
- YAML frontmatter is mandatory on every page — no exceptions.
- `source:` field is required for all `sources/` category pages.
- Always end with a `## Links` section listing related pages.
- **Wikilinks use `[[Page Title]]` syntax** — always the exact H1 title of the target page, not a filename. This makes pages Obsidian-compatible and human-readable.
- Page size: soft cap 400 lines, hard cap 800 lines. Split into sub-pages if exceeded.
- Never duplicate content — query first, then decide to save.

---

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| `sources/` filename | `kebab-case.md` | `python-asyncio-guide.md` |
| `entities/` filename | `<type>-<name>.md` | `tool-redis.md`, `person-karpathy.md` |
| `concepts/` filename | `<category>-<name>.md` | `pattern-saga.md`, `technique-rag.md` |
| `synthesis/` filename | `kebab-case.md` | `btree-vs-hash-comparison.md` |
| Page title (H1) | Title Case | `Redis — In-Memory Data Store` |
| Index entry | `- [Title](wiki/<subdir>/file.md)` | `- [Redis](wiki/entities/tool-redis.md)` |
| Log entry | `- filename \| ISO timestamp` | `- notes.md \| 2026-04-22T14:00:00+00:00` |

---

## Scalability Rules

- **Page size cap** — soft cap 400 lines, hard cap 800 lines. When a page exceeds 800 lines during ingest, split into `<slug>-part-1.md` and `<slug>-part-2.md`. Warn the user when approaching 400 lines.
- **Index sharding** — when total wiki pages exceed 150, the index splits into `index.md` (master TOC with shard links) + per-category shards in `wiki/indexes/sources.md`, `wiki/indexes/entities.md`, `wiki/indexes/concepts.md`, `wiki/indexes/synthesis.md`.
- **Frontmatter filtering** — for large wikis, use YAML `tags:` and `category:` to narrow reads before loading full content.

---

## Memory Structure

```
.mnemo/               (local — per project)
~/.mnemo/             (global — cross-project)

Each tier:
├── raw/              ← source files (immutable input)
├── wiki/
│   ├── sources/      ← one page per ingested raw source
│   ├── entities/     ← people, tools, projects, systems
│   ├── concepts/     ← ideas, patterns, techniques
│   ├── synthesis/    ← cross-source analyses, comparisons
│   └── indexes/      ← index shards (created when >150 pages)
├── index.md          ← categorized table of contents
├── log.md            ← audit trail (prevents re-processing)
└── SCHEMA.md         ← domain conventions (edit per project)
```

---

## Prohibited Behaviors

- **Never invent wiki content.** If a query returns no results, say so.
- **Never save without a meaningful title.**
- **Never skip lint output.** If issues are found, report and offer to fix.
- **Never process the same file twice.** Check `log.md` first.
- **Never write wiki pages outside `wiki/`.**
- **Never omit YAML frontmatter** from a wiki page.
- **Never write a sources page without a `source:` citation** in the frontmatter.
