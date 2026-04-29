---
name: mnemo-init
description: >
  Bootstrap a new mnemo knowledge base with taxonomy directory structure and a
  starter SCHEMA.md. Use when starting a new wiki, setting up a second brain,
  initializing a personal knowledge base, or when the user says "set up my wiki",
  "create a knowledge base", "initialize mnemo", or "start my second brain".
  Run once per project before the first ingest.
  After init, optionally wires the wiki into a tool-agnostic agent memory file for future sessions.
license: MIT
compatibility: >
  Agents that support skill-style slash commands (for example /mnemo:init).
  Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.16.0"
allowed-tools: Read Write Edit Glob Bash
---

Initialize `.mnemo/<project-name>/` with the full taxonomy structure.

## Steps

## Step 0 — Python fast path (optional)

Fast path: use `Glob('**/scripts/init_mnemo.py')` first, then `Glob('**/skills/init/init_mnemo.py')` if the public wrapper is not found.
If found at `<script_path>`, run:
```
python3 <script_path>
```
If exit 0 — confirm to the user that the vault filesystem was initialized, then continue with the host-aware steps below that are not handled safely by the generic script: agent memory wiring, session-end reminder wiring, graphify guidance, and Obsidian guidance. The Python fast path is a filesystem bootstrap, not the whole `/mnemo:init` workflow.
If exit non-zero — emit `⚠ fast path failed (exit <code>) — falling back to LLM.` then continue with the steps below.
If Python unavailable or script not found — continue with the steps below.

**1. Determine vault root** — `<project-name>` = current directory name (`Path.cwd().name`). The local vault root is `.mnemo/<project-name>/`.

**2. Check for existing init** — if `.mnemo/<project-name>/wiki/sources/` already exists, warn:
> "Knowledge base already initialized. Run `/mnemo:lint` to check its health."

Stop here.

**3. Create directory structure:**
```
.mnemo/
└── <project-name>/
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
    ├── SESSION_BRIEF.md        ← compact startup context for agents
    ├── SCHEMA.md
    └── config.json
```

Write `.mnemo/<project-name>/index.md`:
```markdown
# Index

## Sources

## Entities

## Concepts

## Synthesis
```

Write `.mnemo/<project-name>/log.md`:
```markdown
# Log
```

**4. Write `.mnemo/<project-name>/SCHEMA.md`** — starter schema the user should customize:
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

**5. Schema setup** — offer to define the domain taxonomy immediately:

> "Would you like to define your domain taxonomy now? I can read files already in `raw/` to infer entity types and concept categories, then ask a few questions. [y]es / [n]o (you can run `/mnemo:schema` anytime)"

If `[y]es`: invoke the schema skill by reading `skills/schema/SKILL.md` and following its instructions. Skip the manual SCHEMA.md note in step 5.

If `[n]o`: continue — the starter SCHEMA.md from step 3 will be used until the user runs `/mnemo:schema`.

**6. User profile** — ensure the global user profile exists:

Invoke the onboard skill by reading `skills/onboard/SKILL.md` and following its instructions. It will detect whether a profile already exists:
- If no profile exists: run the full interview to create one.
- If a profile already exists: skip silently (no prompt to the user).

**7. Semantic search setup (optional)** — ask the user:

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
   qmd collection add mnemo-wiki .mnemo/<project-name>/wiki "**/*.md"
   ```
   If this command fails, report the error and skip the rest of step 6 — the user can retry manually.

3. Write `.mnemo/<project-name>/config.json`:
   ```json
   {
     "search_backend": "qmd",
     "qmd_collection": "mnemo-wiki"
   }
   ```

4. Inform the user: "qmd is configured. Embeddings will be built automatically on first `/mnemo:ingest`."

**If no:**

Write `.mnemo/<project-name>/config.json`:
```json
{
  "search_backend": "bm25"
}
```

**8. Report:**
> "Knowledge base initialized at `.mnemo/<project-name>/`.
> Search backend: **<qmd | BM25>**.
> Next: drop files into `.mnemo/<project-name>/raw/` and run `/mnemo:ingest`."
> (If schema was not defined in step 4, add: "Run `/mnemo:schema` to define your domain taxonomy first.")

**8b. Generate session brief** — after `index.md`, `log.md`, and `config.json` exist, create the compact startup context file.

Fast path: use `Glob('**/mnemo/scripts/update_session_brief.py')` or `Glob('**/scripts/update_session_brief.py')` to locate the script. If found at `<script_path>`, run:
```
python3 <script_path> --vault .mnemo/<project-name>
```
If the script is unavailable or fails, write `.mnemo/<project-name>/SESSION_BRIEF.md` manually with short sections for startup reads, project summary, canonical pages, recent changes, active threads, and guardrails. Do not copy raw source content or the full index.

**9. Agent memory wiring** — offer to persist the wiki in the project's agent instructions/memory:

Ask the user:
> "Want me to add a mnemo memory stanza to this project's agent instructions so future sessions know about the wiki? [y/n]"

If `[n]`: do nothing. Do not ask again.

If `[y]`:

Resolve the target file using this logic:
1. Prefer the project-level memory/instructions file that the current tool is known to auto-load at the start of new sessions.
2. If multiple supported files exist, prefer the one already used by the current tool in this project.
3. If support exists but no file is present yet, create the tool's preferred project-level memory/instructions file.
4. If the current tool does not auto-load any project-level memory/instructions file, or support cannot be confirmed, do not assume persistence. Warn the user and ask whether they still want a best-effort local file created for manual or future-tool use.

For best-effort local files, prefer this fallback order:
1. `AGENTS.md`
2. `CLAUDE.md`
3. another conventional project-level agent memory/instructions file appropriate to the environment

Check whether the target file already contains the heading `## mnemo`. If yes: skip silently — the stanza is already present.

Otherwise:

Build the stanza based on what was initialized in steps 3–6:

```markdown
## mnemo

This project has a mnemo knowledge base in `.mnemo/<project-name>/`.

At the start of every session:
- Read the user profile if it exists at `~/.mnemo/wiki/entities/person-user.md`
- Read `.mnemo/<project-name>/SESSION_BRIEF.md` if it exists
- Read `graphify-out/GRAPH_REPORT.md` only if the task concerns codebase structure
- Use that context before answering project-specific questions or making implementation decisions

During the session:
- Query it with `/mnemo:query <term>` before answering factual questions
- Ingest new sources with `/mnemo:ingest`
- When a spec or plan is finalized (e.g. from superpowers brainstorming or writing-plans), move it to `.mnemo/<project-name>/raw/` and run `/mnemo:ingest` to add it to the knowledge base
```

If graphify was set up in step 10, append this line to the stanza:
```
- Treat `graphify-out/GRAPH_REPORT.md` as the canonical starting point for project structure when it exists
- Run `/mnemo:graphify` after significant code changes to keep the knowledge graph up to date
```

Then:
- If the target file exists: append the stanza at the end of the file, preceded by a blank line.
- If the target file does not exist: create it with the stanza as the only content.

Confirm:
> "Done — mnemo instructions added to the project's agent memory file. Future sessions can discover this wiki automatically."

If the stanza was written only as a best-effort file without confirmed auto-loading support, confirm instead:
> "mnemo instructions written to a local agent file, but automatic reuse in future sessions depends on tool support."

**9b. Session-end reminder wiring** — if the current tool supports project-local stop hooks or session-end reminders, offer to wire one:

Ask the user:
> "Want me to add a session-end reminder to capture insights with `/mnemo:mine` when this tool supports local hooks/reminders? [y/n]"

If `[n]`: do nothing. Do not ask again.

If `[y]`:

- Detect whether the current tool has a supported project-local mechanism for session-end hooks or reminders.
- If supported: add a reminder that tells the user to run `/mnemo:mine` at session end, preserving any existing config and skipping silently if an equivalent mnemo reminder is already present.
- If not supported: skip gracefully and tell the user manual use of `/mnemo:mine` remains available.

After writing, confirm:
> "Session-end reminder configured — you'll be prompted to run `/mnemo:mine` when the session ends."

**10. Graphify setup (optional)** — ask the user:

> "Want to map your codebase with **graphify**? It builds a persistent knowledge graph so I can answer questions about your project without re-reading source files on every session. [y]es / [n]o"

**If `[n]o`:** do nothing. Report:
> "You can run `/mnemo:graphify` anytime to map your codebase."

**If `[y]es`:**

Check if graphify is installed: run `graphify --version`.

- **If not found:** show the install command and wait for the user to run it:
  ```
  pip install graphifyy && graphify install
  ```
  Once the user confirms graphify is installed (or `graphify --version` succeeds): continue.

- **If found:** continue immediately.

Invoke the graphify skill by reading `skills/graphify/SKILL.md` and following its instructions.

After the graphify skill completes, report:
> "Codebase mapped. Start with `graphify-out/GRAPH_REPORT.md` for structure, and use `graphify query ... --graph graphify-out/graph.json` for focused follow-up questions. Re-run `/mnemo:graphify` after significant code changes to keep the graph up to date."

**11. Obsidian setup (optional)** — ask the user:

> "Want to open this wiki in **Obsidian**? It gives you a visual graph, full-text search, and lets the Web Clipper send pages directly into your ingest queue. [y]es / [n]o"

**If `[n]o`:** do nothing. Report:
> "You can open `.mnemo/<project-name>/` as an Obsidian vault anytime — it's compatible out of the box."

**If `[y]es`:**

1. Since Obsidian cannot be detected from a shell, show the install instructions immediately:
   > "If Obsidian is not yet installed, download it from **https://obsidian.md/** (free, available on macOS, Windows, Linux, iOS, Android). No sign-up required for local vaults."

2. Instruct the user to open Obsidian and set the vault root to `.mnemo/<project-name>/` — this gives the vault a meaningful name and keeps both `raw/` and `wiki/` visible inside the app:
   > "In Obsidian: **Open folder as vault** → select `.mnemo/<project-name>/` in this project (or `~/.mnemo/` for the global vault)."

3. Offer to set up the **Obsidian Web Clipper** browser extension so clipped pages land directly in the ingest queue:
   > "Install the Obsidian Web Clipper: https://obsidian.md/clipper#more-browsers — then set its default save location to `raw/` inside this vault. Pages you clip will be picked up automatically by `/mnemo:ingest`."

4. Report:
   > "Obsidian vault ready at `.mnemo/<project-name>/`. Clipped pages saved to `raw/` will be ingested with `/mnemo:ingest`."
