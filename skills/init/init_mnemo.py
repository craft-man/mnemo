#!/usr/bin/env python3
"""Bootstrap a mnemo knowledge base. Python 3.10+ stdlib only.

Usage:
  python scripts/init_mnemo.py              # current directory
  python scripts/init_mnemo.py ./my-project # specific directory
"""
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
> Run /mnemo:schema to have Claude guide you through customization.

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
        print("  SESSION_BRIEF.md was not updated. Run scripts/update_session_brief.py manually to retry.")


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
        print("  Install Node.js >= 22 or Bun >= 1.0, then re-run /mnemo:init or /mnemo:query.")
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
            ans2 = input("  qmd is not installed. Install it automatically now? [Y/n/s skip]: ").strip().lower()
            if ans2 in ("s", "skip"):
                config = {"search_backend": "bm25"}
            elif ans2 not in ("", "y", "yes") or not _install_qmd() or shutil.which("qmd") is None:
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


def _read_created_date(path: pathlib.Path) -> str:
    if not path.exists():
        return date.today().isoformat()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("created:"):
            return line.split(":", 1)[1].strip()
    return date.today().isoformat()


def prompt_schema_setup(mnemo_root: pathlib.Path) -> bool:
    """Offer a standalone schema customization path for the init fast path."""
    print()
    ans = input("Define your domain taxonomy now? (you can run /mnemo:schema anytime) [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        print("  Starter SCHEMA.md will be used until you run /mnemo:schema.")
        return False

    raw_files = sorted((mnemo_root / "raw").glob("*"))
    if raw_files:
        print(f"  Found {len(raw_files)} file(s) in raw/. Use them as context when answering.")

    domain = input("In one sentence, what is this knowledge base about? ").strip()
    entity_types = input("Entity types, comma-separated (e.g. Person, Tool, Project): ").strip()
    concept_categories = input("Concept categories, comma-separated (e.g. Pattern, Technique, Problem): ").strip()

    entities = [item.strip() for item in entity_types.split(",") if item.strip()]
    concepts = [item.strip() for item in concept_categories.split(",") if item.strip()]
    if not domain:
        domain = "General knowledge base for this project."
    if len(entities) < 2:
        entities = ["Person", "Tool", "Project"]
    if len(concepts) < 2:
        concepts = ["Pattern", "Technique", "Problem"]

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
        print("  Edit mode is not available in the standalone script yet. Re-run /mnemo:schema to revise.")
    (mnemo_root / "SCHEMA.md").write_text(schema, encoding="utf-8")
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

> *Generated by graphify on {today}. Canonical runtime artifacts live in `graphify-out/`. Re-run `/mnemo:graphify` to refresh.*

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
        print("  You can run /mnemo:graphify anytime to map your codebase.")
        return False

    if shutil.which("graphify") is None:
        ans2 = input("  graphify is not installed. Install it automatically now? [Y/n/s skip]: ").strip().lower()
        if ans2 in ("s", "skip"):
            print("  Skipped. Run /mnemo:graphify manually later.")
            return False
        if ans2 not in ("", "y", "yes") or not _install_graphify() or shutil.which("graphify") is None:
            print("  graphify still not found — skipping. Run /mnemo:graphify manually later.")
            return False

    ensure_graphifyignore(target)
    print("  Running graphify on the project (this may take a moment)...")
    result = subprocess.run(["graphify", "."], cwd=target)
    if result.returncode != 0:
        print("  graphify failed — run /mnemo:graphify manually to retry.")
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
        content = profile_path.read_text(encoding="utf-8")
        print("User profile already exists:")
        for heading in ("Role", "Technical Level", "Language", "Domains", "Proactivity", "Register"):
            marker = f"## {heading}"
            if marker in content:
                value = content.split(marker, 1)[1].split("\n## ", 1)[0].strip()
                print(f"  {heading}: {value}")
        ans = input("Review and update it? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("  Profile unchanged.")
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
{role}

## Technical Level
{level}

## Language
{language}

## Domains
{domains}

## Proactivity
{proactivity}

## Register
{register}

## Links
"""
    print("\n## Your mnemo profile")
    print(f"Role: {role}")
    print(f"Technical level: {level}")
    print(f"Language: {language}")
    print(f"Domains: {domains}")
    print(f"Proactivity: {proactivity}")
    print(f"Register: {register}")
    ans = input("Write this profile? [Y/e]: ").strip().lower()
    if ans in ("e", "edit"):
        print("  Edit mode is not available in the standalone script yet. Re-run /mnemo:onboard to revise.")
    profile_path.write_text(profile, encoding="utf-8")
    print("  Profile saved to ~/.mnemo/wiki/entities/person-user.md.")


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
    ans = input("Open this wiki in Obsidian? (visual graph, full-text search, Web Clipper integration) [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        print(f"  You can open {vault_root} as an Obsidian vault anytime — it's compatible out of the box.")
        return

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


def main() -> None:
    target = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()
    project_name = target.name

    if guard(target):
        print(f".mnemo/{project_name}/ already exists.")
        print(f"To start over, delete .mnemo/{project_name}/ and re-run this script.")
        print("If you have Claude Code, run /mnemo:schema to revise the taxonomy.")
        sys.exit(0)

    choice = prompt_choice()
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
        prompt_schema_setup(local_root)

    prompt_onboard()

    if choice in ("1", "2"):
        prompt_qmd(local_root, project_name)

    if choice in ("1", "2") and (target / ".git").exists():
        print()
        ans = input("Add .mnemo/ to .gitignore? (recommended — keeps your wiki out of version control) [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            update_gitignore(target)

    graphify_done = False
    if choice in ("1", "2"):
        graphify_done = prompt_graphify(target, local_root)

    if choice in ("1", "2"):
        prompt_obsidian(local_root)
        update_session_brief(local_root)

    print("\nNext steps:")
    if graphify_done:
        print("  Re-run /mnemo:graphify after significant code changes to keep the graph up to date")
    else:
        print("  Run /mnemo:graphify to map your codebase into a queryable knowledge graph")
        print(f"  Or: run /mnemo:schema to define your domain taxonomy, drop files into .mnemo/{project_name}/raw/, run /mnemo:ingest")
    print("  Query with /mnemo:query <term>")


if __name__ == "__main__":
    main()
