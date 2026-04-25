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
  version: "0.7.0"
allowed-tools: Read Write Edit Glob Grep Bash
---

Dispatch the mnemo-ingestor sub-agent to handle this ingest request.

## Step 0 — Dispatch agent

1. Locate the plugin root: find the directory containing `agents/ingestor.md`
   relative to this skill file (two levels up from `skills/ingest/`).

2. Read the full contents of `agents/ingestor.md`.

3. Spawn a sub-agent using the Agent tool with:
   - prompt: full contents of `agents/ingestor.md` followed by:
     ```
     ## Inputs
     vault: .mnemo/<project-name>/
     source: <$ARGUMENTS — file path passed by the user>
     ```
     Replace `<project-name>` with the current working directory's base name,
     or read it from `.mnemo/` (the first subdirectory found there).
   - model: opus
   - tools: Read, Write, Edit, Grep, Glob, Bash

4. Wait for the agent to complete.

5. Relay the agent's final report to the user verbatim.
