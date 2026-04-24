---
name: mine
description: >
  Extract knowledge from the current conversation session worth persisting to the
  mnemo knowledge base. Scans for decisions, new entities, insights, and conclusions.
  Invoke explicitly (/mnemo:mine) or when the user expresses intent to save something
  ("remember this", "note that", "important") or when the agent detects high-value
  signals ("we decided", "in conclusion", "key insight") — in any language.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:mine). Other agentskills.io-compatible agents
  invoke by natural language.
metadata:
  author: mnemo contributors
  version: "0.4.2"
allowed-tools: Read Glob
---

## Flag: `--global`

If `--global` is present in the invocation arguments, substitute every `.mnemo/` path below with `~/.mnemo/`. All reads and saves operate on the global knowledge base instead of the local one.

## Trigger Patterns

Invoke this skill — or propose invoking it — when any of the following appear in the conversation, **in any language**:

**Explicit triggers** (user clearly wants to save something):

The user expresses intent to retain or save: phrases meaning "remember this", "note that", "keep this", "important", or a direct invocation of `/mnemo:mine`. Recognize these expressions regardless of the language the conversation is in.

**Implicit triggers** (agent detects high-value content):

- The user signals a resolved decision: phrases meaning "we decided", "we agreed on", "we'll use X for Y"
- The user signals a conclusion: phrases meaning "in conclusion", "to summarize", "the result is"
- The user describes an architecture or design: phrases meaning "the architecture is", "the structure will be"
- The user highlights an insight: phrases meaning "key insight", "important point", "notable finding"
- A term matching an entity type or concept category in `SCHEMA.md` is being defined for the first time

## Steps

### Step 0 — Read the knowledge base index and schema

Read `.mnemo/SCHEMA.md` to understand the domain's entity types and concept categories. Use these throughout Steps 1–3 to guide candidate extraction and categorization.

Read `.mnemo/index.md`. If shard files exist under `wiki/indexes/` (sources.md, entities.md,
concepts.md, synthesis.md), read those too. Build a set of known page titles from all index
lines of the form `- [Title](wiki/...)`.

If `.mnemo/index.md` does not exist, skip this step — the wiki is empty, everything is new.

### Step 1 — Scan the conversation for candidates

Review the current conversation from the beginning of this session. For each passage, ask:

- **Decision** — a resolved architectural, design, or process choice ("we'll use X", "we decided not to Y")
- **Entity** — a tool, person, project, or system not found in the index, matching an entity type from SCHEMA.md
- **Concept** — a technique, approach, tradeoff, or insight matching a concept category from SCHEMA.md
- **Synthesis** — a comparison, lesson learned, or cross-domain insight with no clear single-entity home

**Categorize each candidate** as one of the above before moving to Step 2. Use the SCHEMA.md types to guide entity and concept classification.

**Exclude:**
- Ephemeral task state ("I'm now on step 3", "let me check file X")
- Content whose title already appears in the index from Step 0
- Simple clarifications with no generalizable value
- In-progress work and open questions

### Step 2 — Present candidates

If no candidates found, report:
> "No new knowledge found in this session worth persisting."

Stop.

Otherwise, present a numbered menu:

```
Found N item(s) worth persisting:

1. [entity] "Tool X" — identified as preferred solution for Y
2. [decision] "Use event sourcing for audit trail" — agreed during architecture discussion
3. [concept] "Saga vs 2PC tradeoff" — distributed transaction pattern explained

Enter numbers to save (e.g. "1 3"), "a" for all, "n" to discard all:
```

### Step 3 — Save approved items

For each selected number, invoke `/mnemo:save` with:
- **title**: suggested title from Step 2
- **category**: use save's plural category names — `entities`, `concepts`, or `synthesis`. Route Decision candidates to `synthesis`.
- **content**: the relevant passage(s) from the conversation, formatted as markdown
- **tags**: 2–3 tags inferred from context and `SCHEMA.md`

**Decision candidates** from Step 1 map to `synthesis` (resolved design choices are AI-generated insights about the project).

Never save without user approval. Never batch-save without showing the numbered list first.

### Step 4 — Report

After all saves complete, list the titles saved. If 3 or more items were saved, suggest
running `/mnemo:lint` to verify integration.

---

### Step 5 — Offer activity log

After Step 4, if at least one item was saved, offer to write a session activity log.

Ask the user: "Log this session in `wiki/activity/`? (y/n)"

If the user declines, skip silently.

If the user confirms:

1. Determine today's date in `YYYY-MM-DD` format.
2. Set target path: `.mnemo/wiki/activity/YYYY-MM-DD.md` (substitute `--global` path `~/.mnemo/wiki/activity/YYYY-MM-DD.md` if the `--global` flag was set).
3. If the file already exists (multiple mine runs in one day): read it, locate the `## Items Saved` heading, and insert the new bullet lines directly before the `## Links` heading. Also update the `updated:` field in the YAML frontmatter to today's date.
4. If the file does not exist, create it with this exact structure:

```yaml
---
title: Session YYYY-MM-DD
category: activity
tags: [session, YYYY-MM-DD]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

```markdown
# Session YYYY-MM-DD

> *Generated: <ISO-8601 timestamp>*

---

## Summary

[2–3 sentences: what was worked on, problems solved, decisions made]

## Items Saved

[One line per item saved in Step 3:]
- [[Page Title]] (`category`)

## Links

[Wikilinks to the most relevant entities or concepts referenced today]
```

*(Write these as a single file — the frontmatter and body blocks above are shown separately for clarity only.)*

5. Report: "Activity log written to `wiki/activity/YYYY-MM-DD.md`."
