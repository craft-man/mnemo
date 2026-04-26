# Changelog

All notable changes to mnemo are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.9.0] — 2026-04-27

### Added

-

### Changed

-

---

## [0.8.0] — 2026-04-26

### Added

- **`/mnemo:log`** — new inline skill to query `log.md` in natural language. Displays `ingest`, `skipped`, `generated`, and `lint` entries as a markdown table sorted newest first. Supports three filters: operation type (`ingest`, `skipped`, `generated`, `lint`), date range (`since YYYY-MM-DD`, `since Monday`, `yesterday`), and recency (`last N`). Read-only — never writes to `log.md`.
- **`scripts/bump_version.py`** — atomic version bump script. Updates `.claude-plugin/plugin.json`, the README badge, all `skills/*/SKILL.md` frontmatter, and `CHANGELOG.md` in a single commit. Supports `--tag` (creates `vX.Y.Z`) and `--push` (pushes the tag to origin).

---

## [0.7.0] — 2026-04-25

### Added

- **Sub-agents** — les skills lourds (`ingest`, `query`, `lint`) dispatche désormais un agent dédié en contexte isolé, libérant le contexte principal pour la conversation.
- **`agents/ingestor.md`** (Opus) — workflow d'ingest complet avec une nouvelle phase *discuss before write* : l'agent propose TL;DR, pages prévues, et contradictions détectées, puis attend confirmation avant d'écrire. Annulation partielle possible ("skip les entités", "ignore X").
- **`agents/archivist.md`** (Sonnet) — workflow de query complet avec format adaptatif (tableau pour A vs B, timeline pour requêtes temporelles, explication pour définitions) et *offer to file back* systématique après chaque réponse substantielle.
- **`agents/linter.md`** (Opus) — workflow de lint complet avec une nouvelle Pass 2 graphe intégrant les métriques de `/mnemo:graphify` (hubs, sinks, composantes connexes, densité) directement dans le rapport de lint.

### Changed

- **`skills/ingest/SKILL.md`**, **`skills/query/SKILL.md`**, **`skills/lint/SKILL.md`** — réduits à un Step 0 de dispatch. Les workflows complets ont migré dans les fichiers agents correspondants. Comportement externe inchangé.

---

## [0.6.0] — 2026-04-24

### Added

- **Multi-agent support** — mnemo skills now run on Claude Code, OpenCode, Gemini CLI, Cursor, Codex, and any agentskills.io-compatible agent. Agent-specific wiring (CLAUDE.md stanza, Stop hook) is extracted into extension files loaded automatically at the end of `/mnemo:init`.
- **`skills/init/claude-code.md`** — Claude Code extension: CLAUDE.md stanza + Stop hook injection (identical behavior to previous versions).
- **`skills/init/opencode.md`** — OpenCode extension: AGENTS.md stanza.
- **`skills/init/gemini.md`** — Gemini CLI extension: GEMINI.md stanza.
- **`skills/init/cursor.md`** — Cursor extension: AGENTS.md stanza.
- **`skills/init/codex.md`** — Codex extension: AGENTS.md stanza.
- **Extension contributor guide** — `skills/references/agent-memory-integration.md` now documents how to add support for new agents by creating a single extension file.
- **`scripts/check_skill_invocations.sh`** — CI guard that verifies no slash-command invocation syntax remains in any `SKILL.md`.

### Changed

- **`skills/init/SKILL.md`** renamed from `init` to `mnemo-init` to avoid collisions with built-in agent commands.
- Sub-skill invocations in `init`, `mine`, and `lint` converted from slash-command syntax (`/mnemo:schema`) to natural-language delegation (`read skills/schema/SKILL.md and follow its instructions`) — compatible with all agents.

---

## [0.5.1] — 2026-04-24

### Changed

- **Project-name vault level** — the local knowledge base now lives at `.mnemo/<project-name>/` instead of `.mnemo/`. Opening `.mnemo/<project-name>/` as an Obsidian vault now displays the project name rather than `.mnemo`. The global vault (`~/.mnemo/`) is unchanged. All skills, `scripts/init_mnemo.py`, and CLAUDE.md updated accordingly. Existing installs are unaffected (new structure applies only to fresh `/mnemo:init` runs).

---

## [0.5.0] — 2026-04-24

### Added

- **`/mnemo:query` progressive disclosure** — results now show as a compact numbered index (title + category + snippet). Type a result number to expand to full page content. Works in any language.
- **`/mnemo:query` activity intent detection** — temporal and procedural queries (e.g. "what did we do yesterday", "qu'est-ce qu'on a fait cette semaine") automatically include session logs from `wiki/activity/` in results. Multilingual signal detection (FR, EN, DE, IT, ES, JA, ZH, RU).
- **`/mnemo:mine` session capture** — after saving items, offers to write a session activity log to `wiki/activity/YYYY-MM-DD.md`. Append-safe on same-day re-runs.
- **`/mnemo:init` Stop hook injection** — automatically wires a session-end reminder hook into the host project's `.claude/settings.local.json` (creates the file if needed, merges safely if it exists).
- **`activity/` category** — new wiki subdirectory for session logs, excluded from default search, included automatically when query detects activity intent.
- **Session End Protocol in CLAUDE.md** — agent now proactively proposes `/mnemo:mine` at end of write-worthy sessions.

---

## [0.4.2] — 2026-04-24

### Added

- **`/mnemo:init` step 10** — optional Obsidian setup: proposes opening `.mnemo/` as a vault and installing the Web Clipper (https://obsidian.md/clipper#more-browsers) with `raw/` as the default save location so clipped pages feed directly into `/mnemo:ingest`.

---

## [0.4.1] — 2026-04-24

### Changed

- **`/mnemo:onboard` interview** — replaced Q5 (knowledge base goal) and Q6 (response style) with **Proactivity** (`High` / `Moderate` / `Low`) and **Register** (`Direct` / `Collaborative`). Both questions drive observable behavior in query and session responses. Added interview language note (interview in user's language, values stored in English, Q4 domains normalized). Added migration handling for profiles created before this version.

---

## [0.4.0] — 2026-04-24

### Added

- **`/mnemo:onboard`** — new skill that creates or updates a global user profile at `~/.mnemo/wiki/entities/person-user.md`. Conducts a short interview (role, technical level, language, domains, goal, response style) and saves answers as a structured wiki entity. Auto-detects whether a profile already exists: runs the full interview if absent, skips silently if present. Invoked automatically during `/mnemo:init` (placed right after schema setup, before the technical configuration steps).

### Changed

- **`/mnemo:init` step order** — user profile (onboard) now runs as step 5, immediately after schema setup (step 4), grouping the two context-setting questions together before technical configuration (semantic search, CLAUDE.md wiring, graphify).

---

## [0.3.0] — 2026-04-24

### Added

- **`/mnemo:graphify`** — new skill that maps the current project codebase into a queryable knowledge graph using [graphify](https://github.com/safishamsi/graphify). Converts `graph.json` directly into mnemo wiki pages (entities, concepts, synthesis report) with full frontmatter and wikilinks. Re-runs are incremental — only nodes whose description or edges changed are updated. Persists `graph.json` to `.mnemo/graph.json` as the baseline for future diffs.

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
