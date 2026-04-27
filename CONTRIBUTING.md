# Contributing to mnemo

## How it works

Each skill is a plain Markdown file (`SKILL.md`) with instructions the agent follows at runtime. The agent reads it, interprets the steps, and runs them using its built-in tools (`Read`, `Write`, `Glob`, `Grep`). No server, no binary, no dependencies.

```
mnemo/
├── .claude-plugin/
│   └── plugin.json        ← Claude Code marketplace manifest
├── agents/                ← portable workflow specs for heavy skills
│   ├── ingestor.md        ← heavy ingest workflow + discuss before write
│   ├── archivist.md       ← balanced query workflow + adaptive format + file back
│   └── linter.md          ← heavy lint workflow + graph analytics
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
│   ├── dispatch/          ← host adapters + inline fallback
│   ├── ingest/SKILL.md    ← orchestrates dispatch → agents/ingestor.md
│   ├── query/SKILL.md     ← orchestrates dispatch → agents/archivist.md
│   ├── lint/SKILL.md      ← orchestrates dispatch → agents/linter.md
│   ├── save/SKILL.md
│   ├── mine/SKILL.md
│   ├── graphify/SKILL.md
│   ├── stats/SKILL.md
│   └── references/        ← contributor and integration docs
├── scripts/
│   ├── init_mnemo.py      ← standalone bootstrap (no agent required)
│   ├── update_log.py      ← fast path: append entries to log.md
│   ├── update_index.py    ← fast path: regenerate index.md from frontmatter
│   └── check_skill_invocations.sh  ← CI guard: no slash-command syntax in SKILL.md
├── tests/
│   ├── test_init_mnemo.py
│   ├── test_update_index.py
│   ├── test_update_log.py
│   └── test_wiki_lint.py
└── CLAUDE.md              ← agent constitution (loaded in every session)
```

## Fast path pattern

Skills and agents invoke Python scripts as a "Step 0" before their LLM logic. The pattern:

```
Fast path: use `Glob('**/mnemo/scripts/<script>.py')` to locate the script.
If found, run: `python3 <script_path> --vault <vault> [args]`
If exit 0 → skip LLM steps.
If exit non-zero → emit `⚠ fast path failed (exit <code>) — falling back to LLM.` and continue.
If script not found → apply LLM fallback.
```

**Rules for adding a new fast path script:**
- Stdlib only — no external dependencies
- Exit 0 = success, exit 1 = error (print to stderr)
- Must have a corresponding test file in `tests/test_<script_name>.py`
- Follow naming convention: `verb_noun.py` (e.g. `update_log.py`, `update_index.py`)
- Test with `python -m pytest tests/test_<script_name>.py -v` before opening a PR

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

Agents in `agents/*.md` are self-contained workflow specs. They must be
portable: a host may execute them through native sub-agent delegation or inline
through the main agent via the dispatch adapters.

**Structure de fichier obligatoire :**

```markdown
---
name: mnemo-<role>
description: >
  Une phrase sur ce que fait l'agent et quand il est dispatché.
reasoning-profile: heavy   # ou balanced selon la charge
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
- `reasoning-profile: heavy` pour les workflows lourds (ingest complet, lint, graph analytics)
- `reasoning-profile: balanced` pour les workflows de lecture/synthèse (query, save)
- Chaque agent est self-contained — ne pas importer ni référencer le SKILL.md parent
- Les inputs sont explicitement listés dans la section `## Inputs` du prompt de dispatch
- Terminer par un step Report qui résume les actions effectuées
- Le workflow doit rester valide en délégation native et en fallback inline

**Mise à jour du skill parent :**
Quand tu ajoutes ou modifies un agent, vérifier que le Step 0 dans le SKILL.md
correspondant transmet bien tous les inputs nécessaires à l'agent via le
contrat défini dans `skills/references/subagent-dispatch.md`.

## Adding or modifying dispatch adapters

Dispatch adapters live in `skills/dispatch/`.

Use one file per host plus the universal fallback:

- `claude-code.md`
- `codex.md`
- `cursor.md`
- `gemini.md`
- `opencode.md`
- `inline.md`

Rules:

- Prefer native delegation only when the host supports it clearly.
- Otherwise use the inline fallback.
- Treat reasoning hints as advisory only.
- Do not redefine workflow semantics in the adapter.

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

Use the bump script to update all four atomically, then fill in the release
notes and create your commit deliberately:

```bash
python3 scripts/bump_version.py 0.8.0                   # bump files + changelog placeholder
python3 scripts/bump_version.py 0.8.0 --commit          # bump + commit
python3 scripts/bump_version.py 0.8.0 --commit --tag    # bump + commit + git tag v0.8.0
python3 scripts/bump_version.py 0.8.0 --commit --tag --push  # also push the tag
```

The script inserts a placeholder section in `CHANGELOG.md`. Preferred flow:

1. Run the script without `--commit`
2. Fill in the release notes
3. Review the diff
4. Create the release commit manually

Use `--commit` only if you intentionally want the script to create the commit
for you. Agent extension files (`skills/init/*.md` other than `SKILL.md`) and
agent files (`agents/*.md`) do not carry individual version numbers.

## License

MIT — contributions are accepted under the same license.
