# Contributing to mnemo

## How it works

Each skill is a plain Markdown file (`SKILL.md`) containing instructions the agent follows at runtime. The agent reads the file, interprets the steps, and executes them using its built-in tools (`Read`, `Write`, `Glob`, `Grep`). No server, no binary, no dependencies.

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

- **Be explicit about stop conditions.** Agents follow instructions literally — ambiguous wording leads to over-eager behaviour (e.g. ingesting files twice).
- **Order matters.** Steps execute top to bottom; put guard clauses first.
- **Keep steps atomic.** One action per step makes retry logic predictable.
- **Test edge cases in prose.** Write what the agent should do when a file is missing, already processed, or oversized — not just the happy path.

## Testing the Python bootstrap

```bash
python -m pytest tests/ -v
```

Tests cover `create_structure`, `guard`, `prompt_qmd`, `update_gitignore`, and the full `main()` flow for all three init choices.

## Versioning

mnemo follows [Semantic Versioning](https://semver.org/). The version appears in:
- `.claude-plugin/plugin.json` → `"version"`
- `README.md` → version badge
- All `skills/*/SKILL.md` → `version:` frontmatter field

Update all three when bumping.

## License

MIT — contributions are accepted under the same license.
