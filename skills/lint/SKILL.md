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
  (scripts/wiki_lint.py).
metadata:
  author: mnemo contributors
  version: "0.6.0"
allowed-tools: Read Write Edit Glob Grep Bash
---

Dispatch the mnemo-linter sub-agent to handle this audit.

## Step 0 — Dispatch agent

1. Locate the plugin root: find the directory containing `agents/linter.md`
   relative to this skill file (two levels up from `skills/lint/`).

2. Read the full contents of `agents/linter.md`.

3. Spawn a sub-agent using the Agent tool with:
   - prompt: full contents of `agents/linter.md` followed by:
     ```
     ## Inputs
     vault: .mnemo/<project-name>/
     ```
   - model: opus
   - tools: Read, Write, Edit, Grep, Glob, Bash

4. Wait for the agent to complete.

5. Relay the agent's report to the user verbatim.
