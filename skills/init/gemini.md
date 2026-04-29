---
name: mnemo-init-gemini
description: Gemini CLI-specific wiring for mnemo-init. Run after skills/init/SKILL.md completes.
---

## Agent wiring — GEMINI.md

Ask the user:
> "Want me to add a memory stanza to `GEMINI.md` so Gemini CLI remembers the wiki in future sessions? [y/n]"

If `[n]`: do nothing.

If `[y]`:

Check if `GEMINI.md` already contains the heading `## Knowledge Base (mnemo)`. If yes: skip silently.

Otherwise, append to `GEMINI.md` (create it if it doesn't exist):

```markdown
## Knowledge Base (mnemo)

This project maintains a synthesized wiki at `.mnemo/<project-name>/wiki/`.

- At session startup, read `.mnemo/<project-name>/SESSION_BRIEF.md` if present.
- Read `graphify-out/GRAPH_REPORT.md` only when the task concerns codebase structure.
- Do not load the whole wiki at startup; use `/mnemo:query <term>` for factual lookup.
- If the brief was not auto-read at startup, the user can run `/mnemo:context`.
- Skill instructions are in `skills/<skill-name>/SKILL.md` — follow them to ingest, query, save, and lint.
```

Confirm:
> "Done — stanza added to `GEMINI.md`."
