# Changelog

All notable changes to mnemo are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2026-04-24

### Added

- **`/mnemo:mine`** — new skill that scans the current session for knowledge worth persisting (decisions, entities, concepts, conclusions). Presents a numbered candidate list; approved items route to `/mnemo:save`. Triggered explicitly or by intent expressed in any language.
- **Temporal validity tracking** — optional `superseded_by:` and `supersedes:` frontmatter fields on entity/concept pages, plus a `## History` section format for recording replacement events (see `skills/references/page-conventions.md`)
- **`[h]istory` option in ingest contradiction detection** — when a contradiction involves replacement language, `/mnemo:ingest` now offers `[h]istory` in addition to `[u]pdate / [k]eep both / [s]kip`. Choosing it writes `superseded_by:` to the old page, adds a `## History` entry, and adds `supersedes:` to the new page
- **`superseded_without_history` lint check** — `/mnemo:lint` and `scripts/wiki_lint.py` now flag entity/concept pages with `superseded_by:` or `supersedes:` in frontmatter but no `## History` section
- **`skills/references/backends.md`** — reference document for the search backend interface, built-in backends, and custom backend integration guide
- **`tests/test_wiki_lint.py`** — unit tests for the new lint check and temporal frontmatter field parsing

### Changed

- **Search backend config key** renamed from `semantic_search` to `search_backend` in `config.json`. Old `semantic_search` configs remain supported as a fallback — no migration required.
- **`/mnemo:query` Step 0** now reads `search_backend` first, falls back to `semantic_search`, and warns on unknown backend names instead of silently defaulting
- **qmd collection name** is now read from `config.json` (`qmd_collection` field, default `"mnemo-wiki"`) rather than hardcoded in the query and ingest skills
- **`/mnemo:mine` trigger patterns** are language-agnostic — the skill recognizes intent regardless of conversation language rather than matching a fixed list of phrases

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
