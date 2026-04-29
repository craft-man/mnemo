---
name: mnemo-init-codex
description: Codex-specific notes for mnemo-init. Use with skills/init/SKILL.md.
---

## Codex Init Contract

Codex must complete the whole init contract in the same run. Do not defer
schema, onboarding/profile check, search config, graphify decision, Obsidian
decision, session brief generation, or `AGENTS.md` wiring to a follow-up.

Use the core `skills/init/SKILL.md` workflow and its skill-owned scripts:

- `skills/init/scripts/create_vault.py`
- `skills/schema/scripts/write_schema.py`
- `skills/onboard/scripts/write_profile.py`
- `skills/init/scripts/configure_search.py`
- `skills/graphify/scripts/run_graphify.py`
- `skills/init/scripts/update_session_brief.py`
- `skills/init/scripts/wire_agent_memory.py`

Collect answers in chat one question at a time before invoking each
non-interactive script. If the user provides minimal detail, use safe complete
defaults from the core skill. If `.mnemo/<project-name>/` already exists, stop
without rerunning schema, onboard, graphify, search, or memory wiring.
