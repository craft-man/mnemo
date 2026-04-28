---
name: mnemo-init-claude-code
description: Claude Code-specific wiring for mnemo init. Run after skills/init/SKILL.md completes.
---

## Step 8 — CLAUDE.md wiring

Ask the user:
> "Want me to add a memory stanza to `CLAUDE.md` so I remember this wiki in future sessions? [y/n]"

If `[n]`: do nothing.

If `[y]`:

Check if `CLAUDE.md` already contains the heading `## mnemo`. If yes: skip silently — the stanza is already present.

Otherwise, build the stanza based on what was initialized:

```markdown
## mnemo

This project has a mnemo knowledge base in `.mnemo/<project-name>/`.

At session startup:
- Read `.mnemo/<project-name>/SESSION_BRIEF.md` if it exists.
- Read `graphify-out/GRAPH_REPORT.md` only when the task concerns codebase structure.
- Do not load the whole wiki at startup.
- If the brief was not auto-read at startup, the user can run `/mnemo:context`.

During the session:
- Query it with `/mnemo:query <term>` before answering factual questions.
- Ingest new sources with `/mnemo:ingest`
- When a spec or plan is finalized (e.g. from superpowers brainstorming or writing-plans), move it to `.mnemo/<project-name>/raw/` and run `/mnemo:ingest` to add it to the knowledge base
```

If graphify was set up in step 9 of the core, append this line to the stanza:
```
- Run `/mnemo:graphify` after significant code changes to keep the knowledge graph up to date
```

Then:
- If `CLAUDE.md` exists: append the stanza at the end of the file, preceded by a blank line.
- If `CLAUDE.md` does not exist: create it with the stanza as the only content.

Confirm:
> "Done — stanza added to `CLAUDE.md`. I'll remember this wiki in future sessions."

---

## Step 8b — Stop hook injection

Ensure the `.claude/` directory exists in the current project (create it if needed). Then check if `.claude/settings.local.json` exists.

**Case A — file does not exist:**
Create `.claude/settings.local.json`:
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'mnemo — session ending. Run /mnemo:mine to capture insights from this session.'"
          }
        ]
      }
    ]
  }
}
```

**Case B — file exists, no `hooks` key:**
Read the file. Add the `"hooks"` key from Case A at the top level, preserving all existing content.

**Case C — file exists, `hooks.Stop` exists but no mnemo entry:**
Read the file. Append the mnemo hook object to the existing `hooks.Stop` array, preserving all existing hooks.

**Case D — file already contains the mnemo echo command:**
Skip silently.

Confirm:
> "Stop hook added to `.claude/settings.local.json` — you'll be reminded to run `/mnemo:mine` at session end."
