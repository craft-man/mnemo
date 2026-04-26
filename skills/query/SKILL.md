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
  version: "0.8.0"
allowed-tools: Read Glob Grep Bash
---

Dispatch the mnemo-archivist sub-agent to handle this query.

## Step 0 — Dispatch agent

1. Locate the plugin root: find the directory containing `agents/archivist.md`
   relative to this skill file (two levels up from `skills/query/`).

2. Read the full contents of `agents/archivist.md`.

3. Spawn a sub-agent using the Agent tool with:
   - prompt: full contents of `agents/archivist.md` followed by:
     ```
     ## Inputs
     vault: .mnemo/<project-name>/
     query: <$ARGUMENTS — the user's search query>
     ```
   - model: sonnet
   - tools: Read, Write, Edit, Grep, Glob, Bash

4. Wait for the agent to complete.

5. Relay the agent's response to the user verbatim.
