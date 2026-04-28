---
name: mnemo-init-copilot
description: Best-effort Copilot-specific wiring for mnemo init. Run after skills/init/SKILL.md completes when the user wants a manual/local fallback.
---

## Agent wiring — best effort

Copilot project auto-load behavior varies by product surface and repository setup. Do not promise automatic reuse unless the current environment confirms a supported project instruction file.

Ask the user:
> "Want me to add best-effort mnemo instructions for Copilot? Automatic loading depends on your Copilot surface. [y/n]"

If `[n]`: do nothing.

If `[y]`:

Prefer an existing repository instruction file that Copilot is known to read in the current environment. If none is confirmed, write a local fallback stanza to `AGENTS.md` for manual use.

```markdown
## Knowledge Base (mnemo)

This project has a mnemo knowledge base in `.mnemo/<project-name>/`.

At session startup:
- Read `.mnemo/<project-name>/SESSION_BRIEF.md` if available.
- Read `graphify-out/GRAPH_REPORT.md` only for codebase-structure tasks.
- Do not load the whole wiki at startup.
- If the brief was not auto-read at startup, the user can run `/mnemo:context`.

During the session:
- Use `/mnemo:query <term>` or read `skills/query/SKILL.md` before answering factual questions.
- Use `skills/ingest/SKILL.md`, `skills/save/SKILL.md`, and `skills/lint/SKILL.md` for maintenance.
```

Confirm:
> "mnemo instructions written as a best-effort Copilot/local fallback. Automatic reuse depends on your Copilot environment."
