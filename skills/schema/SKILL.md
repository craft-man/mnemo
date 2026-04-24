---
name: schema
description: >
  Interactively create or revise .mnemo/SCHEMA.md — the domain taxonomy that
  guides ingest categorization. If raw/ files are present, infers entity types
  and concept categories from their content before asking questions. Use when the
  user says "define my schema", "set up my taxonomy", "what entity types should I
  use", "update my schema", "my domain has changed", or right after /mnemo:init.
license: MIT
compatibility: >
  Claude Code (slash command /mnemo:schema). Other agentskills.io-compatible
  agents invoke by natural language. No external dependencies.
metadata:
  author: mnemo contributors
  version: "0.2.0"
allowed-tools: Read Write Glob Grep
---

Arguments: $ARGUMENTS

Create or revise `.mnemo/SCHEMA.md` for this project's domain.

## Steps

**1. Check init** — if `.mnemo/` does not exist, stop:
> "Knowledge base not initialized. Run `/mnemo:init` first."

**2. Check for existing SCHEMA.md** — read `.mnemo/SCHEMA.md` if it exists. If it contains domain content beyond the starter template (i.e. the `## Domain` section is filled in), inform the user:
> "A schema already exists. I'll show you the current version and propose updates."

Keep the existing content in context for the revision flow below.

**3. Scan raw/ for inference signals** — glob `.mnemo/raw/*`. If files are found:

Inform the user:
> "I found N file(s) in raw/. I'll read them to infer your domain before asking questions."

Read up to **5 files** (largest first by estimated relevance — prefer `.md`, `.txt`, `.pdf` over binary). For each file:
- If > 300 lines: read the first 150 lines only.
- Extract:
  - **Domain signals**: recurring technical nouns, proper nouns, field-specific vocabulary
  - **Entity candidates**: named things that appear repeatedly (tools, people, projects, systems, papers)
  - **Concept candidates**: abstract terms that recur (patterns, techniques, algorithms, problems, ideas)

Consolidate into:
- `inferred_domain`: a 1-sentence description of the subject matter
- `inferred_entity_types`: list of 3–6 entity type names with one-line descriptions
- `inferred_concept_categories`: list of 3–5 concept category names with one-line descriptions

If raw/ is empty or no files can be read, skip to step 4 with empty inferences.

**4. Present inferences and ask for confirmation** — show what was inferred (or nothing if raw/ was empty), then ask the user to validate and complete:

```
## Inferred from raw/ files

Domain: <inferred_domain or "not determined">

Entity types:
- <type>: <description>
- ...

Concept categories:
- <category>: <description>
- ...

Does this look right? Add, remove, or rename anything before I write the schema.
You can also describe your domain in plain language and I'll adjust.
```

Wait for the user's response. Incorporate corrections, additions, and removals.

**5. Ask for any missing pieces** — if after the user's response any of these are still unclear, ask them individually (one question at a time, not all at once):

- If domain is still empty: "In one sentence, what is this knowledge base about?"
- If fewer than 2 entity types: "What kinds of named things recur in your domain? (e.g. tools, people, papers, companies)"
- If fewer than 2 concept categories: "What kinds of abstract ideas or patterns recur? (e.g. algorithms, design patterns, failure modes)"

**6. Draft and preview** — compose the full SCHEMA.md and show it to the user before writing:

```markdown
# Knowledge Base Schema

## Domain
<domain description>

## Entity Types
<for each entity type>
- **<Type>** — <description>

## Concept Taxonomy
<for each concept category>
- **<Category>** — <description>

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md` (e.g. `<type>-<example>.md`)
- Concept pages: `wiki/concepts/<category>-<name>.md` (e.g. `<category>-<example>.md`)
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax — always the exact H1 title of the target page. Obsidian-compatible.
```

Ask: "Write this schema? [y]es / [e]dit"

If `[e]dit`: ask what to change, update the draft, show it again. Repeat until approved.

**7. Write `.mnemo/SCHEMA.md`** — on approval, write the file.

**8. Report:**
> "Schema written to `.mnemo/SCHEMA.md`.
> Entity types: <list>
> Concept categories: <list>
> Next: drop files into `.mnemo/raw/` and run `/mnemo:ingest` — the schema will guide categorization."

If ingest has already run (check `.mnemo/log.md` for existing entries), add:
> "Note: already-ingested pages used the previous schema. Run `/mnemo:ingest` on new files to apply the updated taxonomy."
