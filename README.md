# mnemo

> *Knowledge that compounds.*

Most AI tools re-derive answers from your raw files on every query. mnemo builds a persistent wiki instead: Claude reads your sources once, synthesizes structured pages, and cross-references them permanently. The longer you use it, the richer the graph gets.

Inspired by Karpathy's [LLM Wiki pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).

---

## Why not just RAG?

RAG retrieves — it doesn't remember. Every query starts from scratch: embed, search, read, answer, forget.

mnemo accumulates. Each ingest run extracts entities and concepts, links them bidirectionally, and updates existing pages with new citations. A concept page that starts with one source reference grows into a dense hub as more sources arrive. Queries hit a pre-synthesized graph, not raw documents.

The difference compounds over time. At 5 sources it feels similar. At 50, the wiki answers questions your sources never explicitly addressed.

---

## What it does

mnemo gives Claude Code a two-tier knowledge base:

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

The plugin exposes six skills that instruct Claude to manage this structure using its native file tools — no server, no binary, no dependencies.

---

## Installation

**Requirements:** [Claude Code](https://claude.ai/code) CLI

```bash
git clone https://github.com/mnemo-ai/mnemo
claude --plugin-dir ./mnemo
```

To avoid typing `--plugin-dir` every time:

```bash
echo 'alias claude="claude --plugin-dir /path/to/mnemo"' >> ~/.bashrc
source ~/.bashrc
```

---

## Search backends

By default mnemo uses **BM25** — no extra dependencies, works out of the box.

For better results, `/mnemo:init` offers to configure **[qmd](https://github.com/qmd-lab/qmd)**, a local hybrid search engine (BM25 + vector embeddings). Once set up, `/mnemo:query` routes through qmd automatically.

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

```
/mnemo:init                          # bootstrap once per project
/mnemo:schema                        # define your domain taxonomy (infers from raw/ if files present)
# drop files into .mnemo/raw/
/mnemo:ingest                        # synthesize → wiki pages + wikilinks
/mnemo:query database indexing       # search the knowledge base
/mnemo:save B-tree vs Hash Index     # persist a Claude-generated insight
/mnemo:lint                          # audit for broken links, orphans, stale claims
/mnemo:stats                         # check size and scaling status
```

---

## Skills

### `/mnemo:init`

Bootstraps a new knowledge base with the taxonomy directory structure and a starter `SCHEMA.md`. Run once per project — warns if already initialized. Offers to run `/mnemo:schema` immediately after.

### `/mnemo:schema`

Interactively creates or revises `.mnemo/SCHEMA.md` — the domain taxonomy that guides how ingest categorizes entities and concepts.

If files are already present in `raw/`, reads them first to infer entity types and concept categories before asking any questions. Otherwise walks through a short guided questionnaire. Shows a full draft for approval before writing.

Can be run at any time — not just at init. Useful when the domain evolves or the initial taxonomy turns out to be too coarse.

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

## How it works

Each skill is a `SKILL.md` file with detailed instructions — Claude follows them using its built-in `Read`, `Write`, `Glob`, and `Grep` tools. No moving parts.

```
mnemo/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── init/SKILL.md
│   ├── ingest/SKILL.md
│   ├── query/SKILL.md
│   ├── lint/SKILL.md
│   ├── save/SKILL.md
│   └── stats/SKILL.md
└── CLAUDE.md
```

---

## Contributing

1. Fork the repo and create a feature branch
2. Edit the relevant `SKILL.md` — test with `claude --plugin-dir ./mnemo`
3. Use `/reload-plugins` inside Claude Code to pick up changes without restarting
4. Open a PR describing what the change improves and why

---

## License

MIT
