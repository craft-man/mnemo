# Contributing to mnemo

## How it works

Each skill is a plain Markdown file (`SKILL.md`) with instructions the agent follows at runtime. The agent reads it, interprets the steps, and runs them using its built-in tools (`Read`, `Write`, `Glob`, `Grep`). No server, no binary, no dependencies.

```
mnemo/
├── .claude-plugin/
│   └── plugin.json        ← Claude Code marketplace manifest
├── agents/                ← sub-agents dispatché par les skills lourds
│   ├── ingestor.md        ← Opus — ingest complet + discuss before write
│   ├── archivist.md       ← Sonnet — query + format adaptatif + file back
│   └── linter.md          ← Opus — lint 3 passes + graph analytics
├── commands/mnemo/        ← slash-command stubs (one .md per skill)
├── skills/
│   ├── init/
│   │   ├── SKILL.md       ← universal core
│   │   ├── claude-code.md ← Claude Code extension (CLAUDE.md + Stop hook)
│   │   ├── opencode.md    ← OpenCode extension (AGENTS.md stanza)
│   │   ├── gemini.md      ← Gemini CLI extension (GEMINI.md stanza)
│   │   ├── cursor.md      ← Cursor extension (AGENTS.md stanza)
│   │   └── codex.md       ← Codex extension (AGENTS.md stanza)
│   ├── onboard/SKILL.md
│   ├── schema/SKILL.md
│   ├── ingest/SKILL.md    ← Step 0 dispatch → agents/ingestor.md
│   ├── query/SKILL.md     ← Step 0 dispatch → agents/archivist.md
│   ├── lint/SKILL.md      ← Step 0 dispatch → agents/linter.md
│   ├── save/SKILL.md
│   ├── mine/SKILL.md
│   ├── graphify/SKILL.md
│   ├── stats/SKILL.md
│   └── references/        ← contributor and integration docs
├── scripts/
│   ├── init_mnemo.py      ← standalone bootstrap (no agent required)
│   └── check_skill_invocations.sh  ← CI guard: no slash-command syntax in SKILL.md
├── tests/
│   └── test_init_mnemo.py
└── CLAUDE.md              ← agent constitution (loaded in every session)
```

## PRs welcome

Edit a `SKILL.md`, test with `claude --plugin-dir ./mnemo` (use `/reload-plugins` to pick up changes), run `python -m pytest tests/ -v`, open a PR.

## Adding support for a new agent

Each agent gets one extension file alongside the core skill. The core (`skills/init/SKILL.md`) auto-delegates to it in step 11.

1. Create `skills/init/<agent-name>.md` (e.g. `skills/init/copilot.md`)
2. Follow the structure of an existing extension — frontmatter, user prompt, idempotency check, append stanza, confirm
3. Add your file to the `Known extension files` list in `skills/init/SKILL.md` step 11
4. Add the memory stanza format to `skills/references/agent-memory-integration.md` if it uses a new config file format

No changes to the core skill needed. Run `bash scripts/check_skill_invocations.sh` before opening a PR to verify no slash-command syntax leaked in.

## Adding or modifying agents

Les agents (`agents/*.md`) sont des specs self-contained lus par l'outil Agent de Claude Code. Ils ne dépendent d'aucun autre fichier à l'exécution.

**Structure de fichier obligatoire :**

```markdown
---
name: mnemo-<role>
description: >
  Une phrase sur ce que fait l'agent et quand il est dispatché.
model: opus   # ou sonnet selon la charge
allowed-tools: Read Write Edit Grep Glob Bash
---

## Inputs

- `vault`: chemin du vault
- <autres inputs transmis par le skill parent>

---

## Step 1 — ...
## Step N — Report
```

**Conventions :**
- `model: opus` pour les workflows lourds (ingest complet, lint, graph analytics)
- `model: sonnet` pour les workflows de lecture/synthèse (query, save)
- Chaque agent est self-contained — ne pas importer ni référencer le SKILL.md parent
- Les inputs sont explicitement listés dans la section `## Inputs` du prompt de dispatch
- Terminer par un step Report qui résume les actions effectuées

**Mise à jour du skill parent :**
Quand tu ajoutes ou modifies un agent, vérifier que le Step 0 dans le SKILL.md correspondant transmet bien tous les inputs nécessaires à l'agent.

**Versioning :**
Les fichiers agents ne portent pas de version individuelle. La version du plugin (`0.x.y`) couvre l'ensemble skills + agents.

## Skill authoring tips

- Write explicit stop conditions. Agents follow instructions literally — vague wording leads to over-eager behaviour, like ingesting files twice.
- Put guard clauses first. Steps execute top to bottom.
- One action per step. It keeps retry logic predictable.
- Write edge cases in prose: what should the agent do when a file is missing, already processed, or oversized?

## Testing the Python bootstrap

```bash
python -m pytest tests/ -v
```

Tests cover `create_structure`, `guard`, `prompt_qmd`, `update_gitignore`, and the full `main()` flow for all three init choices.

## Versioning

mnemo follows [Semantic Versioning](https://semver.org/). The version lives in four places:
- `.claude-plugin/plugin.json` → `"version"`
- `README.md` → version badge
- All `skills/*/SKILL.md` → `version:` frontmatter field
- `CHANGELOG.md` → new section header

Update all four when bumping. Agent extension files (`skills/init/*.md` other than `SKILL.md`) and agent files (`agents/*.md`) do not carry individual version numbers.

## License

MIT — contributions are accepted under the same license.
