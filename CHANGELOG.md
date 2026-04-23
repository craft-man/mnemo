# Changelog

All notable changes to mnemo are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.1.0] — 2026-04-23

Initial public release — marketplace distribution.

### Added

- **Slash command descriptors** (`commands/mnemo/`) for Claude Code marketplace: `init`, `schema`, `ingest`, `query`, `save`, `lint`, `stats`
- **`scripts/init_mnemo.py`** — Python stdlib bootstrap script; interactive two-tier (local + global) setup
- **`CONTRIBUTING.md`** — contributor guide
- **`tests/test_init_mnemo.py`** — unit tests for the init script
- CLAUDE.md auto-wiring step in `/mnemo:init` skill
- Marketplace metadata in `plugin.json`: `repository`, `keywords`, `category`
- Quick start section in README with marketplace install path

### Changed

- Version set to `0.1.0` across `plugin.json` and all skill descriptors
- README rewritten for marketplace audience

---

## [0.0.1] — 2026-04-23

Internal bootstrap — initial commit of existing plugin files.

### Added

- Core skills: `init`, `schema`, `ingest`, `query`, `save`, `lint`, `stats`
- Reference docs: `ingest-workflow.md`, `scaling-playbook.md`, `page-conventions.md`, `agent-memory-integration.md`
- Utility scripts: `wiki_search.py`, `wiki_lint.py`, `wiki_stats.py`
- `CLAUDE.md` agent constitution
- `.claude-plugin/plugin.json` plugin manifest
- `.gitignore`
