# Agent Memory Integration

Wire mnemo into your agent's memory files so it automatically consults and maintains the wiki across sessions.

---

## Claude Code — `CLAUDE.md`

Add this stanza to your project's `CLAUDE.md`:

```markdown
## Knowledge Base

This project uses mnemo for knowledge management.

- Wiki: `.mnemo/<project-name>/wiki/` — synthesized, categorized, interlinked pages
- Index: `.mnemo/<project-name>/index.md` — categorized table of contents

**Before answering any factual question** that might be in the knowledge base, run `/mnemo:query <topic>`. If results are returned, synthesize from them. If 0 results, say so explicitly — never invent wiki content.

**To ingest new sources**: drop files into `.mnemo/<project-name>/raw/` and run `/mnemo:ingest`.

**To save an insight**: run `/mnemo:save` with a descriptive title.

**To check health**: run `/mnemo:lint` after any session where pages were added or modified.
```

---

## Cursor / OpenCode — `AGENTS.md`

Add this stanza to `AGENTS.md` at the project root:

```markdown
## Knowledge Base (mnemo)

Wiki location: `.mnemo/<project-name>/wiki/`
Index: `.mnemo/<project-name>/index.md`

Workflow:
- Query before answering: invoke the `query` skill with the topic.
- Ingest new sources: invoke the `ingest` skill after adding files to `.mnemo/<project-name>/raw/`.
- Save insights: invoke the `save` skill with a descriptive title.
- Lint after edits: invoke the `lint` skill at session end.

Skill invocation (agentskills.io format): skills are in `skills/<name>/SKILL.md`.
```

---

## Gemini CLI — `GEMINI.md`

Add this stanza to `GEMINI.md` at the project root:

```markdown
## Knowledge Base (mnemo)

This project maintains a synthesized wiki at `.mnemo/<project-name>/wiki/`.

- Consult `.mnemo/<project-name>/index.md` before answering domain questions.
- Read relevant wiki pages (sources, entities, concepts, synthesis) for grounded answers.
- Skill instructions are in `skills/<skill-name>/SKILL.md` — follow them to ingest, query, save, and lint.
```

---

## How the Wiki Compounds

Each ingest run:
1. Creates a source summary page.
2. Updates or creates entity and concept pages with citations.
3. Enriches 10–15 related existing pages with new wikilinks.

Over time, entity and concept pages accumulate multiple source references, making them richer and more connected. The index grows and eventually shards. Query results improve as the graph densifies.

The wiki is the agent's long-term memory — raw files are the ground truth, wiki pages are the synthesized knowledge.

---

## Cross-Project Global Memory

Place shared knowledge (domain concepts that apply across projects) in `~/.mnemo/` using the same directory structure. The `query` skill searches local first, then falls back to global if no results are found.

---

## Adding Support for a New Agent

mnemo uses an extension file pattern for agent-specific wiring. To add support for a new agent:

1. Create `skills/init/<agent-name>.md` (e.g. `skills/init/cursor.md`)
2. Follow the structure of existing extensions (`claude-code.md`, `opencode.md`, `gemini.md`):
   - Frontmatter with `name` and `description`
   - Ask the user if they want to wire mnemo into their agent's memory config file
   - If yes: check for an existing stanza, then append it
   - Confirm when done
3. The core `skills/init/SKILL.md` will automatically delegate to your file in step 11.

No changes to the core skill are needed.
