---
name: init
description: >
  Bootstrap a new mnemo knowledge base with taxonomy directory structure and a
  starter SCHEMA.md. Use when starting a new wiki, setting up a second brain,
  initializing a personal knowledge base, or when the user says "set up my wiki",
  "create a knowledge base", "initialize mnemo", or "start my second brain".
  Run once per project before the first ingest.
  After init, optionally wires the wiki into CLAUDE.md for future session memory.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:init). Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.5.0"
allowed-tools: Read Write Edit Glob Bash
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
│   ├── activity/           ← session logs (not searched by default)
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

**5. User profile** — ensure the global user profile exists:

Invoke `/mnemo:onboard` now. It will detect whether a profile already exists:
- If no profile exists: run the full interview to create one.
- If a profile already exists: skip silently (no prompt to the user).

**6. Semantic search setup (optional)** — ask the user:

> "Would you like to enable semantic search via **qmd**? It adds hybrid BM25 + vector search locally — no API key required. Needs: Node.js ≥ 22 (or Bun ≥ 1.0) + ~2 GB disk for models (downloaded once on first use). [y]es / [n]o"

**If yes:**

1. Check if qmd is already installed: run `qmd --version`.
   - If not found: show the install command and wait for the user to run it:
     ```
     # with npm
     npm install -g @tobilu/qmd
     # or
     bun install -g @tobilu/qmd
     ```
   - Once installed (user confirms or `qmd --version` succeeds): continue.

2. Register the wiki as a qmd collection:
   ```
   qmd collection add mnemo-wiki .mnemo/wiki "**/*.md"
   ```
   If this command fails, report the error and skip the rest of step 6 — the user can retry manually.

3. Write `.mnemo/config.json`:
   ```json
   {
     "search_backend": "qmd",
     "qmd_collection": "mnemo-wiki"
   }
   ```

4. Inform the user: "qmd is configured. Embeddings will be built automatically on first `/mnemo:ingest`."

**If no:**

Write `.mnemo/config.json`:
```json
{
  "search_backend": "bm25"
}
```

**7. Report:**
> "Knowledge base initialized at `.mnemo/`.
> Search backend: **<qmd | BM25>**.
> Next: drop files into `.mnemo/raw/` and run `/mnemo:ingest`."
> (If schema was not defined in step 4, add: "Run `/mnemo:schema` to define your domain taxonomy first.")

**8. CLAUDE.md wiring** — offer to persist the wiki in the project's agent memory: — offer to persist the wiki in the project's agent memory:

Ask the user:
> "Want me to add a memory stanza to `CLAUDE.md` so I remember this wiki in future sessions? [y/n]"

If `[n]`: do nothing. Do not ask again.

If `[y]`:

Check if `CLAUDE.md` already contains the heading `## mnemo`. If yes: skip silently — the stanza is already present.

Otherwise:

Build the stanza based on what was initialized in steps 2–5:

```markdown
## mnemo

This project has a mnemo knowledge base in `.mnemo/`.
- Query it with `/mnemo:query <term>` before answering factual questions
- Ingest new sources with `/mnemo:ingest`
- When a spec or plan is finalized (e.g. from superpowers brainstorming or writing-plans), move it to `.mnemo/raw/` and run `/mnemo:ingest` to add it to the knowledge base
```

If graphify was set up in step 9, append this line to the stanza:
```
- Run `/mnemo:graphify` after significant code changes to keep the knowledge graph up to date
```

Then:
- If `CLAUDE.md` exists: append the stanza at the end of the file, preceded by a blank line.
- If `CLAUDE.md` does not exist: create it with the stanza as the only content.

Confirm:
> "Done — stanza added to `CLAUDE.md`. I'll remember this wiki in future sessions."

**8b. Stop hook injection** — wire the session-end reminder into the project's Claude Code settings:

Ensure the `.claude/` directory exists in the current project (create it if needed). Then check if `.claude/settings.local.json` exists.

**Case A — file does not exist:**
Create `.claude/settings.local.json` with:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'mnemo — session ending. Run /mnemo:mine to capture insights from this session.'"
          }
        ]
      }
    ]
  }
}
```

**Case B — file exists, no `hooks` key yet:**
Read the file. Add the `"hooks"` key from Case A at the top level, preserving all existing content.

**Case C — file exists, `hooks.Stop` exists but no mnemo entry:**
Read the file. Append the mnemo hook object to the existing `hooks.Stop` array, preserving all existing hooks.

**Case D — file already contains the mnemo echo command:**
Skip silently — already wired.

After writing, confirm:
> "Stop hook added to `.claude/settings.local.json` — you'll be reminded to run `/mnemo:mine` at session end."

If the `.claude/` directory does not exist, create it first.

**9. Graphify setup (optional)** — ask the user:

> "Want to map your codebase with **graphify**? It builds a persistent knowledge graph so I can answer questions about your project without re-reading source files on every session. [y]es / [n]o"

**If `[n]o`:** do nothing. Report:
> "You can run `/mnemo:graphify` anytime to map your codebase."

**If `[y]es`:**

Check if graphify is installed: run `graphify --version`.

- **If not found:** show the install command and wait for the user to run it:
  ```
  pip install graphify && graphify install
  ```
  Once the user confirms graphify is installed (or `graphify --version` succeeds): continue.

- **If found:** continue immediately.

Invoke `/mnemo:graphify` now.

After `/mnemo:graphify` completes, report:
> "Codebase mapped. Query it with `/mnemo:query <term>`. Re-run `/mnemo:graphify` after significant code changes to keep the graph up to date."

**10. Obsidian setup (optional)** — ask the user:

> "Want to open this wiki in **Obsidian**? It gives you a visual graph, full-text search, and lets the Web Clipper send pages directly into your ingest queue. [y]es / [n]o"

**If `[n]o`:** do nothing. Report:
> "You can open `.mnemo/` as an Obsidian vault anytime — it's compatible out of the box."

**If `[y]es`:**

1. Since Obsidian cannot be detected from a shell, show the install instructions immediately:
   > "If Obsidian is not yet installed, download it from **https://obsidian.md/** (free, available on macOS, Windows, Linux, iOS, Android). No sign-up required for local vaults."

2. Instruct the user to open Obsidian and set the vault root to `.mnemo/` (not `.mnemo/wiki/`) — this keeps both `raw/` and `wiki/` visible inside the app:
   > "In Obsidian: **Open folder as vault** → select `.mnemo/` in this project (or `~/.mnemo/` for the global vault)."

3. Offer to set up the **Obsidian Web Clipper** browser extension so clipped pages land directly in the ingest queue:
   > "Install the Obsidian Web Clipper: https://https://obsidian.md//clipper#more-browsers — then set its default save location to `raw/` inside this vault. Pages you clip will be picked up automatically by `/mnemo:ingest`."

4. Report:
   > "Obsidian vault ready at `.mnemo/`. Clipped pages saved to `raw/` will be ingested with `/mnemo:ingest`."
