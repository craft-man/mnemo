#!/usr/bin/env python3
"""Bootstrap a mnemo knowledge base. Python 3.10+ stdlib only.

Usage:
  python scripts/init_mnemo.py              # current directory
  python scripts/init_mnemo.py ./my-project # specific directory
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone

DIRS = [
    "raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/synthesis",
    "wiki/activity",
    "wiki/indexes",
]

INDEX_TEMPLATE = """\
# Index

## Sources

## Entities

## Concepts

## Synthesis
"""

LOG_TEMPLATE = "# Log\n"

SCHEMA_TEMPLATE = """\
# Knowledge Base Schema

> Edit this file to define domain-specific conventions.

## Domain
<!-- Describe the subject matter (e.g. "distributed systems", "my research") -->

## Entity Types
- **Person** — researchers, authors, contributors
- **Tool** — software, libraries, frameworks
- **Project** — codebases, products, initiatives
- **System** — infrastructure, platforms

## Concept Taxonomy
- **Pattern** — reusable design or architectural pattern
- **Technique** — method or approach
- **Problem** — known failure mode or challenge
- **Idea** — hypothesis, insight, observation

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md` (e.g. `tool-redis.md`)
- Concept pages: `wiki/concepts/<category>-<name>.md` (e.g. `pattern-saga.md`)
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax — always the exact H1 title of the target page.
"""


def create_structure(root: pathlib.Path, overwrite: bool = True) -> None:
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    files = {
        "index.md": INDEX_TEMPLATE,
        "log.md": LOG_TEMPLATE,
        "SCHEMA.md": SCHEMA_TEMPLATE,
    }
    for name, template in files.items():
        path = root / name
        if overwrite or not path.exists():
            path.write_text(template, encoding="utf-8")


def update_session_brief(mnemo_root: pathlib.Path) -> None:
    script = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "update_session_brief.py"
    if not script.exists():
        return
    result = subprocess.run([sys.executable, str(script), "--vault", str(mnemo_root)])
    if result.returncode != 0:
        print("  SESSION_BRIEF.md was not updated; init continues without a refreshed brief.")


def ensure_global_tier() -> pathlib.Path:
    global_root = pathlib.Path.home() / ".mnemo"
    create_structure(global_root, overwrite=False)
    return global_root


def guard(target: pathlib.Path) -> bool:
    project_name = target.name
    return (target / ".mnemo" / project_name).exists()


def prompt_choice() -> str:
    print("mnemo -- Agentic Knowledge Management System\n")
    print("How would you like to initialize mnemo?\n")
    print("  [1] Project + Global (recommended)")
    print("      -> .mnemo/<project-name>/   knowledge specific to this project")
    print("      -> ~/.mnemo/ knowledge reusable across all projects")
    print("      Best when you work across multiple projects.\n")
    print("  [2] Project only")
    print("      -> .mnemo/<project-name>/   self-contained knowledge base for this project\n")
    print("  [3] Global only")
    print("      -> ~/.mnemo/ single vault shared across all projects\n")
    raw = input("Choice [1/2/3] (default: 1): ").strip()
    return raw if raw in ("1", "2", "3") else "1"


def _parse_csv(value: str, defaults: list[str]) -> list[str]:
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items if len(items) >= 2 else defaults


def write_schema(mnemo_root: pathlib.Path, domain: str, entity_types: str, concept_categories: str) -> None:
    domain = domain.strip() or "General knowledge base for this project."
    entities = _parse_csv(entity_types, ["Person", "Tool", "Project"])
    concepts = _parse_csv(concept_categories, ["Pattern", "Technique", "Problem"])

    entity_lines = "\n".join(f"- **{name}** -- named {name.lower()} items in this domain" for name in entities)
    concept_lines = "\n".join(f"- **{name}** -- recurring {name.lower()} concepts in this domain" for name in concepts)
    schema = f"""# Knowledge Base Schema

## Domain
{domain}

## Entity Types
{entity_lines}

## Concept Taxonomy
{concept_lines}

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md` (e.g. `tool-redis.md`)
- Concept pages: `wiki/concepts/<category>-<name>.md` (e.g. `pattern-saga.md`)
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax -- always the exact H1 title of the target page. Obsidian-compatible.
"""
    (mnemo_root / "SCHEMA.md").write_text(schema, encoding="utf-8")


def write_profile(
    role: str,
    technical_level: str,
    language: str,
    domains: str,
    proactivity: str,
    register: str,
) -> bool:
    global_root = ensure_global_tier()
    profile_path = global_root / "wiki" / "entities" / "person-user.md"
    if profile_path.exists():
        print("  Global mnemo profile already exists -- keeping it unchanged.")
        return False

    today = date.today().isoformat()
    created = _read_created_date(profile_path)
    profile = f"""---
title: User Profile
category: entities
tags: [user, profile]
created: {created}
updated: {today}
---

# User Profile

## Role
{role.strip() or "Solo developer"}

## Technical Level
{technical_level.strip() or "CLI comfortable"}

## Language
{language.strip() or "English"}

## Domains
{domains.strip() or "General knowledge"}

## Proactivity
{proactivity.strip() or "Moderate"}

## Register
{register.strip() or "Direct"}

## Links
"""
    profile_path.write_text(profile, encoding="utf-8")
    return True


def _run_command(args: list[str], cwd: pathlib.Path | None = None) -> bool:
    result = subprocess.run(args, cwd=cwd)
    return result.returncode == 0


def _install_qmd() -> bool:
    installers = []
    if shutil.which("npm") is not None:
        installers.append(["npm", "install", "-g", "@tobilu/qmd"])
    if shutil.which("bun") is not None:
        installers.append(["bun", "install", "-g", "@tobilu/qmd"])

    if not installers:
        print("  qmd is not installed and no supported installer was found.")
        print("  Search backend will fall back to BM25.")
        return False

    for command in installers:
        print(f"  Installing qmd automatically: {' '.join(command)}")
        if _run_command(command):
            return shutil.which("qmd") is not None

    print("  Automatic qmd installation failed -- using BM25 for now.")
    return False


def _install_graphify() -> bool:
    print("  Installing graphify automatically...")
    if not _run_command([sys.executable, "-m", "pip", "install", "graphifyy"]):
        print("  graphify package installation failed.")
        return False

    if _run_command(["graphify", "install"]):
        return shutil.which("graphify") is not None

    if _run_command([sys.executable, "-m", "graphify", "install"]):
        return shutil.which("graphify") is not None

    print("  graphify runtime installation failed.")
    return False


def prompt_qmd(mnemo_root: pathlib.Path, project_name: str) -> None:
    print()
    ans = input("Enable hybrid search with qmd? (BM25 + vector, requires Node.js >= 22 or Bun >= 1.0) [Y/n]: ").strip().lower()
    if ans not in ("n", "no"):
        config = {"search_backend": "qmd", "qmd_collection": "mnemo-wiki"}
        if shutil.which("qmd") is None:
            print("  qmd is not installed; attempting automatic installation.")
            if not _install_qmd() or shutil.which("qmd") is None:
                print("  qmd still not found -- using BM25 for now.")
                config = {"search_backend": "bm25"}
        if config["search_backend"] == "qmd":
            collection_path = f".mnemo/{project_name}/wiki"
            result = subprocess.run(["qmd", "collection", "add", "mnemo-wiki", collection_path, "**/*.md"], cwd=mnemo_root.parent.parent)
            if result.returncode != 0:
                print("  qmd collection registration failed -- using BM25 for now.")
                config = {"search_backend": "bm25"}
            else:
                print("  qmd is configured. Embeddings will be built automatically on first /mnemo:ingest.")
    else:
        config = {"search_backend": "bm25"}
    (mnemo_root / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def configure_search(mnemo_root: pathlib.Path, project_name: str, search_backend: str) -> None:
    if search_backend == "bm25":
        config = {"search_backend": "bm25"}
        (mnemo_root / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
        print("  Search backend configured: BM25.")
        return

    config = {"search_backend": "qmd", "qmd_collection": "mnemo-wiki"}
    if shutil.which("qmd") is None:
        print("  qmd is not installed; attempting automatic installation.")
        if not _install_qmd() or shutil.which("qmd") is None:
            print("  qmd still not found -- using BM25 for now.")
            config = {"search_backend": "bm25"}
    if config["search_backend"] == "qmd":
        collection_path = f".mnemo/{project_name}/wiki"
        result = subprocess.run(["qmd", "collection", "add", "mnemo-wiki", collection_path, "**/*.md"], cwd=mnemo_root.parent.parent)
        if result.returncode != 0:
            print("  qmd collection registration failed -- using BM25 for now.")
            config = {"search_backend": "bm25"}
        else:
            print("  qmd is configured. Embeddings will be built automatically on first /mnemo:ingest.")
    (mnemo_root / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def _read_created_date(path: pathlib.Path) -> str:
    if not path.exists():
        return date.today().isoformat()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("created:"):
            return line.split(":", 1)[1].strip()
    return date.today().isoformat()


def prompt_schema_setup(mnemo_root: pathlib.Path) -> bool:
    """Collect baseline domain taxonomy during init so SCHEMA.md is not left as an optional follow-up."""
    print()
    print("Define the domain taxonomy for this knowledge base.")
    print("  This step is part of init. Leave a field blank to accept the starter defaults.")
    raw_files = sorted((mnemo_root / "raw").glob("*"))
    if raw_files:
        print(f"  Found {len(raw_files)} file(s) in raw/. Use them as context when answering.")

    domain = input("In one sentence, what is this knowledge base about? ").strip()
    entity_types = input("Entity types, comma-separated (e.g. Person, Tool, Project): ").strip()
    concept_categories = input("Concept categories, comma-separated (e.g. Pattern, Technique, Problem): ").strip()

    domain = domain or "General knowledge base for this project."
    entities = _parse_csv(entity_types, ["Person", "Tool", "Project"])
    concepts = _parse_csv(concept_categories, ["Pattern", "Technique", "Problem"])
    entity_lines = "\n".join(f"- **{name}** -- named {name.lower()} items in this domain" for name in entities)
    concept_lines = "\n".join(f"- **{name}** -- recurring {name.lower()} concepts in this domain" for name in concepts)
    schema = f"""# Knowledge Base Schema

## Domain
{domain}

## Entity Types
{entity_lines}

## Concept Taxonomy
{concept_lines}

## Naming Conventions
- Entity pages: `wiki/entities/<type>-<name>.md` (e.g. `tool-redis.md`)
- Concept pages: `wiki/concepts/<category>-<name>.md` (e.g. `pattern-saga.md`)
- Source pages: `wiki/sources/<slug>.md`
- Synthesis pages: `wiki/synthesis/<slug>.md`

## Wikilink Style
Use `[[Page Title]]` syntax -- always the exact H1 title of the target page. Obsidian-compatible.
"""
    print("\nSchema preview:")
    print(schema)
    confirm = input("Write this schema? [Y/e]: ").strip().lower()
    if confirm in ("e", "edit"):
        print("  Edit mode is not available in the standalone script yet; writing the generated schema.")
    write_schema(mnemo_root, domain, ", ".join(entities), ", ".join(concepts))
    print("  Schema written to SCHEMA.md.")
    return True


def _add_synthesis_links(path: pathlib.Path, links: list[str]) -> None:
    content = path.read_text(encoding="utf-8") if path.exists() else INDEX_TEMPLATE
    missing = [link for link in links if link not in content]
    if not missing:
        return

    lines = content.splitlines()
    if "## Synthesis" not in lines:
        lines.extend(["", "## Synthesis"])
    insert_at = lines.index("## Synthesis") + 1
    while insert_at < len(lines) and (lines[insert_at].startswith("- ") or lines[insert_at].strip() == ""):
        insert_at += 1
    lines[insert_at:insert_at] = missing
    path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def ensure_graphifyignore(target: pathlib.Path) -> None:
    defaults = [
        ".mnemo/",
        "graphify-out/",
        "node_modules/",
        ".git/",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        "dist/",
        "build/",
        "coverage/",
        ".next/",
        ".nuxt/",
    ]
    graphifyignore = target / ".graphifyignore"
    if not graphifyignore.exists():
        graphifyignore.write_text("\n".join(defaults) + "\n", encoding="utf-8")
        print("  Created .graphifyignore with default exclusions.")
        return

    content = graphifyignore.read_text(encoding="utf-8")
    existing = {line.strip() for line in content.splitlines()}
    missing = [entry for entry in defaults if entry not in existing]
    if missing:
        graphifyignore.write_text(content.rstrip("\n") + "\n" + "\n".join(missing) + "\n", encoding="utf-8")
        print(f"  Updated .graphifyignore -- added: {', '.join(missing)}.")


def write_graphify_pages(target: pathlib.Path, mnemo_root: pathlib.Path) -> bool:
    graph_dir = target / "graphify-out"
    report_path = graph_dir / "GRAPH_REPORT.md"
    graph_path = graph_dir / "graph.json"
    cache_path = graph_dir / "cache"

    if not report_path.exists():
        print("  graphify produced no GRAPH_REPORT.md. Nothing was written to the wiki.")
        return False
    if not graph_path.exists():
        print("  graphify produced no graph.json. Nothing was written to the wiki.")
        return False

    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    if not graph.get("nodes"):
        print("  graphify produced no nodes. Nothing was written to the wiki.")
        return False

    today = date.today().isoformat()
    now = datetime.now(timezone.utc).isoformat()
    synthesis = mnemo_root / "wiki" / "synthesis"
    synthesis.mkdir(parents=True, exist_ok=True)

    report_page = synthesis / "codebase-graph-report.md"
    report_created = _read_created_date(report_page)
    report = report_path.read_text(encoding="utf-8")
    report_page.write_text(f"""---
title: Codebase Graph Report
category: synthesis
tags: [graphify, codebase, graph-report]
source: graphify-out/GRAPH_REPORT.md
created: {report_created}
updated: {today}
---

# Codebase Graph Report

> *Generated by graphify on {today}. Canonical runtime artifacts live in `graphify-out/`. Refresh graphify after significant code changes.*

## Canonical Runtime

- Human-readable report: `graphify-out/GRAPH_REPORT.md`
- Structured graph: `graphify-out/graph.json`
- Incremental cache: `graphify-out/cache/`

## Usage

- Read `graphify-out/GRAPH_REPORT.md` first when you need a fast understanding of project structure.
- Use `graphify query ... --graph graphify-out/graph.json` for focused follow-up questions instead of scanning the entire codebase.
- Treat `graphify-out/` as the source of truth for graphify outputs.

## Report

{report}
""", encoding="utf-8")

    status_page = synthesis / "codebase-graph-status.md"
    status_created = _read_created_date(status_page)
    status_page.write_text(f"""---
title: Codebase Graph Status
category: synthesis
tags: [graphify, codebase, status]
created: {status_created}
updated: {today}
---

# Codebase Graph Status

- Canonical runtime directory: `graphify-out/`
- Report present: yes
- Graph present: yes
- Cache present: {"yes" if cache_path.exists() else "no"}
- Last graphify run: {now}

## Guidance

- Start with `graphify-out/GRAPH_REPORT.md`.
- Use `graphify-out/graph.json` for structured queries.
- Leave `graphify-out/cache/` in place so graphify can re-use its SHA256 cache on the next run.
""", encoding="utf-8")

    _add_synthesis_links(mnemo_root / "index.md", [
        "- [Codebase Graph Report](wiki/synthesis/codebase-graph-report.md)",
        "- [Codebase Graph Status](wiki/synthesis/codebase-graph-status.md)",
    ])
    with (mnemo_root / "log.md").open("a", encoding="utf-8") as f:
        f.write(f"- graphify-out/graph.json | {now} | graphify\n")
    return True


def prompt_graphify(target: pathlib.Path, mnemo_root: pathlib.Path | None = None) -> bool:
    """Ask the user if they want to map the codebase with graphify. Returns True if graphify ran successfully."""
    print()
    ans = input("Map your codebase with graphify? (builds a queryable knowledge graph -- no re-reading files each session) [Y/n]: ").strip().lower()
    if ans in ("n", "no"):
        print("  Codebase graph mapping was not enabled during init.")
        return False

    if shutil.which("graphify") is None:
        print("  graphify is not installed; attempting automatic installation.")
        if not _install_graphify() or shutil.which("graphify") is None:
            print("  graphify still not found -- codebase graph mapping was not enabled.")
            return False

    ensure_graphifyignore(target)
    print("  Running graphify on the project (this may take a moment)...")
    result = subprocess.run(["graphify", "."], cwd=target)
    if result.returncode != 0:
        print("  graphify failed -- codebase graph mapping was not enabled.")
        return False

    if mnemo_root is not None and not write_graphify_pages(target, mnemo_root):
        return False

    print("  Codebase mapped. Start with graphify-out/GRAPH_REPORT.md for structure.")
    return True


def run_graphify(target: pathlib.Path, mnemo_root: pathlib.Path | None = None) -> bool:
    if shutil.which("graphify") is None:
        print("  graphify is not installed; attempting automatic installation.")
        if not _install_graphify() or shutil.which("graphify") is None:
            print("  graphify still not found -- codebase graph mapping was not enabled.")
            return False

    ensure_graphifyignore(target)
    print("  Running graphify on the project (this may take a moment)...")
    result = subprocess.run(["graphify", "."], cwd=target)
    if result.returncode != 0:
        print("  graphify failed -- codebase graph mapping was not enabled.")
        return False

    if mnemo_root is not None and not write_graphify_pages(target, mnemo_root):
        return False

    print("  Codebase mapped. Start with graphify-out/GRAPH_REPORT.md for structure.")
    return True


def prompt_onboard() -> None:
    global_root = ensure_global_tier()
    profile_path = global_root / "wiki" / "entities" / "person-user.md"
    print()

    if profile_path.exists():
        print("  Global mnemo profile already exists -- keeping it unchanged.")
        return

    print("Set up your global mnemo user profile.")
    role_map = {
        "1": "Solo developer",
        "2": "Team lead or engineering manager",
        "3": "Content creator or writer",
        "4": "Researcher or student",
        "5": "Business owner",
    }
    level_map = {
        "1": "Terminal native",
        "2": "CLI comfortable",
        "3": "Config light",
        "4": "Non-technical",
    }
    proactive_map = {"1": "High", "2": "Moderate", "3": "Low"}
    register_map = {"1": "Direct", "2": "Collaborative"}

    role_raw = input("Role [1 Solo developer / 2 Team lead / 3 Content creator / 4 Researcher / 5 Business owner / other]: ").strip()
    role = role_map.get(role_raw, role_raw or "Solo developer")
    level = level_map.get(input("Technical level [1 Terminal native / 2 CLI comfortable / 3 Config light / 4 Non-technical]: ").strip(), "CLI comfortable")
    language = input("Language for notes and responses [English]: ").strip() or "English"
    domains = input("Main domains of interest (comma-separated): ").strip() or "General knowledge"
    proactivity = proactive_map.get(input("Proactivity [1 High / 2 Moderate / 3 Low]: ").strip(), "Moderate")
    register = register_map.get(input("Register [1 Direct / 2 Collaborative]: ").strip(), "Direct")

    print("\n## Your mnemo profile")
    print(f"Role: {role}")
    print(f"Technical level: {level}")
    print(f"Language: {language}")
    print(f"Domains: {domains}")
    print(f"Proactivity: {proactivity}")
    print(f"Register: {register}")
    ans = input("Write this profile? [Y/e]: ").strip().lower()
    if ans in ("e", "edit"):
        print("  Edit mode is not available in the standalone script yet; writing the generated profile.")
    write_profile(role, level, language, domains, proactivity, register)
    print("  Profile saved to ~/.mnemo/wiki/entities/person-user.md.")


def _contains_mnemo_stanza(path: pathlib.Path) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    return "## Knowledge Base (mnemo)" in content or "\n## mnemo\n" in f"\n{content}\n"


def _build_agents_stanza(project_name: str) -> str:
    return f"""## Knowledge Base (mnemo)

Wiki location: `.mnemo/{project_name}/wiki/`
Index: `.mnemo/{project_name}/index.md`
Session brief: `.mnemo/{project_name}/SESSION_BRIEF.md`

Workflow:
- At session startup, read `SESSION_BRIEF.md` if present. Read `graphify-out/GRAPH_REPORT.md` only for codebase-structure tasks. Do not load the whole wiki.
- If startup auto-load did not happen, run `/mnemo:context` or ask: "Load the minimal mnemo context for this project."
- Query before answering: invoke the `query` skill with the topic (read `skills/query/SKILL.md`).
- Ingest new sources: invoke the `ingest` skill after adding files to `.mnemo/{project_name}/raw/` (read `skills/ingest/SKILL.md`).
- Save insights: invoke the `save` skill with a descriptive title (read `skills/save/SKILL.md`).
- Lint after edits: invoke the `lint` skill at session end (read `skills/lint/SKILL.md`).
"""


def _build_claude_stanza(project_name: str, graphify_done: bool) -> str:
    stanza = f"""## mnemo

This project has a mnemo knowledge base in `.mnemo/{project_name}/`.

At session startup:
- Read `.mnemo/{project_name}/SESSION_BRIEF.md` if it exists.
- Read `graphify-out/GRAPH_REPORT.md` only when the task concerns codebase structure.
- Do not load the whole wiki at startup.
- If the brief was not auto-read at startup, load the minimal mnemo context for this project.

During the session:
- Query it with `/mnemo:query <term>` before answering factual questions.
- Ingest new sources with `/mnemo:ingest`
- When a spec or plan is finalized (e.g. from superpowers brainstorming or writing-plans), move it to `.mnemo/{project_name}/raw/` and run `/mnemo:ingest` to add it to the knowledge base
"""
    if graphify_done:
        stanza += "- Refresh graphify after significant code changes to keep the knowledge graph up to date\n"
    return stanza


def _append_stanza(path: pathlib.Path, stanza: str) -> None:
    if path.exists():
        content = path.read_text(encoding="utf-8").rstrip()
        path.write_text(f"{content}\n\n{stanza.rstrip()}\n", encoding="utf-8")
        return
    path.write_text(f"{stanza.rstrip()}\n", encoding="utf-8")


def ensure_claude_stop_hook(target: pathlib.Path) -> bool:
    settings_path = target / ".claude" / "settings.local.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    mnemo_command = "echo 'mnemo - session ending. Run /mnemo:mine to capture insights from this session.'"
    mnemo_hook = {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": mnemo_command,
            }
        ],
    }

    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("  .claude/settings.local.json is not valid JSON -- skipping mnemo stop hook wiring.")
            return False
    else:
        data = {}

    hooks = data.setdefault("hooks", {})
    stop_hooks = hooks.setdefault("Stop", [])
    for entry in stop_hooks:
        for hook in entry.get("hooks", []):
            if hook.get("command") == mnemo_command:
                return False

    stop_hooks.append(mnemo_hook)
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def wire_agent_memory(target: pathlib.Path, project_name: str, graphify_done: bool) -> str | None:
    agents_path = target / "AGENTS.md"
    claude_path = target / "CLAUDE.md"

    if agents_path.exists():
        target_path = agents_path
        stanza = _build_agents_stanza(project_name)
    elif claude_path.exists():
        target_path = claude_path
        stanza = _build_claude_stanza(project_name, graphify_done)
    else:
        target_path = agents_path
        stanza = _build_agents_stanza(project_name)

    if _contains_mnemo_stanza(target_path):
        return None

    _append_stanza(target_path, stanza)
    if target_path.name == "CLAUDE.md":
        ensure_claude_stop_hook(target)
    return target_path.name


def update_gitignore(target: pathlib.Path) -> None:
    gitignore = target / ".gitignore"
    entry = ".mnemo/"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if entry in content:
            print("[ok] .gitignore already contains .mnemo/")
            return
        gitignore.write_text(content.rstrip("\n") + "\n\n# mnemo knowledge base\n.mnemo/\n", encoding="utf-8")
    else:
        gitignore.write_text("# mnemo knowledge base\n.mnemo/\n", encoding="utf-8")
    print("[ok] .mnemo/ added to .gitignore")


def prompt_obsidian(vault_root: pathlib.Path) -> None:
    print()
    ans = input("Open this wiki in Obsidian? (visual graph, full-text search, Web Clipper integration) [Y/n]: ").strip().lower()
    if ans in ("n", "no"):
        print(f"  You can open {vault_root} as an Obsidian vault anytime — it's compatible out of the box.")
        return

    show_obsidian_instructions(vault_root)


def show_obsidian_instructions(vault_root: pathlib.Path) -> None:
    print()
    print("  If Obsidian is not yet installed, download it from: https://obsidian.md/")
    print("  (free, available on macOS, Windows, Linux, iOS, Android — no sign-up for local vaults)")
    print()
    print("  In Obsidian: Open folder as vault → select:")
    print(f"    {vault_root}")
    print("  (use ~/.mnemo/ for the global vault)")
    print()
    print("  For the Web Clipper browser extension:")
    print("    Install from: https://obsidian.md//clipper#more-browsers")
    print("    Set the default save location to: raw/")
    print("    Pages you clip will be picked up automatically by /mnemo:ingest")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap a mnemo knowledge base.")
    parser.add_argument("target", nargs="?", help="Project directory to initialize. Defaults to the current directory.")
    parser.add_argument("--non-interactive", action="store_true", help="Run without prompts using explicit values and safe defaults.")
    parser.add_argument("--init-scope", choices=("both", "project", "global"), default="both", help="Initialization scope for non-interactive mode.")
    parser.add_argument("--schema-domain", default="General knowledge base for this project.")
    parser.add_argument("--schema-entity-types", default="Person, Tool, Project")
    parser.add_argument("--schema-concept-categories", default="Pattern, Technique, Problem")
    parser.add_argument("--role", default="Solo developer")
    parser.add_argument("--technical-level", default="CLI comfortable")
    parser.add_argument("--language", default="English")
    parser.add_argument("--domains", default="General knowledge")
    parser.add_argument("--proactivity", default="Moderate")
    parser.add_argument("--register", default="Direct")
    parser.add_argument("--search-backend", choices=("bm25", "qmd"), default="bm25")
    parser.add_argument("--enable-graphify", action="store_true")
    parser.add_argument("--open-obsidian", action="store_true")
    parser.add_argument("--add-gitignore", dest="add_gitignore", action="store_true", default=True)
    parser.add_argument("--no-add-gitignore", dest="add_gitignore", action="store_false")
    return parser.parse_args(argv)


def _choice_from_scope(scope: str) -> str:
    return {"both": "1", "project": "2", "global": "3"}[scope]


def main(argv: list[str] | None = None) -> None:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    target = pathlib.Path(args.target).resolve() if args.target else pathlib.Path.cwd()
    project_name = target.name

    if guard(target):
        print(f".mnemo/{project_name}/ already exists.")
        print(f"To start over, delete .mnemo/{project_name}/ and re-run this script.")
        sys.exit(0)

    choice = _choice_from_scope(args.init_scope) if args.non_interactive else prompt_choice()
    initialized: list[str] = []

    if choice in ("1", "2"):
        local_root = target / ".mnemo" / project_name
        create_structure(local_root)
        initialized.append(f"[ok] .mnemo/{project_name}/ initialized in {target}")

    if choice in ("1", "3"):
        global_root = pathlib.Path.home() / ".mnemo"
        if not global_root.exists():
            create_structure(global_root)
            initialized.append("[ok] ~/.mnemo/ initialized")
        else:
            initialized.append("[ok] ~/.mnemo/ already exists -- skipped")

    print()
    for line in initialized:
        print(line)

    if choice in ("1", "2"):
        if args.non_interactive:
            write_schema(local_root, args.schema_domain, args.schema_entity_types, args.schema_concept_categories)
            print("  Schema written to SCHEMA.md.")
        else:
            prompt_schema_setup(local_root)

    if args.non_interactive:
        if write_profile(args.role, args.technical_level, args.language, args.domains, args.proactivity, args.register):
            print("  Profile saved to ~/.mnemo/wiki/entities/person-user.md.")
    else:
        prompt_onboard()

    if choice in ("1", "2"):
        if args.non_interactive:
            configure_search(local_root, project_name, args.search_backend)
        else:
            prompt_qmd(local_root, project_name)

    if choice in ("1", "2") and (target / ".git").exists():
        if args.non_interactive:
            if args.add_gitignore:
                update_gitignore(target)
        else:
            print()
            ans = input("Add .mnemo/ to .gitignore? (recommended — keeps your wiki out of version control) [Y/n]: ").strip().lower()
            if ans in ("", "y", "yes"):
                update_gitignore(target)

    graphify_done = False
    if choice in ("1", "2"):
        if args.non_interactive:
            if args.enable_graphify:
                graphify_done = run_graphify(target, local_root)
            else:
                print("  Codebase graph mapping was not enabled during init.")
        else:
            graphify_done = prompt_graphify(target, local_root)

    if choice in ("1", "2"):
        if args.non_interactive:
            if args.open_obsidian:
                show_obsidian_instructions(local_root)
            else:
                print(f"  You can open {local_root} as an Obsidian vault anytime — it's compatible out of the box.")
        else:
            prompt_obsidian(local_root)
        update_session_brief(local_root)
        wired_target = wire_agent_memory(target, project_name, graphify_done)
        if wired_target is not None:
            print(f"  mnemo instructions added to {wired_target}.")

    if choice in ("1", "2"):
        print("\nReady:")
        print(f"  Add source files to .mnemo/{project_name}/raw/ and run /mnemo:ingest")
    else:
        print("\nReady.")


if __name__ == "__main__":
    try:
        main()
    except EOFError:
        print(
            "mnemo init needs interactive stdin. Re-run in a terminal, or use "
            "`--non-interactive` with --schema-* and onboarding arguments.",
            file=sys.stderr,
        )
        sys.exit(2)
