---
name: query
description: >
  Search the mnemo wiki knowledge base. Uses qmd (hybrid BM25 + vector semantic
  search) if configured at init, otherwise falls back to BM25 ranked retrieval.
  Supports tag:, since:, category:, backlinks:, and top-linked modifiers. Use when
  the user asks "what does my wiki say about X", "search my notes for Y", "find pages
  about Z", "query the knowledge base", "what do I know about X", or "look up X in my
  second brain". Falls back to global knowledge base if local returns no results.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:query). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for faster BM25
  (scripts/wiki_search.py).
metadata:
  author: mnemo contributors
  version: "0.13.0"
allowed-tools: Read Glob Grep Bash
---

Dispatch the mnemo-archivist workflow using the portable dispatch contract.

## Step 0 — Resolve workflow and dispatch path

1. Locate the plugin root: find the directory containing `agents/archivist.md`
   relative to this skill file (two levels up from `skills/query/`).

2. Read the full contents of `agents/archivist.md`.

3. Read `skills/references/subagent-dispatch.md`. Use it as the canonical
   dispatch contract.

4. Build the runtime inputs block:
   ```markdown
   ## Inputs
   vault: .mnemo/<project-name>/
   query: <$ARGUMENTS — the user's search query>
   ```

5. Select a dispatch adapter:
   - If the current host has a matching adapter in `skills/dispatch/<host>.md`,
     read it and follow it.
   - If the host is unknown, ambiguous, or lacks reliable sub-agent support,
     use `skills/dispatch/inline.md`.

   Known adapters:
   - `skills/dispatch/claude-code.md`
   - `skills/dispatch/codex.md`
   - `skills/dispatch/cursor.md`
   - `skills/dispatch/gemini.md`
   - `skills/dispatch/opencode.md`
   - `skills/dispatch/inline.md`

6. Dispatch the workflow with these inputs:
   - `workflow_name`: `mnemo-archivist`
   - `workflow_spec`: full contents of `agents/archivist.md`
   - `inputs_block`: the block from step 4
   - `preferred_reasoning`: `balanced`
   - `allowed_tools`: `Read, Write, Edit, Grep, Glob, Bash`

7. If delegated, wait for completion and relay the final report.
   If executed inline, follow the workflow directly and present its response.
