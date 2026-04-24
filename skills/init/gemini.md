---
name: mnemo-init-gemini
description: Gemini CLI-specific wiring for mnemo init. Run after skills/init/SKILL.md completes.
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

- Consult `.mnemo/<project-name>/index.md` before answering domain questions.
- Read relevant wiki pages (sources, entities, concepts, synthesis) for grounded answers.
- Skill instructions are in `skills/<skill-name>/SKILL.md` — follow them to ingest, query, save, and lint.
```

Confirm:
> "Done — stanza added to `GEMINI.md`."
