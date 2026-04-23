#!/usr/bin/env python3
"""Bootstrap a mnemo knowledge base. Python 3.10+ stdlib only.

Usage:
  python scripts/init_mnemo.py              # current directory
  python scripts/init_mnemo.py ./my-project # specific directory
"""
import json
import pathlib
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
    return (target / ".mnemo").exists()


def prompt_choice() -> str:
    print("mnemo -- Agentic Knowledge Management System\n")
    print("How would you like to initialize mnemo?\n")
    print("  [1] Project + Global (recommended)")
    print("      -> .mnemo/   knowledge specific to this project")
    print("      -> ~/.mnemo/ knowledge reusable across all projects")
    print("      Best when you work across multiple projects.\n")
    print("  [2] Project only")
    print("      -> .mnemo/   self-contained knowledge base for this project\n")
    print("  [3] Global only")
    print("      -> ~/.mnemo/ single vault shared across all projects\n")
    raw = input("Choice [1/2/3] (default: 1): ").strip()
    return raw if raw in ("1", "2", "3") else "1"


def prompt_qmd(mnemo_root: pathlib.Path) -> None:
    print()
    ans = input("Enable hybrid search with qmd? (BM25 + vector, requires Node.js >= 22 or Bun >= 1.0) [y/N]: ").strip().lower()
    if ans in ("y", "yes"):
        config = {"semantic_search": "qmd", "qmd_collection": "mnemo-wiki"}
        print("  Install qmd if needed:  npm install -g qmd  or  bun add -g qmd")
        print("  Then run: qmd collection add mnemo-wiki .mnemo/wiki \"**/*.md\"")
    else:
        config = {"semantic_search": "bm25"}
    (mnemo_root / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")


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


def main() -> None:
    target = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()

    if guard(target):
        print(".mnemo/ already exists.")
        print("To start over, delete .mnemo/ and re-run this script.")
        print("If you have Claude Code, run /mnemo:schema to revise the taxonomy.")
        sys.exit(0)

    choice = prompt_choice()
    initialized: list[str] = []

    if choice in ("1", "2"):
        create_structure(target / ".mnemo")
        initialized.append(f"[ok] .mnemo/ initialized in {target}")

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
        prompt_qmd(target / ".mnemo")

    if choice in ("1", "2") and (target / ".git").exists():
        print()
        ans = input("Add .mnemo/ to .gitignore? (recommended — keeps your wiki out of version control) [Y/n]: ").strip().lower()
        if ans in ("", "y", "yes"):
            update_gitignore(target)

    print("\nNext steps:")
    print("  Run /mnemo:schema to define your domain taxonomy")
    print("  Drop files into .mnemo/raw/ and run /mnemo:ingest")


if __name__ == "__main__":
    main()
