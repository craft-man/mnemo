# Changelog

All notable changes to mnemo are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow [Semantic Versioning](https://semver.org/).

---

## [0.16.5] — 2026-04-29

### Added

- **End-to-end init regression coverage** — expanded init tests for default qmd and graphify execution, minimal `main()` answers, automatic agent memory wiring, and forbidden manual handoff messaging.

### Changed

- **Init now completes setup before returning** — `/mnemo:init` now treats schema, onboarding, qmd, graphify, Obsidian guidance, session brief generation, and agent memory wiring as one integrated run.
- **Manual handoffs removed from init messaging** — qmd and graphify use yes-default prompts with automatic install attempts, falling back cleanly without asking the user to install or run follow-up commands manually.

---

## [0.16.4] — 2026-04-29

### Added

- **Init completion regression coverage** — expanded `tests/test_init_mnemo.py` to cover the fast-path completion message and the non-interactive handling of an existing global user profile.

### Changed

- **Existing onboard profile is now kept silently during init** — the standalone `/mnemo:init` fast path no longer pauses to ask whether an already-present `~/.mnemo/wiki/entities/person-user.md` should be reviewed.
- **Bootstrap follow-up messaging now matches the real flow** — the fast path no longer suggests `/mnemo:schema` as a next step after schema setup already ran during init, and instead points directly to `raw/`, `/mnemo:ingest`, and `/mnemo:query`.

---

## [0.16.3] — 2026-04-29

### Added

- **Init schema regression coverage** — expanded `tests/test_init_mnemo.py` to cover the required schema pass in the fast-path bootstrap flow.

### Changed

- **Schema setup is now mandatory during init** — `/mnemo:init` no longer frames domain taxonomy setup as an optional follow-up. The bootstrap now always runs a schema pass and falls back to starter defaults only when fields are left blank.
- **Init skill and script alignment** — the host-level `skills/init/SKILL.md` and the standalone Python fast path now match on this behavior, removing the contradiction that suggested `SCHEMA.md` refinement could be skipped.

---

## [0.16.2] — 2026-04-29

### Added

- **Init wiring regression tests** — added coverage for the fast-path `/mnemo:init` flow when `CLAUDE.md` already exists and when no agent memory file exists yet.

### Changed

- **Fast-path agent memory wiring restored** — the standalone `/mnemo:init` bootstrap now resumes the host-aware steps after filesystem setup, wiring mnemo into `CLAUDE.md` or `AGENTS.md` instead of stopping early.
- **Claude stop hook restoration** — when the fast path wires `CLAUDE.md`, it now also restores `.claude/settings.local.json` with the `/mnemo:mine` session-end reminder if it is missing.

---

## [0.16.1] — 2026-04-29

### Added

- **Regression coverage for releases** — added tests for `scripts/bump_version.py` to verify both plugin manifests are updated together and to fail fast when their versions drift.

### Changed

- **Version bump consistency** — `scripts/bump_version.py` now updates both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` during a release bump.
- **Manifest sync guard** — the release script now aborts if the Claude and Codex plugin manifests start from different versions, preventing silent drift.
- **Codex plugin manifest** — aligned `.codex-plugin/plugin.json` with the current project versioning flow.

---

## [0.16.0] — 2026-04-29

### Added

- **Automatic init installs** — the standalone `/mnemo:init` fast path now attempts to install `@tobilu/qmd` and `graphify` automatically when those optional integrations are enabled but missing.

### Changed

- **Codex-friendly setup flow** — qmd and graphify setup no longer depends on the user manually completing installs outside the init flow before configuration can continue.

---

## [0.15.0] — 2026-04-29

### Added

- **Codex plugin metadata** — added a Codex plugin manifest and repo-local marketplace entry so mnemo can be exposed in Codex plugin catalogs.

---

## [0.14.0] — 2026-04-28

### Added

- **Manual startup context** — added `/mnemo:context` and `scripts/show_session_brief.py` to load the compact mnemo context manually when an agent does not auto-load project instructions before the first prompt.
- **Session brief generation** — added `scripts/update_session_brief.py` plus init integration so each vault can maintain a compact `SESSION_BRIEF.md` startup summary.
- **Public CLI wrappers** — added root-level wrappers for init and stats so deterministic workflows can be used outside a skill runtime.
- **Copilot fallback wiring** — added best-effort Copilot/local instructions that point agents at the session brief without promising automatic loading.

### Changed

- **Startup context model** — updated agent memory guidance to read `SESSION_BRIEF.md` first, load `graphify-out/GRAPH_REPORT.md` only for code-structure tasks, and avoid loading the whole wiki at startup.
- **Scaling guidance** — expanded stats and scaling checks for qmd recommendations, oversized pages, and index growth.

---

## [0.13.0] — 2026-04-28

### Added

- **`/mnemo:init` fast path schema setup** — the standalone Python init now offers to define the project domain taxonomy during initialization and writes a customized `.mnemo/<project-name>/SCHEMA.md` instead of only creating the starter template.
- **`/mnemo:init` fast path onboard setup** — the Python init now ensures the global user profile tier exists and creates or reviews `~/.mnemo/wiki/entities/person-user.md`, matching the core init skill's onboard step.

### Changed

- **`/mnemo:init` fast path defaults** — qmd semantic search and graphify codebase mapping now default to yes (`[Y/n]`) in the Python init script.
- **`/mnemo:init` graphify integration** — the Python init no longer stops at `graphify .`; it prepares `.graphifyignore`, validates `graphify-out/`, writes the codebase graph report/status synthesis pages, updates the index, and appends the graphify log entry.
- **Init structure parity** — the Python init now creates `wiki/activity/` and preserves existing global tier files when onboarding runs against an existing `~/.mnemo/`.
- **Test portability** — init tests now import the self-contained script from `skills/init/`, and lint tests import `wiki_lint.py` from `skills/lint/`, matching the refactored skill layout.

---

## [0.12.0] — 2026-04-28

### Changed

- **`/mnemo:init` behavior** — made agent memory wiring tool-agnostic and changed session-start guidance to read the global user profile plus `graphify-out/GRAPH_REPORT.md` when present, while keeping the local project vault at `.mnemo/<project-name>/`.
- **`/mnemo:graphify` behavior** — redefined `graphify-out/` as the canonical runtime owned by graphify. The skill now keeps `GRAPH_REPORT.md`, `graph.json`, and `cache/` in place, writes only lightweight synthesis/status pages into `.mnemo/<project-name>/wiki/synthesis/`, and no longer converts graph nodes into mnemo entity/concept pages or copies `graph.json` into the local vault.
- **Documentation alignment** — updated `README.md`, `CLAUDE.md`, and `CONTRIBUTING.md` to reflect the retained `.mnemo/<project-name>/` layout, tool-agnostic init wiring, and graphify's new role as the codebase runtime rather than a page-expansion pipeline.

---

## [0.11.0] — 2026-04-27

### Added

- **Portable dispatch contract** — Added `skills/references/subagent-dispatch.md` as the canonical cross-host contract for heavy workflows (`ingest`, `query`, `lint`). It defines explicit workflow inputs, reasoning hints, prompt assembly, and mandatory inline fallback semantics.
- **Host dispatch adapters** — Added `skills/dispatch/claude-code.md`, `codex.md`, `cursor.md`, `gemini.md`, `opencode.md`, and `inline.md` to separate workflow transport from workflow semantics and document host-specific delegation behavior.
- **Compatibility matrix** — README now includes a host-by-host matrix covering memory file, invocation mode, heavy workflow execution path, and current integration notes for Claude Code, Codex, Cursor, OpenCode, Gemini CLI, and generic agentskills.io hosts.

### Changed

- **Heavy workflow portability** — `skills/ingest/SKILL.md`, `skills/query/SKILL.md`, and `skills/lint/SKILL.md` no longer hardcode a Claude-specific Agent tool dispatch. They now route through the portable dispatch contract and explicitly fall back to inline execution when no reliable native delegation exists.
- **Workflow metadata** — `agents/ingestor.md`, `agents/archivist.md`, and `agents/linter.md` now use `reasoning-profile: heavy|balanced` instead of vendor-specific model labels, keeping workflow intent while removing provider coupling.
- **Contributor guidance** — `CONTRIBUTING.md` now documents portable workflow specs, dispatch adapters, and the requirement that heavy workflows remain valid both under native delegation and inline fallback.
- **Version bump workflow** — `scripts/bump_version.py` no longer commits by default. It now prepares the version bump and changelog placeholder first, with commit/tag behavior moved behind explicit `--commit` and `--tag` flags so release notes can be filled in before the release commit.

---

## [0.10.0] — 2026-04-27

### Changed

- **Refactor: Encapsulation of proprietary scripts** — Moved module-specific Python scripts (`init_mnemo.py`, `wiki_lint.py`, `wiki_stats.py`) from the global `scripts/` directory to their respective skill directories (`skills/init/`, `skills/lint/`, `skills/stats/`). This enhances portability and modularity, ensuring that skills are self-contained and easier to use with external agents like Cursor or Codex.
- **Standardized references** — Updated all `SKILL.md` files to use root-relative paths (e.g., `skills/init/init_mnemo.py`) for maximum compatibility across all AI agent environments.

---

## [0.9.0] — 2026-04-27

### Added

- **`scripts/update_log.py`** — fast path script for deterministic log writes. Appends 3-column entries (`file | timestamp | op`) to `log.md`; special `lint` op updates the `# Last lint:` header. Validates `--file` against pipe and newline injection.
- **`scripts/update_index.py`** — fast path script for index regeneration. Rebuilds `index.md` from YAML frontmatter of every wiki page; shards into `wiki/indexes/<category>.md` when page count exceeds 150. Supports `--dry-run` and `--json`. Category whitelisted against path traversal.
- **Fast path Step 0** added to `/mnemo:init`, `/mnemo:save`, `agents/ingestor.md`, `agents/linter.md`. Each fast path: tries the Python script → exit 0 skips LLM → exit non-zero emits non-blocking warning and falls back to LLM → script not found falls back to LLM.

### Changed

- **Log entry format** unified to 3 columns: `- file | ISO timestamp | op` (was 2-column in CLAUDE.md — now consistent across scripts, agents, and convention docs).
- **`scripts/wiki_lint.py`** log reader updated to parse 3-column format; adds raw paths to `processed` set only for `op == ingest`.
- **`CLAUDE.md`** naming conventions updated: log entry and index entry formats reflect enriched output (with summary and date).
- **`skills/init/SKILL.md`** prose steps renumbered 1-N to avoid collision with the new `## Step 0` fast path heading.

---

## [0.8.0] — 2026-04-26

### Added

- **`/mnemo:log`** — new inline skill to query `log.md` in natural language. Displays `ingest`, `skipped`, `generated`, and `lint` entries as a markdown table sorted newest first. Supports three filters: operation type (`ingest`, `skipped`, `generated`, `lint`), date range (`since YYYY-MM-DD`, `since Monday`, `yesterday`), and recency (`last N`). Read-only — never writes to `log.md`.
- **`scripts/bump_version.py`** — atomic version bump script. Updates `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, the README badge, all `skills/*/SKILL.md` frontmatter, and `CHANGELOG.md` in a single commit. Supports `--tag` (creates `vX.Y.Z`) and `--push` (pushes the tag to origin).

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
