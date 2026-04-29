---
name: mnemo-init-codex
description: Codex-specific wiring for mnemo init. Use with skills/init/SKILL.md.
---

## Codex Init Contract

Codex must complete the whole init contract in the same run. Do not defer schema,
onboarding, search config, session brief generation, graphify decision, Obsidian
decision, or `AGENTS.md` wiring to a follow-up.

Before launching the script, ask the user for the required schema and onboarding
answers in chat. If the user provides minimal detail, use safe complete defaults:
- Schema domain: `General knowledge base for this project.`
- Entity types: `Person, Tool, Project`
- Concept categories: `Pattern, Technique, Problem`
- Role: `Solo developer`
- Technical level: `CLI comfortable`
- Language: `English`
- Domains: `General knowledge`
- Proactivity: `Moderate`
- Register: `Direct`
- Search backend: `bm25`
- Graphify: off unless explicitly requested
- Obsidian: off unless explicitly requested

Run the public wrapper with explicit values:

```bash
python scripts/init_mnemo.py --non-interactive \
  --schema-domain "<domain>" \
  --schema-entity-types "<entity types>" \
  --schema-concept-categories "<concept categories>" \
  --role "<role>" \
  --technical-level "<technical level>" \
  --language "<language>" \
  --domains "<domains>" \
  --proactivity "<proactivity>" \
  --register "<register>" \
  --search-backend bm25
```

Add `--enable-graphify`, `--open-obsidian`, or `--search-backend qmd` only when
the user explicitly chooses those options. The script preserves an existing
global user profile without rewriting it.
