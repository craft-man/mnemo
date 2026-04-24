# Contributing to mnemo

## How it works

Each skill is a plain Markdown file (`SKILL.md`) with instructions the agent follows at runtime. The agent reads it, interprets the steps, and runs them using its built-in tools (`Read`, `Write`, `Glob`, `Grep`). No server, no binary, no dependencies.

```
mnemo/
├── .claude-plugin/
│   └── plugin.json        ← Claude Code marketplace manifest
├── commands/mnemo/        ← slash-command stubs (one .md per skill)
├── skills/
│   ├── init/SKILL.md
│   ├── schema/SKILL.md
│   ├── ingest/SKILL.md
│   ├── query/SKILL.md
│   ├── lint/SKILL.md
│   ├── save/SKILL.md
│   ├── mine/SKILL.md
│   ├── graphify/SKILL.md
│   └── stats/SKILL.md
├── scripts/
│   └── init_mnemo.py      ← standalone bootstrap (no agent required)
├── tests/
│   └── test_init_mnemo.py
└── CLAUDE.md              ← agent constitution (loaded in every session)
```

## PRs welcome

Edit a `SKILL.md`, test with `claude --plugin-dir ./mnemo` (use `/reload-plugins` to pick up changes), run `python -m pytest tests/ -v`, open a PR.

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

mnemo follows [Semantic Versioning](https://semver.org/). The version lives in three places:
- `.claude-plugin/plugin.json` → `"version"`
- `README.md` → version badge
- All `skills/*/SKILL.md` → `version:` frontmatter field

Update all three when bumping.

## License

MIT — contributions are accepted under the same license.
