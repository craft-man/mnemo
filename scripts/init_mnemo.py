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

DIRS = [
    "raw",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/synthesis",
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


def create_structure(root: pathlib.Path) -> None:
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    (root / "index.md").write_text(INDEX_TEMPLATE, encoding="utf-8")
    (root / "log.md").write_text(LOG_TEMPLATE, encoding="utf-8")
    (root / "SCHEMA.md").write_text(SCHEMA_TEMPLATE, encoding="utf-8")


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


def prompt_qmd(mnemo_root: pathlib.Path) -> None:
    print()
    ans = input("Enable hybrid search with qmd? (BM25 + vector, requires Node.js >= 22 or Bun >= 1.0) [y/N]: ").strip().lower()
    if ans in ("y", "yes"):
        config = {"search_backend": "qmd", "qmd_collection": "mnemo-wiki"}
        print("  Install qmd if needed:  npm install -g qmd  or  bun add -g qmd")
        print("  Then run: qmd collection add mnemo-wiki .mnemo/wiki \"**/*.md\"")
    else:
        config = {"search_backend": "bm25"}
    (mnemo_root / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


def prompt_graphify(target: pathlib.Path) -> bool:
    """Ask the user if they want to map the codebase with graphify. Returns True if graphify ran successfully."""
    print()
    ans = input("Map your codebase with graphify? (builds a queryable knowledge graph — no re-reading files each session) [y/N]: ").strip().lower()
    if ans not in ("y", "yes"):
        print("  You can run /mnemo:graphify anytime to map your codebase.")
        return False

    if shutil.which("graphify") is None:
        print("  graphify is not installed. Install it with:")
        print("    pip install graphifyy && graphify install")
        ans2 = input("  Press Enter once installed, or type 's' to skip: ").strip().lower()
        if ans2 in ("s", "skip"):
            print("  Skipped. Run /mnemo:graphify manually later.")
            return False
        if shutil.which("graphify") is None:
            print("  graphify still not found — skipping. Run /mnemo:graphify manually later.")
            return False

    print("  Running graphify on the project (this may take a moment)...")
    result = subprocess.run(["graphify", "."], cwd=target)
    if result.returncode != 0:
        print("  graphify failed — run /mnemo:graphify manually to retry.")
        return False

    print("  Codebase mapped. Query it with /mnemo:query <term>.")
    return True


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
        prompt_qmd(local_root)

    if choice in ("1", "2") and (target / ".git").exists():
        print()
        ans = input("Add .mnemo/ to .gitignore? (recommended — keeps your wiki out of version control) [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            update_gitignore(target)

    graphify_done = False
    if choice in ("1", "2"):
        graphify_done = prompt_graphify(target)

    if choice in ("1", "2"):
        prompt_obsidian(local_root)

    print("\nNext steps:")
    if graphify_done:
        print("  Re-run /mnemo:graphify after significant code changes to keep the graph up to date")
    else:
        print("  Run /mnemo:graphify to map your codebase into a queryable knowledge graph")
        print(f"  Or: run /mnemo:schema to define your domain taxonomy, drop files into .mnemo/{project_name}/raw/, run /mnemo:ingest")
    print("  Query with /mnemo:query <term>")


if __name__ == "__main__":
    main()
