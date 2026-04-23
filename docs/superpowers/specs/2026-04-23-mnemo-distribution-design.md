# mnemo — Distribution & Friction Reduction

**Date:** 2026-04-23
**Goal:** Publish mnemo on the Claude Code marketplace and remove the `--plugin-dir` friction for end users.

---

## Context

mnemo currently requires `git clone` + `--plugin-dir` on every invocation. The goal is to make installation a one-liner via the Claude Code marketplace, add a Python bootstrap script so the wiki can be initialized without Claude, and wire mnemo into `CLAUDE.md` automatically so Claude remembers the wiki in future sessions.

Target audience: Claude Code users first. Multi-agent support is a future concern — this design must not block it but does not implement it.

---

## Scope

Three independent deliverables, in priority order:

1. **Marketplace publication** — `plugin.json` updates + `commands/mnemo/` directory
2. **`scripts/init_mnemo.py`** — Python stdlib bootstrap script with interactive two-tier setup
3. **CLAUDE.md auto-wiring** — `/mnemo:init` proposes a memory stanza at the end of init

No changes to existing `skills/*/SKILL.md` files. Additive only.

---

## Target user flow (post-implementation)

```
# 1. Install once, globally
/plugin marketplace add craft-man/mnemo

# 2. Bootstrap a project — no Claude needed
python scripts/init_mnemo.py

# 3. Memory wiring — proposed by /mnemo:init
→ Claude offers to append a stanza to CLAUDE.md

# 4. Normal usage
/mnemo:schema → /mnemo:ingest → /mnemo:query
```

---

## Deliverable 1 — Marketplace publication

### plugin.json changes

Add three missing fields required for the marketplace listing:

```json
{
  "name": "mnemo",
  "version": "0.3.0",
  "description": "Agentic Knowledge Management System — a Second Brain for Claude Code.",
  "author": { "name": "mnemo contributors" },
  "homepage": "https://github.com/craft-man/mnemo",
  "repository": "https://github.com/craft-man/mnemo",
  "license": "MIT",
  "keywords": ["knowledge-base", "wiki", "second-brain", "obsidian", "rag-alternative"],
  "category": "productivity"
}
```

Fields added: `repository`, `keywords`, `category`.

### commands/mnemo/ directory

One `.md` file per command. Each file is a minimal slash command descriptor that references the underlying skill. No logic lives here — the SKILL.md files remain the source of truth.

```
commands/mnemo/
├── init.md
├── schema.md
├── ingest.md
├── query.md
├── lint.md
├── save.md
└── stats.md
```

Example — `commands/mnemo/ingest.md`:

```markdown
---
description: Process raw files in .mnemo/raw/ into synthesized wiki pages
---

Run the mnemo ingest skill.
```

No changes to `skills/*/SKILL.md`.

---

## Deliverable 2 — scripts/init_mnemo.py

Pure Python stdlib (3.10+), no dependencies. Creates the `.mnemo/` and/or `~/.mnemo/` directory structure without requiring Claude.

### CLI

```bash
python scripts/init_mnemo.py           # interactive, targets current directory
python scripts/init_mnemo.py ./notes   # interactive, targets specified directory
```

The `--global` flag is not exposed — the interactive prompt handles scope selection.

### Interactive prompt

```
mnemo — Agentic Knowledge Management System

How would you like to initialize mnemo?

  [1] Project + Global (recommended)
      → .mnemo/   knowledge specific to this project
      → ~/.mnemo/ knowledge reusable across all projects
      Best when you work across multiple projects.

  [2] Project only
      → .mnemo/   self-contained knowledge base for this project

  [3] Global only
      → ~/.mnemo/ single vault shared across all projects

Choice [1/2/3] (default: 1):
```

### Directory structure created

For each selected tier:

```
<root>/
├── raw/
├── wiki/
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   └── synthesis/
├── index.md      ← seeded with category headings
├── log.md        ← empty with header comment
└── SCHEMA.md     ← generic template, edited via /mnemo:schema
```

### Completion output

```
✓ .mnemo/ initialized in /path/to/project
✓ ~/.mnemo/ initialized

Next steps:
  Run /mnemo:schema to define your domain taxonomy
  Drop files into .mnemo/raw/ and run /mnemo:ingest
```

### Guard clause

If the target directory already contains `.mnemo/`:

```
.mnemo/ already exists.
Use /mnemo:init to re-initialize or /mnemo:schema to revise the taxonomy.
```

### Scope

The script creates structure only. Taxonomy definition (`SCHEMA.md` customization) remains Claude's responsibility via `/mnemo:schema`. The separation is intentional.

---

## Deliverable 3 — CLAUDE.md auto-wiring

At the end of `/mnemo:init`, Claude proposes adding a memory stanza to `CLAUDE.md`. This ensures Claude remembers the wiki in future sessions without being told.

### Prompt to user

```
mnemo is initialized in this project. Want me to add a memory stanza
to CLAUDE.md so I remember the wiki in future sessions? [y/n]
```

### Stanza written on approval

```markdown
## mnemo

This project has a mnemo knowledge base in `.mnemo/`.
- Query it with `/mnemo:query <term>` before answering factual questions
- Ingest new sources with `/mnemo:ingest`
- Global knowledge base available at `~/.mnemo/` (if initialized)
```

### Rules

| Condition | Behavior |
|---|---|
| `CLAUDE.md` exists | Append stanza at end of file |
| `CLAUDE.md` does not exist | Create file with stanza only |
| Stanza already present | Skip silently, no duplicate |
| Global vault initialized | Include the global line in the stanza |
| User answers `n` | Do nothing, no retry |

Claude never writes to `CLAUDE.md` without explicit `y` confirmation.

---

## What this does NOT change

- `skills/*/SKILL.md` — untouched
- `.mnemo/` directory layout — unchanged
- Existing wiki pages and conventions — unchanged
- Multi-agent support — not in scope, but `commands/mnemo/` and the agentskills.io-compatible skill frontmatter leave the door open

---

## Deliverable 4 — README update

Rewrite the Installation section to reflect the new flow, and add a Quick start section that leads with `init_mnemo.py`.

### Installation section (replaces current)

```markdown
## Installation

**Requirements:** [Claude Code](https://claude.ai/code) CLI

### Claude Code marketplace (recommended)

/plugin marketplace add craft-man/mnemo

### Manual (git clone)

git clone https://github.com/craft-man/mnemo
claude --plugin-dir ./mnemo
```

### Quick start section (new, placed after Installation)

```markdown
## Quick start

Bootstrap a new knowledge base without Claude:

python scripts/init_mnemo.py

Then in Claude Code:

/mnemo:schema      # define your domain taxonomy
# drop files into .mnemo/raw/
/mnemo:ingest      # synthesize → wiki pages
/mnemo:query <term>
```

### Other README changes

- Remove the `alias claude="claude --plugin-dir ..."` workaround — no longer needed as primary flow
- Keep it as a note under the manual install path for users who prefer git clone
- Update the search backends section to mention that `init_mnemo.py` does not configure qmd — that remains `/mnemo:init`'s responsibility

---

## Out of scope (v2)

- `npx skills add` support for multi-agent
- `AGENTS.md` / `GEMINI.md` integration
- `qmd` setup during `init_mnemo.py`
