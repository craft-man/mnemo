---
name: ingest
description: >
  Process raw files in raw/ into synthesized, categorized wiki pages via LLM
  analysis. Extracts entities and concepts, creates bidirectional wikilinks, and
  enforces source citations. Use when the user says "ingest this", "add this to
  my wiki", "process my notes", "compile this paper into the knowledge base",
  "add to second brain", or drops new files into raw/ and asks to process them.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:ingest). Other agentskills.io-compatible
  agents invoke by natural language. Optional: Python 3.10+ for BM25 search
  acceleration (scripts/wiki_search.py).
metadata:
  author: mnemo contributors
  version: "0.16.2"
allowed-tools: Read Write Edit Glob Grep Bash
---

Dispatch the mnemo-ingestor workflow using the portable dispatch contract.

## Step 0 — Resolve workflow and dispatch path

1. Locate the plugin root: find the directory containing `agents/ingestor.md`
   relative to this skill file (two levels up from `skills/ingest/`).

2. Read the full contents of `agents/ingestor.md`.

3. Read `skills/references/subagent-dispatch.md`. Use it as the canonical
   dispatch contract.

4. Build the runtime inputs block:
   ```markdown
   ## Inputs
   vault: .mnemo/<project-name>/
   source: <$ARGUMENTS — file path passed by the user>
   ```
   Replace `<project-name>` with the current working directory's base name,
   or read it from `.mnemo/` (the first subdirectory found there).

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
   - `workflow_name`: `mnemo-ingestor`
   - `workflow_spec`: full contents of `agents/ingestor.md`
   - `inputs_block`: the block from step 4
   - `preferred_reasoning`: `heavy`
   - `allowed_tools`: `Read, Write, Edit, Grep, Glob, Bash`

7. If delegated, wait for completion and relay the final report.
   If executed inline, follow the workflow directly and present its response.
