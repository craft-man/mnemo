# mnemo — Agent Constitution

You are operating with **mnemo**, an Agentic Knowledge Management System.
Use your native tools (Read, Write, Edit, Glob, Grep) to manage the knowledge base.
This document is your operating contract — follow it strictly.

---

## Available Skills

| Skill | Purpose |
|---|---|
| `/mnemo:init` | Bootstrap taxonomy structure + SCHEMA.md |
| `/mnemo:onboard` | Create or update the global user profile in `~/.mnemo/` |
| `/mnemo:schema` | Interactively create or revise the domain taxonomy (SCHEMA.md) |
| `/mnemo:ingest` | Synthesize `raw/` files → categorized `wiki/` |
| `/mnemo:query` | Search the knowledge base |
| `/mnemo:context` | Load minimal mnemo startup context manually |
| `/mnemo:lint` | Audit for structure issues, broken links, oversized pages |
| `/mnemo:save` | Persist generated content as a wiki page |
| `/mnemo:stats` | Display size metrics and scaling thresholds |
| `/mnemo:mine` | Extract knowledge from the current session worth persisting |
| `/mnemo:graphify` | Map the project codebase into a queryable knowledge graph via graphify |
| `/mnemo:log` | Query the audit log (log.md) — filter by op, date range, or recency |

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
If `.mnemo/<project-name>/SESSION_BRIEF.md` exists, read it first for compact startup context.
If `~/.mnemo/wiki/entities/person-user.md` exists and user context matters, read it before making personalized recommendations.
If `graphify-out/GRAPH_REPORT.md` exists and codebase structure matters, read it before broad raw-file search.
Do not load the whole wiki at startup; use `/mnemo:query <term>` for focused retrieval.
If startup auto-load did not happen, run `/mnemo:context` as a read-only fallback.

---

## Session End Protocol

At the end of any session that produced decisions, new knowledge, or significant work:

1. **Automatically propose `/mnemo:mine`** — do not wait for the user to ask.
2. Do not propose if the session was purely read-only (queries, lint checks, stats).
3. Signals that a session was write-worthy: a decision was made, a new concept was explained, architecture was discussed, a bug was diagnosed, a comparison was drawn.

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
- After the user drops new files into `.mnemo/<project-name>/raw/`

### `/mnemo:query`

- Before answering any factual question that might be in the knowledge base
- Search **local first** (`.mnemo/<project-name>/`), then global (`~/.mnemo/`) if no results
- If query returns 0 results, say so explicitly — never hallucinate wiki content

### `/mnemo:context`

- When startup auto-load did not happen before the first prompt
- Read only the session brief, optional global profile, and `graphify-out/GRAPH_REPORT.md` with `--code`
- Never regenerate the brief automatically; report the update command if it is missing or stale

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
category: sources | entities | concepts | synthesis | activity
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

## Claims

- **Claim:** <verifiable assertion>
  **Evidence:** [[<Source Page Title>]] — "<short source excerpt>"
  **Status:** active

## Links

- [[Related Concept]]
- [[Entity Name]]
```

**Rules:**

- H1 = page title only. Never use H1 for sections.
- YAML frontmatter is mandatory on every page — no exceptions.
- `source:` field is required for all `sources/` category pages.
- New `entities`, `concepts`, and `synthesis` pages must include `## Claims`
  with at least one sourced claim.
- Each claim must include `Claim`, `Evidence`, and `Status`.
- `Evidence` must link to a source page and include a short excerpt; excerpts
  are anchors, not replacements for the source.
- Claim status must be `active`, `disputed`, or `superseded`.
- `sources`, `activity`, and graphify-generated pages are exempt from the
  `## Claims` requirement.
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
| `activity/` filename | `YYYY-MM-DD.md` | `2026-04-24.md` |
| Page title (H1) | Title Case | `Redis — In-Memory Data Store` |
| Index entry | `- [Title](wiki/<subdir>/file.md) — summary _(upd YYYY-MM-DD)_` | `- [Redis](wiki/entities/tool-redis.md) — Fast key-value store _(upd 2026-04-20)_` |
| Log entry | `- wiki/path.md \| ISO timestamp \| op` | `- wiki/sources/foo.md \| 2026-04-22T14:00:00+00:00 \| ingest` |

---

## Scalability Rules

- **Page size cap** — soft cap 400 lines, hard cap 800 lines. When a page exceeds 800 lines during ingest, split into `<slug>-part-1.md` and `<slug>-part-2.md`. Warn the user when approaching 400 lines.
- **Index sharding** — when total wiki pages exceed 150, the index splits into `index.md` (master TOC with shard links) + per-category shards in `wiki/indexes/sources.md`, `wiki/indexes/entities.md`, `wiki/indexes/concepts.md`, `wiki/indexes/synthesis.md`. (`activity/` pages are not indexed and are excluded from sharding.)
- **Frontmatter filtering** — for large wikis, use YAML `tags:` and `category:` to narrow reads before loading full content.

---

## Memory Structure

```
.mnemo/                        (local — per project)
└── <project-name>/
    ├── raw/                   ← source files (immutable input)
    ├── wiki/
    │   ├── sources/           ← one page per ingested raw source
    │   ├── entities/          ← people, tools, projects, systems
    │   ├── concepts/          ← ideas, patterns, techniques
    │   ├── synthesis/         ← cross-source analyses, comparisons
    │   ├── activity/          ← session logs (not searched by default)
    │   └── indexes/           ← index shards (created when >150 pages)
    ├── index.md               ← categorized table of contents
    ├── log.md                 ← audit trail (prevents re-processing)
    ├── SESSION_BRIEF.md       ← compact startup context for agents
    ├── SCHEMA.md              ← domain conventions (edit per project)
    └── config.json            ← search backend configuration

~/.mnemo/                      (global — cross-project, flat structure)
├── raw/
├── wiki/
│   └── ...
├── index.md
├── log.md
└── SCHEMA.md
```

---

## Authoring Language

All files in `agents/`, `skills/`, and `skills/references/` must be written in **English** — regardless of the language used in conversation with the user. This applies to new files and edits to existing ones.

Wiki pages in `.mnemo/` follow the user's language preference (no constraint).

---

## Prohibited Behaviors

- **Never invent wiki content.** If a query returns no results, say so.
- **Never save without a meaningful title.**
- **Never skip lint output.** If issues are found, report and offer to fix.
- **Never process the same file twice.** Check `log.md` first.
- **Never write wiki pages outside `wiki/`.**
- **Never omit YAML frontmatter** from a wiki page.
- **Never write a sources page without a `source:` citation** in the frontmatter.
