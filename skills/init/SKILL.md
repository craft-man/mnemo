---
name: mnemo-init
description: >
  Bootstrap a new mnemo project knowledge base with vault structure, schema,
  global user profile when absent, search config, optional graphify, Obsidian
  guidance, session brief, agent memory, and supported session-end hooks. Use
  when starting a new wiki, setting up a second brain, initializing mnemo, or
  when the user invokes mnemo-init. Run once per project before the first ingest.
license: MIT
compatibility: >
  Agents that support skill-style commands should expose this as mnemo-init
  rather than native init command names to avoid collisions. Other
  agentskills.io-compatible agents invoke by natural language. Python scripts
  use stdlib only.
metadata:
  author: mnemo contributors
  version: "0.17.0"
allowed-tools: Read Write Edit Glob Bash
---

Initialize `.mnemo/<project-name>/` completely in one run. Do not report success
until vault creation, schema, onboarding/profile check, search config, graphify
decision, Obsidian decision, session brief, agent memory, and supported
session-end hook wiring have all been handled.

All helper scripts used by this skill are non-interactive, live under skill-owned
`scripts/` directories, support `--help`, write machine-readable JSON to stdout,
and write errors to stderr. The LLM collects and validates user answers one at a
time before invoking scripts.

## Stop Condition

Resolve `<project-name>` from the current directory name unless the user clearly
names another project root. Before asking schema, onboarding, search, graphify,
or Obsidian questions, check whether `.mnemo/<project-name>/` already exists.

If it exists, say:
> "mnemo is already initialized at `.mnemo/<project-name>/`."

Stop. Do not rerun schema, onboard, graphify, search, memory wiring, or any other
init step.

## Step 1 - Create Vault

Run:
```bash
python skills/init/scripts/create_vault.py --project-root .
```

If stdout reports `already_exists`, use the stop condition above. Otherwise keep
the returned `vault` and `project_name`.

## Step 2 - Schema

Delegate to the schema skill immediately by reading `skills/schema/SKILL.md` and
following its interview flow. Ask one question at a time, with a recommendation
when useful. This is mandatory schema setup, not a follow-up.

When the schema values are validated, materialize them with:
```bash
python skills/schema/scripts/write_schema.py \
  --vault .mnemo/<project-name> \
  --domain "<validated domain>" \
  --entity-types "<comma-separated validated entity types>" \
  --concept-categories "<comma-separated validated concept categories>"
```

## Step 3 - Global Profile

Check whether `~/.mnemo/wiki/entities/person-user.md` exists.

If absent, delegate to the onboard skill by reading `skills/onboard/SKILL.md` and
running its interview. Ask one question at a time, with the recommended/default
choice first. This is mandatory onboarding, not a follow-up.

After validation, create the profile with:
```bash
python skills/onboard/scripts/write_profile.py \
  --role "<role>" \
  --technical-level "<technical level>" \
  --language "<language>" \
  --domains "<domains>" \
  --proactivity "<High|Moderate|Low>" \
  --register "<Direct|Collaborative>"
```

If the profile is already present, keep it unchanged and continue without asking
profile questions.

## Step 4 - Search

Ask:
> "Enable semantic search with qmd? Recommended: yes. It adds local hybrid BM25 + vector search and falls back to BM25 if installation or registration fails. [Y/n]"

If yes or blank:
```bash
python skills/init/scripts/configure_search.py --vault .mnemo/<project-name> --backend qmd --install
```

If no:
```bash
python skills/init/scripts/configure_search.py --vault .mnemo/<project-name> --backend bm25
```

Use the JSON result to report the active backend. If qmd fails, BM25 is the
expected fallback; do not ask the user to install qmd manually.

## Step 5 - Gitignore

If the project has `.git/`, ask:
> "Add `.mnemo/` to `.gitignore`? Recommended: yes, to keep the local wiki out of version control. [Y/n]"

If yes or blank:
```bash
python skills/init/scripts/update_gitignore.py --project-root . --accept
```

If no, skip. Do not modify `.gitignore` without consent.

## Step 6 - Graphify

Ask:
> "Map this codebase with graphify? Recommended: yes. It creates `graphify-out/` so future sessions can inspect project structure without re-reading every source file. [Y/n]"

If no, record that graphify was not enabled and continue.

If yes or blank, attempt installation if `graphify --version` fails:
```bash
python -m pip install graphifyy
graphify install
```

If installation or graphify itself fails, continue cleanly and record that
graphify was not enabled. Do not present manual install work as a required init
step. It is acceptable to say that after the graphify environment is fixed, the
user can rerun `/mnemo:graphify` to create `graphify-out/`.

When graphify is available, delegate to the graphify skill by reading
`skills/graphify/SKILL.md`. Use its deterministic script:
```bash
python skills/graphify/scripts/run_graphify.py --project-root . --vault .mnemo/<project-name>
```

The graphify skill owns `.graphifyignore`, `graphify-out/`, graph validation,
wiki graph pages, index/log updates, and graphify status reporting.

## Step 7 - Obsidian

Ask:
> "Open this wiki in Obsidian? Recommended: yes. It gives you a local graph view, full-text search, and Web Clipper intake into `raw/`. [Y/n]"

If yes or blank, give instructions only. Do not install Obsidian automatically:
- Download Obsidian from `https://obsidian.md/` if needed.
- In Obsidian, choose **Open folder as vault** and select `.mnemo/<project-name>/`.
- Install the Web Clipper from `https://obsidian.md/clipper#more-browsers` and set the default save location to `raw/`.

If no, state that `.mnemo/<project-name>/` is Obsidian-compatible.

## Step 8 - Session Brief

Run:
```bash
python skills/init/scripts/update_session_brief.py --vault .mnemo/<project-name>
```

If graphify was enabled, run this after graphify so the brief can mention
`graphify-out/GRAPH_REPORT.md`.

## Step 9 - Agent Memory And Hook

Run:
```bash
python skills/init/scripts/wire_agent_memory.py --project-root . --project-name <project-name>
```

Add `--graphify` when graphify succeeded.

This script writes the mnemo stanza idempotently to a supported local agent
memory file and configures supported session-end hooks automatically when the
current project has a supported mechanism.

## Final Response

Report state, not handoff work:
- vault path
- active search backend
- graphify enabled or not enabled
- session brief path
- agent memory file updated or unchanged
- normal next use: drop files into `.mnemo/<project-name>/raw/` and run `/mnemo:ingest`
- if graphify was requested but failed: also mention that `/mnemo:graphify` can
  be rerun later after fixing graphify, independently from ingesting `raw/`

Do not add `/mnemo:schema`, `/mnemo:onboard`, manual install commands, schema
customization, profile creation, Obsidian installation, or memory setup as
optional follow-ups. Do not present `/mnemo:graphify` as an unfinished init step;
only mention it as a later retry when graphify was requested and failed. If any
required step above did not run, init is incomplete; finish it before reporting
success.
