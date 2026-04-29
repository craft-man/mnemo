---
name: mnemo-init-cursor
description: Cursor-specific wiring for mnemo-init. Run after skills/init/SKILL.md completes.
---

## Agent wiring — AGENTS.md

Ask the user:
> "Want me to add a memory stanza to `AGENTS.md` so Cursor remembers the wiki in future sessions? [y/n]"

If `[n]`: do nothing.

If `[y]`:

Check if `AGENTS.md` already contains the heading `## Knowledge Base (mnemo)`. If yes: skip silently.

Otherwise, append to `AGENTS.md` (create it if it doesn't exist):

```markdown
## Knowledge Base (mnemo)

Wiki location: `.mnemo/<project-name>/wiki/`
Index: `.mnemo/<project-name>/index.md`
Session brief: `.mnemo/<project-name>/SESSION_BRIEF.md`

Workflow:
- At session startup, read `SESSION_BRIEF.md` if present. Read `graphify-out/GRAPH_REPORT.md` only for codebase-structure tasks. Do not load the whole wiki.
- If the brief was not auto-read at startup, the user can run `/mnemo:context`.
- Query before answering: invoke the `query` skill with the topic (read `skills/query/SKILL.md`).
- Ingest new sources: invoke the `ingest` skill after adding files to `.mnemo/<project-name>/raw/` (read `skills/ingest/SKILL.md`).
- Save insights: invoke the `save` skill with a descriptive title (read `skills/save/SKILL.md`).
- Lint after edits: invoke the `lint` skill at session end (read `skills/lint/SKILL.md`).
```

Confirm:
> "Done — stanza added to `AGENTS.md`."
