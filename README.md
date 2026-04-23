# mnemo

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
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

mnemo exposes seven skills that work with any [agentskills.io](https://agentskills.io)-compatible agent — no server, no binary, no dependencies.

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

---

## Typical workflow

Slash commands work in any agent. Natural language alternatives are shown in comments — use whichever your agent prefers.

```
/mnemo:init                          # "initialize mnemo" — bootstrap + optional qmd setup
/mnemo:schema                        # "define my wiki taxonomy"
# drop files into .mnemo/raw/
/mnemo:ingest                        # "ingest files in raw/"
/mnemo:query database indexing       # "what does my wiki say about database indexing?"
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
├── log.md
└── SCHEMA.md         ← starter taxonomy, ready to edit
```

During init you choose which tiers to activate (project, global, or both) and optionally configure **qmd** for hybrid semantic search. After bootstrapping, init offers to run `/mnemo:schema` immediately so you can define your domain before the first ingest.

### `/mnemo:schema`

Interactively creates or revises `.mnemo/SCHEMA.md` — the taxonomy that tells `/mnemo:ingest` how to classify what it finds.

**What SCHEMA.md contains:**

- **Entity types** — the named things in your domain (people, tools, projects, systems…)
- **Concept categories** — the ideas and patterns that recur (techniques, patterns, principles…)
- **Tagging conventions** — which tags to apply and when
- **Relationship hints** — how entities and concepts typically relate to each other

**How it works:**

If files are already present in `raw/`, schema reads them first and proposes entity types and concept categories inferred from the content — you review and adjust rather than starting from scratch. Otherwise it walks through a short guided questionnaire. Either way, a full draft is shown for approval before anything is written.

Run it at any time, not just at init. Useful when the domain evolves, new source types arrive, or the initial taxonomy turns out to be too coarse.

### `/mnemo:ingest`

Processes all pending files from `raw/` via LLM synthesis.

- Synthesizes a summary, key points, and excerpts — never copy-pastes raw text
- Extracts entities and concepts, creating dedicated pages for each
- Writes bidirectional wikilinks between source, entity, and concept pages
- Enriches up to 15 related existing pages per ingest run
- Enforces `source:` citation in frontmatter — no silent provenance loss
- Checks page size; warns at 400 lines, splits at 800

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

Every proposed fix requires explicit approval before being applied.

### `/mnemo:save <title>`

Saves Claude-generated content (summaries, comparisons, analyses) as a permanent wiki page with YAML frontmatter, routed to the correct category and indexed automatically.

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
