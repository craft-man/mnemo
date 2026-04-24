# mnemo

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.2.0-blue)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> *Knowledge that compounds.*

Named after [Mnémosyne](https://fr.wikipedia.org/wiki/Mn%C3%A9mosyne), the Greek goddess of memory and mother of the Muses.

If this saves you time, [![GitHub stars](https://img.shields.io/github/stars/craft-man/mnemo?style=social)](https://github.com/craft-man/mnemo) helps others find it.

Most AI tools re-derive answers from your raw files on every query. mnemo builds a persistent wiki instead: Claude reads your sources once, synthesizes structured pages, and cross-references them permanently. The longer you use it, the richer the graph gets.

Inspired by Karpathy's [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

---

## Why not just RAG?

RAG retrieves — it doesn't remember. Every query starts from scratch: embed, search, read, answer, forget.

mnemo accumulates. Each ingest run extracts entities and concepts, links them bidirectionally, and updates existing pages with new citations. A concept page that starts with one source reference grows into a dense hub as more sources arrive. Queries hit a pre-synthesized graph, not raw documents.

The difference compounds over time. At 5 sources it feels similar. At 50, the wiki answers questions your sources never explicitly addressed.

---

## What it does

mnemo gives your agent a two-tier knowledge base:

- **Project** (`.mnemo/`) — knowledge scoped to the current project
- **Global** (`~/.mnemo/`) — knowledge shared across all projects

Each tier is a taxonomy-based wiki:

```
.mnemo/
├── raw/              ← drop your source files here (immutable input)
├── wiki/
│   ├── sources/      ← one synthesized page per ingested source
│   ├── entities/     ← people, tools, projects, systems
│   ├── concepts/     ← patterns, techniques, ideas
│   └── synthesis/    ← cross-source analyses and comparisons
├── index.md          ← categorized table of contents
├── log.md            ← audit trail (prevents duplicate processing)
└── SCHEMA.md         ← domain conventions (edit per project)
```

mnemo exposes nine skills that work with any [agentskills.io](https://agentskills.io)-compatible agent — no server, no binary, no dependencies.

---

## Installation

**Requirements:** [Claude Code](https://claude.ai/code) CLI

### Claude Code marketplace (recommended)

```
/plugin marketplace add craft-man/mnemo
```

Once installed, mnemo is available in any project — no `--plugin-dir` needed.

### Other agents (Codex, Cursor, OpenCode…)

```bash
npx skills add craft-man/mnemo
```

### Manual (git clone)

```bash
git clone https://github.com/craft-man/mnemo
claude --plugin-dir ./mnemo
```

---

## Quick start

In any agent (Claude Code, Codex, Cursor, OpenCode…):

```
/mnemo:init
```

Without an agent — standalone bootstrap (Python 3.10+):

```bash
python3 scripts/init_mnemo.py
```

Both paths offer to configure **qmd** for hybrid semantic search and prompt you to choose between project-only, global, or both tiers. Then:

**For a code project:**
```
/mnemo:graphify    # map the codebase into a queryable knowledge graph
/mnemo:query <term>
```

**For document-based knowledge:**
```
/mnemo:schema      # "define my wiki taxonomy"
# drop files into .mnemo/raw/
/mnemo:ingest      # "ingest files in raw/"
/mnemo:query <term>
```

---

## Search backends

By default mnemo uses **BM25** — no extra dependencies, works out of the box.

For better results, both `/mnemo:init` and `python3 scripts/init_mnemo.py` offer to configure **[qmd](https://github.com/qmd-lab/qmd)**, a local hybrid search engine (BM25 + vector embeddings). Once set up, `/mnemo:query` routes through qmd automatically.

**qmd requirements:** Node.js ≥ 22 or Bun ≥ 1.0, ~2 GB disk (models downloaded once on first use).

```bash
# with npm
npm install -g qmd
# or with Bun
bun add -g qmd
```

qmd is optional — BM25 remains available as fallback if qmd is unavailable or returns an error.

The active backend is stored in `.mnemo/config.json` under `search_backend` (`"bm25"` or `"qmd"`). Custom backends can be registered by adding a dispatch case to the query skill — see `skills/references/backends.md` for the interface spec.

---

## Typical workflow

Slash commands work in any agent. Natural language alternatives are shown in comments — use whichever your agent prefers.

```
/mnemo:init                          # "initialize mnemo" — bootstrap; guides graphify + schema setup
# drop files into .mnemo/raw/
/mnemo:ingest                        # "ingest files in raw/"
/mnemo:query database indexing       # "what does my wiki say about database indexing?"
/mnemo:mine                          # "remember this" — extract knowledge from current session
/mnemo:save B-tree vs Hash Index     # "save this as a wiki page titled B-tree vs Hash Index"
/mnemo:lint                          # "audit my wiki"
/mnemo:stats                         # "show wiki stats"
```

No agent? Bootstrap with the standalone script:

```bash
python3 scripts/init_mnemo.py        # requires Python 3.10+
```

---

## Skills

### `/mnemo:init`

Bootstraps a new knowledge base. Run once per project — warns if already initialized.

What it creates:

```
.mnemo/
├── raw/              ← drop your source files here
├── wiki/
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   └── synthesis/
├── index.md
├── log.md            ← ingest audit trail
└── SCHEMA.md         ← starter taxonomy, ready to edit
```

`log.md` records every file that has been ingested — filename and ISO timestamp. Before processing any file, `/mnemo:ingest` checks this log and skips anything already present. This prevents duplicate pages, avoids re-billing the LLM for the same source, and makes reruns safe. To force a re-ingest of a file, remove its entry from `log.md`.

During init you choose which tiers to activate (project, global, or both) and optionally configure **qmd** for hybrid semantic search. Init then offers two optional next steps:

- **`/mnemo:schema`** — define your domain taxonomy before the first ingest (document-based knowledge)
- **`/mnemo:graphify`** — map the codebase into a queryable knowledge graph immediately. If graphify isn't installed yet, init shows the install command and waits before proceeding.

### `/mnemo:schema`

A guided conversation that builds or revises `.mnemo/SCHEMA.md` — the taxonomy that tells `/mnemo:ingest` how to classify what it finds.

You don't fill in a form. The skill asks you questions, listens to your answers, and proposes a taxonomy draft that you can refine before anything is written. If files are already in `raw/`, it reads them first and comes to the conversation with concrete proposals inferred from your content — so you're reacting and adjusting rather than inventing from scratch.

The conversation covers:

- **Entity types** — the named things in your domain (people, tools, projects, systems…)
- **Concept categories** — the ideas and patterns that recur (techniques, patterns, principles…)
- **Tagging conventions** — which tags to apply and when
- **Relationship hints** — how entities and concepts typically relate to each other

Once the draft looks right, you approve it and the skill writes `SCHEMA.md`. Nothing is saved without your explicit confirmation.

Run it at any time, not just at init. Useful when the domain evolves, new source types arrive, or the initial taxonomy turns out to be too coarse.

### `/mnemo:ingest`

Processes all pending files from `raw/` via LLM synthesis.

- Synthesizes a summary, key points, and excerpts — never copy-pastes raw text
- Extracts entities and concepts, creating dedicated pages for each
- Writes bidirectional wikilinks between source, entity, and concept pages
- Enriches up to 15 related existing pages per ingest run
- Enforces `source:` citation in frontmatter — no silent provenance loss
- Checks page size; warns at 400 lines, splits at 800
- Detects contradictions with existing content — offers `[u]pdate / [k]eep both / [h]istory / [s]kip`. The `[h]istory` option marks an entity as superseded: it adds `superseded_by:` to the old page's frontmatter, appends a `## History` entry, and adds `supersedes:` to the new page

### `/mnemo:query <term>`

Searches the knowledge base using BM25 or hybrid semantic search (qmd, if configured at init).

Supports modifiers: `category:concepts`, `tag:redis`, `since:2026-01-01`, `backlinks:<title>`, `top-linked`. Falls back to the global knowledge base if local returns no results.

### `/mnemo:lint`

Audits the knowledge base and proposes fixes for:

| Issue | Meaning |
|---|---|
| `orphan` | Wiki page not referenced in index |
| `broken_link` | Index entry pointing to a missing file |
| `unprocessed` | File in `raw/` not yet ingested |
| `missing_frontmatter` | Wiki page without YAML frontmatter |
| `missing_source_citation` | Source page without `source:` field |
| `oversized` | Wiki page exceeding 800 lines |
| `no_inbound_links` | Entity or concept with no wikilinks pointing to it |
| `stale_claim` | Temporal language that may be outdated |
| `gap_page` | Term in 3+ sources but no dedicated page |
| `superseded_without_history` | Entity/concept with `superseded_by:` or `supersedes:` but no `## History` section |

Every proposed fix requires explicit approval before being applied.

### `/mnemo:save <title>`

Saves Claude-generated content (summaries, comparisons, analyses) as a permanent wiki page with YAML frontmatter, routed to the correct category and indexed automatically.

### `/mnemo:mine`

Scans the current session for knowledge worth persisting — decisions, new entities, concepts, and conclusions. Presents a numbered candidate list; approved items are routed to `/mnemo:save`.

Triggered explicitly (`/mnemo:mine`) or by intent — the user expressing a desire to save something ("remember this", "note that", "important") or the agent detecting high-value signals ("we decided", "in conclusion", "key insight") — in any language.

### `/mnemo:graphify`

Maps the current project codebase into a queryable knowledge graph using [graphify](https://github.com/safishamsi/graphify).

**Prerequisites:** graphify installed (`pip install graphifyy && graphify install`). mnemo initialized.

What it does:

- Runs `graphify .` on the project root (respects `.graphifyignore` — `.mnemo/` is always excluded)
- Reads `graphify-out/graph.json` and converts each node into a mnemo wiki page with full frontmatter and wikilinks
- Routes nodes to the correct category: code nodes (`class`, `module`, `file`) → `entities/`, conceptual nodes (`pattern`, `technique`) → `concepts/`
- Converts `GRAPH_REPORT.md` into a synthesis page at `wiki/synthesis/codebase-graph-report.md`
- Persists `graph.json` to `.mnemo/graph.json` — re-runs are incremental (only changed nodes update their pages)

**Why this matters:** instead of Claude reading hundreds of source files at session start, it queries pre-built wiki pages. The result is persistent across sessions and queryable via `/mnemo:query`.

### `/mnemo:stats`

Displays page counts per category, total lines, top 5 largest pages, and index scaling status.

---

## Using mnemo with Obsidian

mnemo's wiki format is natively Obsidian-compatible — no conversion needed.

- **Wikilinks** (`[[Page Title]]`) resolve directly in Obsidian's graph view
- **YAML frontmatter** (`title`, `tags`, `category`) surfaces in Obsidian's properties panel
- **Bidirectional links** built by `/mnemo:ingest` appear automatically in the backlinks panel

To open your knowledge base in Obsidian, point a vault at `.mnemo/wiki/` (or `~/.mnemo/wiki/` for the global tier).

### Obsidian Web Clipper

[Obsidian Web Clipper](https://obsidian.md/clipper) lets you clip web pages, articles, and highlights directly from your browser. Use it as a capture front-end for mnemo:

1. Configure Web Clipper to save clips into `.mnemo/raw/` (or `~/.mnemo/raw/` for the global knowledge base)
2. Run `/mnemo:ingest` — mnemo synthesizes each clip into a structured wiki page, extracts entities and concepts, and links it into the graph

This turns casual web browsing into a compounding knowledge base: clip once, query forever.

---

## Contributing

Each skill is a `SKILL.md` file — edit it, reload, test. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

---

## License

MIT
