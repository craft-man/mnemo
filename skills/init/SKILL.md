---
name: init
description: >
  Bootstrap a new mnemo knowledge base with taxonomy directory structure and a
  starter SCHEMA.md. Use when starting a new wiki, setting up a second brain,
  initializing a personal knowledge base, or when the user says "set up my wiki",
  "create a knowledge base", "initialize mnemo", or "start my second brain".
  Run once per project before the first ingest.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:init). Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.3.0"
allowed-tools: Read Write Glob
---

Initialize `.mnemo/` with the full taxonomy structure.

## Steps

**1. Check for existing init** — if `.mnemo/wiki/sources/` already exists, warn:
> "Knowledge base already initialized. Run `/mnemo:lint` to check its health."

Stop here.

**2. Create directory structure:**
```
.mnemo/
├── raw/                    ← source files (immutable input)
├── wiki/
│   ├── sources/            ← one page per ingested source
│   ├── entities/           ← people, tools, projects, systems
│   ├── concepts/           ← ideas, patterns, techniques
│   ├── synthesis/          ← cross-source analyses, comparisons
│   └── indexes/            ← index shards (created when >150 pages)
├── index.md
├── log.md
└── SCHEMA.md
```

Write `.mnemo/index.md`:
```markdown
# Index

## Sources

## Entities

## Concepts

## Synthesis
```

Write `.mnemo/log.md`:
```markdown
# Log
```

**3. Write `.mnemo/SCHEMA.md`** — starter schema the user should customize:
```markdown
# Knowledge Base Schema

> Edit this file to define domain-specific conventions for this project.

## Domain
<!-- Describe the subject matter of this knowledge base (e.g. "distributed systems", "my PhD research") -->

## Entity Types
Define the kinds of entities that matter in this domain:
- **Person** — researchers, authors, contributors
- **Tool** — software, libraries, frameworks
- **Project** — codebases, products, initiatives

## Concept Taxonomy
Define recurring concept categories:
- **Pattern** — reusable design or architectural pattern
- **Technique** — method or approach
- **Problem** — known failure mode or challenge

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md` (e.g. `tool-redis.md`)
- Concept pages: `wiki/concepts/<category>-<name>.md` (e.g. `pattern-saga.md`)
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax — always the exact H1 title of the target page. Obsidian-compatible.
```

**4. Schema setup** — offer to define the domain taxonomy immediately:

> "Would you like to define your domain taxonomy now? I can read files already in `raw/` to infer entity types and concept categories, then ask a few questions. [y]es / [n]o (you can run `/mnemo:schema` anytime)"

If `[y]es`: invoke `/mnemo:schema` now. Skip the manual SCHEMA.md note in step 5.

If `[n]o`: continue — the starter SCHEMA.md from step 3 will be used until the user runs `/mnemo:schema`.

**5. Semantic search setup (optional)** — ask the user:

> "Would you like to enable semantic search via **qmd**? It adds hybrid BM25 + vector search locally — no API key required. Needs: Node.js ≥ 22 (or Bun ≥ 1.0) + ~2 GB disk for models (downloaded once on first use). [y]es / [n]o"

**If yes:**

1. Check if qmd is already installed: run `qmd --version`.
   - If not found: show the install command and wait for the user to run it:
     ```
     # with npm
     npm install -g qmd
     # or with Bun
     bun add -g qmd
     ```
   - Once installed (user confirms or `qmd --version` succeeds): continue.

2. Register the wiki as a qmd collection:
   ```
   qmd collection add mnemo-wiki .mnemo/wiki "**/*.md"
   ```
   If this command fails, report the error and skip the rest of step 4 — the user can retry manually.

3. Write `.mnemo/config.json`:
   ```json
   {
     "semantic_search": "qmd",
     "qmd_collection": "mnemo-wiki"
   }
   ```

4. Inform the user: "qmd is configured. Embeddings will be built automatically on first `/mnemo:ingest`."

**If no:**

Write `.mnemo/config.json`:
```json
{
  "semantic_search": "bm25"
}
```

**6. Report:**
> "Knowledge base initialized at `.mnemo/`.
> Search backend: **<qmd | BM25>**.
> Next: drop files into `.mnemo/raw/` and run `/mnemo:ingest`."
> (If schema was not defined in step 4, add: "Run `/mnemo:schema` to define your domain taxonomy first.")
