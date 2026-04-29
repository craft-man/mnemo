---
name: mnemo-init
description: >
  Bootstrap a new mnemo knowledge base with taxonomy directory structure and a
  required schema and global user profile. Use when starting a new wiki, setting up a second brain,
  initializing a personal knowledge base, or when the user says "set up my wiki",
  "create a knowledge base", "initialize mnemo", or "start my second brain".
  Run once per project before the first ingest.
  After init, wires the wiki into a tool-agnostic agent memory file for future sessions when possible.
license: MIT
compatibility: >
  Agents that support skill-style slash commands (for example /mnemo:init).
  Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.16.6"
allowed-tools: Read Write Edit Glob Bash
---

Initialize `.mnemo/<project-name>/` with the full taxonomy structure.

## Steps

## Step 0 — Python fast path

Use the Python fast path first whenever it is available: use `Glob('**/scripts/init_mnemo.py')` first, then `Glob('**/skills/init/init_mnemo.py')` if the public wrapper is not found.

For Codex or any agent running the script as a subprocess, collect the mandatory values in the chat before launching the script:
- Schema: domain, entity types, concept categories.
- Onboarding: role, technical level, language, domains, proactivity, register.
- Search and integrations: default to BM25, graphify off, and Obsidian off unless the user explicitly chooses otherwise.

If found at `<script_path>`, run:
```
python3 <script_path> --non-interactive \
  --schema-domain "<domain>" \
  --schema-entity-types "<Person, Tool, Project>" \
  --schema-concept-categories "<Pattern, Technique, Problem>" \
  --role "<role>" \
  --technical-level "<technical level>" \
  --language "<language>" \
  --domains "<domains>" \
  --proactivity "<High|Moderate|Low>" \
  --register "<Direct|Collaborative>" \
  --search-backend bm25
```
If exit 0 — stop the manual init workflow. The Python script is the canonical complete bootstrap path and already handles local/global structure, mandatory schema setup, mandatory onboarding, qmd, graphify, Obsidian, session brief generation, and best-effort agent memory wiring before returning. In the final response, describe only what was completed and the normal next use: drop source files into `raw/`, then ingest them. Do not list `/mnemo:onboard`, `/mnemo:schema`, `/mnemo:graphify`, profile creation, schema customization, manual installation, or agent-memory setup as optional follow-ups.
If exit non-zero — emit `⚠ fast path failed (exit <code>) — falling back to LLM.` then continue with the steps below.
If Python unavailable or script not found — continue with the steps below.

The fallback LLM path below must preserve the same contract as the Python path: `SCHEMA.md` setup, the global user profile, qmd/graphify decisions, `SESSION_BRIEF.md`, Obsidian guidance when requested, and agent memory wiring are part of init. They are not optional follow-ups. Do not report init as complete until these have been handled in the same run.

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

**4. Write `.mnemo/<project-name>/SCHEMA.md`** — temporary starter content before the mandatory schema pass:
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

**5. Schema setup** — define the domain taxonomy immediately:

Invoke the schema skill by reading `skills/schema/SKILL.md` and following its instructions.
This is part of init, not an optional follow-up. Do not report init as complete until this pass has happened. If the user gives minimal answers, keep starter defaults where needed, but still write a schema whose `## Domain`, `## Entity Types`, and `## Concept Taxonomy` sections are no longer just untouched placeholders.

**6. User profile** — ensure the global user profile exists:

Invoke the onboard skill by reading `skills/onboard/SKILL.md` and following its instructions. This is part of init, not an optional follow-up. It will detect whether a profile already exists:
- If no profile exists: run the full interview now and create `~/.mnemo/wiki/entities/person-user.md`. Do not skip this because the file contains preferences; ask the user and store their answers.
- If a profile already exists: skip silently (no prompt to the user).

**7. Semantic search setup** — ask the user with yes as the default:

> "Would you like to enable semantic search via **qmd**? It adds hybrid BM25 + vector search locally — no API key required. Needs: Node.js ≥ 22 (or Bun ≥ 1.0) + ~2 GB disk for models (downloaded once on first use). [Y/n]"

**If yes:**

1. Check if qmd is already installed: run `qmd --version`.
   - If not found: attempt automatic installation in this same run with `npm install -g @tobilu/qmd` when npm exists, or `bun install -g @tobilu/qmd` when bun exists.
   - If installation is refused by the user through the initial `[n]` answer, unavailable, or fails technically, write BM25 config and state that BM25 is active. Do not ask the user to install qmd manually.

2. Register the wiki as a qmd collection:
   ```
   qmd collection add mnemo-wiki .mnemo/<project-name>/wiki "**/*.md"
   ```
   If this command fails, write BM25 config and state that BM25 is active.

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

**8. Report state, not handoff work:**
> "Knowledge base initialized at `.mnemo/<project-name>/`.
> Search backend: **<qmd | BM25>**.
> Next: drop files into `.mnemo/<project-name>/raw/` and run `/mnemo:ingest`."

Do not add `/mnemo:schema`, `/mnemo:onboard`, `/mnemo:graphify`, manual install commands, or memory setup as next steps here. If schema, onboarding, config, session brief, graphify decision, or memory wiring did not run, init is incomplete and you must complete it before reporting success.

**8b. Generate session brief** — after `index.md`, `log.md`, and `config.json` exist, create the compact startup context file.

Fast path: use `Glob('**/mnemo/scripts/update_session_brief.py')` or `Glob('**/scripts/update_session_brief.py')` to locate the script. If found at `<script_path>`, run:
```
python3 <script_path> --vault .mnemo/<project-name>
```
If the script is unavailable or fails, write `.mnemo/<project-name>/SESSION_BRIEF.md` manually with short sections for startup reads, project summary, canonical pages, recent changes, active threads, and guardrails. Do not copy raw source content or the full index.

**9. Agent memory wiring** — persist the wiki in the project's agent instructions/memory automatically:

Resolve the target file using this logic:
1. Prefer the project-level memory/instructions file that the current tool is known to auto-load at the start of new sessions.
2. If multiple supported files exist, prefer the one already used by the current tool in this project.
3. If support exists but no file is present yet, create the tool's preferred project-level memory/instructions file.
4. If the current tool does not auto-load any project-level memory/instructions file, or support cannot be confirmed, create the best-effort local file without prompting.

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
- Refresh graphify after significant code changes to keep the knowledge graph up to date
```

Then:
- If the target file exists: append the stanza at the end of the file, preceded by a blank line.
- If the target file does not exist: create it with the stanza as the only content.

Confirm:
> "Done — mnemo instructions added to the project's agent memory file. Future sessions can discover this wiki automatically."

If the stanza was written only as a best-effort file without confirmed auto-loading support, confirm instead:
> "mnemo instructions written to a local agent file; automatic reuse in future sessions depends on tool support."

**9b. Session-end reminder wiring** — if the current tool supports project-local stop hooks or session-end reminders, configure one automatically when applicable:

- Detect whether the current tool has a supported project-local mechanism for session-end hooks or reminders.
- If supported: add a reminder that tells the user to run `/mnemo:mine` at session end, preserving any existing config and skipping silently if an equivalent mnemo reminder is already present.
- If not supported: skip gracefully.

After writing, confirm:
> "Session-end reminder configured — you'll be prompted to run `/mnemo:mine` when the session ends."

**10. Graphify setup** — ask the user with yes as the default:

> "Want to map your codebase with **graphify**? It builds a persistent knowledge graph so I can answer questions about your project without re-reading source files on every session. [Y/n]"

**If `[n]o`:** do nothing. Report:
> "Codebase graph mapping was not enabled during init."

**If `[y]es`:**

Check if graphify is installed: run `graphify --version`.

- **If not found:** attempt automatic installation in this same run with `pip install graphifyy`, then `graphify install` or `python -m graphify install`.
  If installation is refused through the initial `[n]` answer, unavailable, or fails technically, continue cleanly without asking the user to install graphify manually.

- **If found:** continue immediately.

Invoke the graphify skill by reading `skills/graphify/SKILL.md` and following its instructions.

After the graphify skill completes, report:
> "Codebase mapped. Start with `graphify-out/GRAPH_REPORT.md` for structure, and use `graphify-out/graph.json` for focused follow-up questions."

**11. Obsidian setup** — ask the user with yes as the default:

> "Want to open this wiki in **Obsidian**? It gives you a visual graph, full-text search, and lets the Web Clipper send pages directly into your ingest queue. [Y/n]"

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
