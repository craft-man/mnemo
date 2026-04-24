---
name: graphify
description: >
  Map the current project codebase into a queryable mnemo knowledge graph using graphify.
  Converts graphify's structured output (graph.json) directly into mnemo wiki pages —
  entities, concepts, and a synthesis report — so agents can answer questions about the
  project without re-reading source files on every session.
  Use when the user says "map my codebase", "build a knowledge graph", "index my project",
  "graphify this", or invokes /mnemo:graphify explicitly.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:graphify). Other agentskills.io-compatible
  agents invoke by natural language. Requires: graphify (pip install graphifyy && graphify install).
metadata:
  author: mnemo contributors
  version: "0.5.1"
allowed-tools: Read Write Edit Glob Bash
---

Map the current project codebase into a queryable mnemo knowledge graph.

> **Scope:** This skill operates on the local `.mnemo/` knowledge base only. The `--global` flag is not supported.

## Prerequisites

**1. mnemo initialized** — check if `.mnemo/<project-name>/wiki/sources/` exists. If not:
> "Knowledge base not initialized. Run `/mnemo:init` first."
Stop.

**2. graphify installed** — run `graphify --version`. If the command fails or is not found:
> "graphify is not installed. Install it with:
> `pip install graphifyy && graphify install`"
Stop.

## Step 1 — Prepare `.graphifyignore`

Check if `.graphifyignore` exists at project root.

**Default exclusion list:**
```
.mnemo/
graphify-out/
node_modules/
.git/
__pycache__/
*.pyc
.venv/
dist/
build/
coverage/
.next/
.nuxt/
```

**If `.graphifyignore` does not exist:** create it with the full default list above.
Report: "Created `.graphifyignore` with default exclusions."

**If `.graphifyignore` exists:** read it. For each entry in the default list that is absent, append it.
Report only what was added: "Updated `.graphifyignore` — added: `.mnemo/`, `graphify-out/`."
If nothing was missing: no report.

Note: if `.mnemo/<project-name>/graph.json` already exists, this is an incremental re-run. Graphify will use its SHA256 cache automatically — only changed files are reprocessed.

## Step 2 — Run graphify

Run from the project root:
```bash
graphify .
```

Wait for completion. If graphify exits non-zero, report the error and stop:
> "graphify failed: <error output>. Fix the error above and re-run `/mnemo:graphify`."

On success, graphify produces:
- `graphify-out/graph.json` — structured graph (nodes + edges)
- `graphify-out/GRAPH_REPORT.md` — narrative report (god nodes, surprising connections, suggested questions)
- `graphify-out/cache/` — SHA256 cache for incremental re-runs

## Step 3 — Convert nodes to wiki pages

If `graphify-out/graph.json` does not exist: report "graphify produced no output file. Nothing was written to the wiki." and stop.

After reading the file, if `nodes` is empty or absent: report "graphify produced no nodes. The project may have no recognized code structure. Nothing was written to the wiki." and stop.

Read `graphify-out/graph.json`.

### Node type mapping

| graphify node type | mnemo category | Target directory |
|---|---|---|
| `class`, `function`, `module`, `file`, `system`, `project`, `person`, `tool` | `entities` | `.mnemo/<project-name>/wiki/entities/` |
| `concept`, `pattern`, `technique`, `idea`, `problem` | `concepts` | `.mnemo/<project-name>/wiki/concepts/` |
| Any unrecognized type | `entities` | `.mnemo/<project-name>/wiki/entities/` |

### Filename

`<type>-<slug>.md` where slug = node label lowercased, spaces → `-`, non-alphanumeric characters (except `-`) removed.

Collision rule: if two nodes produce the same slug, append the community ID: `<type>-<slug>-c<community_id>.md`.

> Note: graphify node types (`class`, `function`, `module`, etc.) are used directly as filename type-prefixes. They are not required to match the SCHEMA.md entity vocabulary.

### Field mapping

| Template variable | graph.json field | Fallback |
|---|---|---|
| `<node label>` | `node.label` | — (required, skip node if absent) |
| `<node description>` | `node.description` | `"No description available."` |
| `<community_id>` | `node.community` | omit tag, write `Community: unknown` in byline |
| Relation tag (`EXTRACTED`/`INFERRED`/`AMBIGUOUS`) | `edge.type` | `EXTRACTED` |
| Confidence score | `edge.confidence` | omit the `*(confidence: X)*` fragment |

### Page format

```markdown
---
title: <node label>
category: <entities | concepts>
tags: [graphify, <node type>, c<community_id>]
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# <node label>

> *Type: <node type> — Community: <community_id>*

---

## Description

<node description from graph.json>

## Sources

- [[Codebase Graph Report]]

## Relations

- **<relationship type>** → [[<target node label>]] `EXTRACTED`
- **<relationship type>** → [[<target node label>]] `INFERRED` *(confidence: 0.87)*
- **<relationship type>** → [[<target node label>]] `AMBIGUOUS`

## Links

- [[<connected node label>]]
```

Only include relations where the target node exists in `graph.json`. Skip dangling edges.
If a node has no relations, omit the `## Relations` section entirely.

### Incremental update (re-run)

If `.mnemo/<project-name>/graph.json` exists (prior run detected in Step 1):

1. Load old graph from `.mnemo/<project-name>/graph.json` and new graph from `graphify-out/graph.json`.
2. Compute delta:
   - **Added nodes** — write new wiki pages.
   - **Modified nodes** (description or edges changed) — update the existing page:
     1. Replace the `## Description` section body.
     2. Replace the `## Relations` section body (or add/remove the section if it appears/disappears).
     3. Update `updated:` frontmatter field to today.
     If `## Description` or `## Relations` cannot be located in the existing page, append the updated content at the end of the file and update `updated:` in the frontmatter. Warn: "`Section not found in <filename> — content appended.`"
   - **Removed nodes** — do not delete the page. Append this block before `## Links`:
     Before appending, check whether a line matching `> **Note (` already appears above `## Links` in the page. If it does, skip the append.
     ```
     > **Note (<YYYY-MM-DD>):** This node was removed from the graphify graph on re-run. Content may be stale.
     ```
   - **Unchanged nodes** — do not touch the page.

### First run

Write all nodes as new pages. Track count for the Step 5 report.

## Step 4 — Convert GRAPH_REPORT.md to synthesis page

If `graphify-out/GRAPH_REPORT.md` does not exist, skip this step and note it in the final report.

Read `graphify-out/GRAPH_REPORT.md`. Write `.mnemo/<project-name>/wiki/synthesis/codebase-graph-report.md`:

```markdown
---
title: Codebase Graph Report
category: synthesis
tags: [graphify, codebase, graph-report]
source: graphify
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# Codebase Graph Report

> *Generated by graphify on <YYYY-MM-DD>. Re-run `/mnemo:graphify` to refresh.*

---

<full body of graphify-out/GRAPH_REPORT.md, preserved verbatim>

## Links

<wikilinks to every god node named in the report, e.g. [[AuthService]], [[DatabaseLayer]]>
```

**On re-run:** overwrite this page entirely — it is always regenerated from the latest report.
Update `created:` only if the file is new; always update `updated:`.

## Step 5 — Integrate

**Persist graph** — copy `graphify-out/graph.json` → `.mnemo/<project-name>/graph.json`. This is the baseline for the next incremental run.

**Update index** — for each new page written, append to `.mnemo/<project-name>/index.md` under the matching heading (`## Entities`, `## Concepts`, `## Synthesis`):
```
- [<Page Title>](wiki/<category>/<filename>.md)
```
If a heading (`## Entities`, `## Concepts`, or `## Synthesis`) does not exist in `index.md`, append it before adding the entry.
If total wiki pages ≥ 150: write to `wiki/indexes/<category>.md` shard (create if absent). Ensure `.mnemo/<project-name>/index.md` has a link to each shard: `- [Entities Index](wiki/indexes/entities.md)`.

**Update log** — append to `.mnemo/<project-name>/log.md`:
```
- graphify-out/graph.json | <UTC ISO timestamp> | graphify
```

**Report:**
```
graphify run complete.
  Pages created:        N
  Pages updated:        M
  Pages unchanged:      K
  Removed nodes flagged: R
  Synthesis page: wiki/synthesis/codebase-graph-report.md

Query the codebase with `/mnemo:query <term>`.
Run `/mnemo:lint` to verify knowledge base health.
```
