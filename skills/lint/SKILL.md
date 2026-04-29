---
name: lint
description: >
  Audit the mnemo knowledge base for structural issues: orphaned pages, broken
  index links, missing YAML frontmatter, missing source citations, oversized pages,
  pages with no inbound wikilinks, stale temporal claims, superseded pages missing
  a History section, and unprocessed raw files.
  Presents each finding as a proposed edit awaiting user approval. Use when the user
  says "check my wiki", "audit the knowledge base", "lint my notes", "find broken
  links", or "health check". Run periodically and after any batch ingest.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:lint). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for faster auditing
  (skills/lint/wiki_lint.py).
metadata:
  author: mnemo contributors
  version: "0.16.2"
allowed-tools: Read Write Edit Glob Grep Bash
---

Dispatch the mnemo-linter workflow using the portable dispatch contract.

## Step 0 — Resolve workflow and dispatch path

1. Locate the plugin root: find the directory containing `agents/linter.md`
   relative to this skill file (two levels up from `skills/lint/`).

2. Read the full contents of `agents/linter.md`.

3. Read `skills/references/subagent-dispatch.md`. Use it as the canonical
   dispatch contract.

4. Build the runtime inputs block:
   ```markdown
   ## Inputs
   vault: .mnemo/<project-name>/
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
   - `workflow_name`: `mnemo-linter`
   - `workflow_spec`: full contents of `agents/linter.md`
   - `inputs_block`: the block from step 4
   - `preferred_reasoning`: `heavy`
   - `allowed_tools`: `Read, Write, Edit, Grep, Glob, Bash`

7. If delegated, wait for completion and relay the final report.
   If executed inline, follow the workflow directly and present its response.
