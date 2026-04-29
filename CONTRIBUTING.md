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
│   │   ├── scripts/       ← non-interactive init helpers
│   │   ├── claude-code.md ← host-specific memory/hook notes
│   │   ├── opencode.md    ← host-specific memory notes
│   │   ├── gemini.md      ← host-specific memory notes
│   │   ├── cursor.md      ← host-specific memory notes
│   │   └── codex.md       ← host-specific memory notes
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
│   ├── update_log.py      ← fast path: append entries to log.md
│   ├── update_index.py    ← fast path: regenerate index.md from frontmatter
│   └── check_skill_invocations.sh  ← CI guard: no slash-command syntax in SKILL.md
├── tests/
│   ├── test_init_scripts.py
│   ├── test_update_index.py
│   ├── test_update_log.py
│   └── test_wiki_lint.py
└── CLAUDE.md              ← agent constitution (loaded in every session)
```

## Fast path pattern

Skills and agents invoke Python scripts for deterministic filesystem work. The pattern:

```
Fast path: use the skill-owned `scripts/<script>.py` first, then shared `scripts/<script>.py` only for repository-wide helpers.
If found, run: `python3 <script_path> --vault <vault> [args]`
If exit 0 → skip LLM steps.
If exit non-zero → emit `⚠ fast path failed (exit <code>); falling back to LLM.` and continue.
If script not found → apply LLM fallback.
```

**Rules for adding a new fast path script:**
- Stdlib only; no external dependencies
- Non-interactive: all choices are collected by the skill before the script runs
- Support `--help`
- Write JSON to stdout and diagnostics/errors to stderr
- Exit 0 = success, exit 1 = error (print to stderr)
- Must have a corresponding test file in `tests/test_<script_name>.py`
- Follow naming convention: `verb_noun.py` (e.g. `update_log.py`, `update_index.py`)
- Test with `python -m pytest tests/test_<script_name>.py -v` before opening a PR

## PRs welcome

Edit a `SKILL.md`, test with `claude --plugin-dir ./mnemo` (use `/reload-plugins` to pick up changes), run `python -m pytest tests/ -v`, open a PR.

## Adding support for a new agent

mnemo now prefers tool-agnostic project memory wiring:

1. Detect whether the host auto-loads a project-level memory/instructions file across sessions.
2. Teach `skills/init/SKILL.md` how to prefer that file over best-effort fallbacks.
3. If the host also supports local stop hooks or session-end reminders, document the integration pattern clearly.
4. Add host-specific notes in `skills/init/<agent-name>.md` and `skills/references/agent-memory-integration.md` only when the host needs special handling beyond the generic resolution logic.

The core skill should not promise persistence when host auto-loading support cannot be confirmed. Run `bash scripts/check_skill_invocations.sh` before opening a PR to verify no slash-command syntax leaked in.

## Adding or modifying agents

Agents in `agents/*.md` are self-contained workflow specs. They must be
portable: a host may execute them through native sub-agent delegation or inline
through the main agent via the dispatch adapters.

**Required file structure:**

```markdown
---
name: mnemo-<role>
description: >
  One sentence about what the agent does and when it is dispatched.
reasoning-profile: heavy   # or balanced, depending on workload
allowed-tools: Read Write Edit Grep Glob Bash
---

## Inputs

- `vault`: vault path
- <other inputs passed by the parent skill>

---

## Step 1: ...
## Step N: Report
```

**Conventions:**
- Use `reasoning-profile: heavy` for heavy workflows (full ingest, lint, graph analytics)
- Use `reasoning-profile: balanced` for reading/synthesis workflows (query, save)
- Each agent is self-contained; do not import or reference the parent `SKILL.md`
- Inputs are explicitly listed in the `## Inputs` section of the dispatch prompt
- End with a Report step that summarizes the actions performed
- The workflow must remain valid for both native delegation and inline fallback

**Parent skill update:**
When you add or modify an agent, verify that Step 0 in the corresponding
`SKILL.md` passes all required inputs to the agent through the contract defined
in `skills/references/subagent-dispatch.md`.

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

**Versioning:**
Agent files do not carry individual versions. The plugin version (`0.x.y`)
covers the full skills + agents set.

## Skill authoring tips

- Write explicit stop conditions. Agents follow instructions literally, and vague wording leads to over-eager behaviour, like ingesting files twice.
- Put guard clauses first. Steps execute top to bottom.
- One action per step. It keeps retry logic predictable.
- Write edge cases in prose: what should the agent do when a file is missing, already processed, or oversized?

## Testing init scripts

```bash
python -m pytest tests/test_init_scripts.py -v
```

Tests cover the small non-interactive scripts used by `mnemo-init`.

## Running Agent Skills evals

Skill eval cases live in `skills/<skill>/evals/evals.json` using the official Agent Skills shape:

```json
{
  "skill_name": "mnemo-init",
  "evals": [
    {
      "id": "fresh-project-complete-init",
      "prompt": "Initialize mnemo in this project...",
      "expected_output": "A complete mnemo project init is performed...",
      "assertions": ["The output reports a vault at `.mnemo/<project-name>/`."]
    }
  ]
}
```

Required path: always use the official `skill-creator` skill to run skill evals end-to-end. If `skill-creator` is not available in the current agent environment, install it first through the agent's skill installer, then restart the eval flow with `skill-creator` loaded. `skill-creator` owns the full loop: spawning with-skill and baseline runs, grading assertions, aggregating benchmarks, and presenting results for human review.

When asking an agent to run evals end-to-end, the expected orchestration is:

1. Load `skill-creator`; if unavailable, install it first through the agent's skill installer.
2. Let `skill-creator` orchestrate the eval run.
3. Execute each `with_skill` and baseline run in isolated agent contexts, using sub-agents or separate sessions when available.
4. Grade each run into its local `grading.json`.
5. Record `timing.json` when available.
6. Aggregate the benchmark.
7. Report the benchmark and the concrete failures that should drive the next skill edit.

## Versioning

mnemo follows [Semantic Versioning](https://semver.org/). The version lives in five places:
- `.claude-plugin/plugin.json` → `"version"`
- `.codex-plugin/plugin.json` → `"version"`
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

MIT. Contributions are accepted under the same license.
