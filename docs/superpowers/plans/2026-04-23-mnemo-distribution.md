# mnemo Distribution & Friction Reduction — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish mnemo on the Claude Code marketplace, add a Python bootstrap script, wire CLAUDE.md automatically at init, and update the README.

**Architecture:** Additive only — no changes to existing SKILL.md files. Four independent deliverables: (1) plugin.json + commands/ for marketplace, (2) init_mnemo.py Python bootstrap script, (3) CLAUDE.md auto-wiring step appended to the init skill, (4) README update.

**Tech Stack:** Python 3.10+ stdlib, Markdown, JSON

---

## File Map

| Action | File |
|---|---|
| Modify | `.claude-plugin/plugin.json` |
| Create | `commands/mnemo/init.md` |
| Create | `commands/mnemo/schema.md` |
| Create | `commands/mnemo/ingest.md` |
| Create | `commands/mnemo/query.md` |
| Create | `commands/mnemo/lint.md` |
| Create | `commands/mnemo/save.md` |
| Create | `commands/mnemo/stats.md` |
| Create | `scripts/init_mnemo.py` |
| Create | `tests/test_init_mnemo.py` |
| Modify | `skills/init/SKILL.md` |
| Modify | `README.md` |

---

## Task 1: Update plugin.json for marketplace

**Files:**
- Modify: `.claude-plugin/plugin.json`

- [ ] **Step 1: Add the three missing marketplace fields**

Replace the contents of `.claude-plugin/plugin.json` with:

```json
{
  "name": "mnemo",
  "description": "Agentic Knowledge Management System — a Second Brain for Claude Code and agentskills.io-compatible agents. Ingests raw files into a synthesized, searchable wiki; queries your knowledge base; saves AI-generated insights permanently.",
  "version": "0.3.0",
  "author": {
    "name": "mnemo contributors"
  },
  "homepage": "https://github.com/craft-man/mnemo",
  "repository": "https://github.com/craft-man/mnemo",
  "license": "MIT",
  "keywords": ["knowledge-base", "wiki", "second-brain", "obsidian", "rag-alternative", "llm-wiki"],
  "category": "productivity"
}
```

- [ ] **Step 2: Verify JSON is valid**

```bash
python3 -c "import json; json.load(open('.claude-plugin/plugin.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add .claude-plugin/plugin.json
git commit -m "feat: add marketplace fields to plugin.json (repository, keywords, category)"
```

---

## Task 2: Create commands/mnemo/ slash command descriptors

**Files:**
- Create: `commands/mnemo/init.md`
- Create: `commands/mnemo/schema.md`
- Create: `commands/mnemo/ingest.md`
- Create: `commands/mnemo/query.md`
- Create: `commands/mnemo/lint.md`
- Create: `commands/mnemo/save.md`
- Create: `commands/mnemo/stats.md`

These are thin entry-point files. The actual logic lives in `skills/*/SKILL.md`. Do not duplicate instructions here.

- [ ] **Step 1: Create the commands directory and all 7 files**

`commands/mnemo/init.md`:
```markdown
---
description: Bootstrap a new mnemo knowledge base with taxonomy structure and SCHEMA.md
---

Run the mnemo init skill to initialize `.mnemo/` in the current project.
```

`commands/mnemo/schema.md`:
```markdown
---
description: Interactively create or revise the mnemo domain taxonomy (SCHEMA.md)
---

Run the mnemo schema skill to define or revise the domain taxonomy for this knowledge base.
```

`commands/mnemo/ingest.md`:
```markdown
---
description: Process raw files in .mnemo/raw/ into synthesized wiki pages
---

Run the mnemo ingest skill to process all pending files in `.mnemo/raw/`.
```

`commands/mnemo/query.md`:
```markdown
---
description: Search the mnemo knowledge base with BM25 or hybrid semantic search
---

Run the mnemo query skill to search the knowledge base for the provided term.
```

`commands/mnemo/lint.md`:
```markdown
---
description: Audit the mnemo knowledge base for structure issues and broken links
---

Run the mnemo lint skill to audit the knowledge base and propose fixes.
```

`commands/mnemo/save.md`:
```markdown
---
description: Save a Claude-generated insight as a permanent wiki page
---

Run the mnemo save skill to persist the provided content as a wiki page.
```

`commands/mnemo/stats.md`:
```markdown
---
description: Display mnemo knowledge base size metrics and scaling status
---

Run the mnemo stats skill to display page counts, sizes, and index scaling status.
```

- [ ] **Step 2: Verify all 7 files exist**

```bash
ls commands/mnemo/
```

Expected output:
```
init.md  ingest.md  lint.md  query.md  save.md  schema.md  stats.md
```

- [ ] **Step 3: Commit**

```bash
git add commands/mnemo/
git commit -m "feat: add commands/mnemo/ slash command descriptors for marketplace"
```

---

## Task 3: Write tests for init_mnemo.py

**Files:**
- Create: `tests/test_init_mnemo.py`

- [ ] **Step 1: Create the tests file**

```python
#!/usr/bin/env python3
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from init_mnemo import create_structure, guard, DIRS


class TestCreateStructure(unittest.TestCase):
    def test_creates_all_wiki_subdirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            for d in DIRS:
                self.assertTrue((root / d).is_dir(), f"Missing dir: {d}")

    def test_creates_raw_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            self.assertTrue((root / "raw").is_dir())

    def test_creates_index_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            self.assertTrue((root / "index.md").exists())

    def test_index_has_category_headings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            content = (root / "index.md").read_text()
            for heading in ("## Sources", "## Entities", "## Concepts", "## Synthesis"):
                self.assertIn(heading, content)

    def test_creates_log_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            self.assertTrue((root / "log.md").exists())

    def test_creates_schema_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            self.assertTrue((root / "SCHEMA.md").exists())

    def test_schema_md_has_entity_types_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            content = (root / "SCHEMA.md").read_text()
            self.assertIn("## Entity Types", content)

    def test_idempotent_on_second_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / ".mnemo"
            create_structure(root)
            create_structure(root)  # should not raise
            self.assertTrue((root / "wiki" / "sources").is_dir())


class TestGuard(unittest.TestCase):
    def test_returns_true_when_mnemo_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".mnemo").mkdir()
            self.assertTrue(guard(target))

    def test_returns_false_when_mnemo_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(guard(pathlib.Path(tmp)))


class TestMainProjectOnly(unittest.TestCase):
    def test_choice_2_creates_local_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            with patch("builtins.input", return_value="2"), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / "wiki" / "sources").is_dir())

    def test_choice_2_does_not_create_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            with patch("builtins.input", return_value="2"), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertFalse((fake_home / ".mnemo").exists())


class TestMainGlobalOnly(unittest.TestCase):
    def test_choice_3_creates_global_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            with patch("builtins.input", return_value="3"), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "sources").is_dir())


class TestMainBoth(unittest.TestCase):
    def test_choice_1_creates_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            with patch("builtins.input", return_value="1"), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / "wiki" / "sources").is_dir())
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "sources").is_dir())

    def test_default_choice_is_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            with patch("builtins.input", return_value=""), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / "wiki" / "sources").is_dir())
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "sources").is_dir())


class TestGuardClause(unittest.TestCase):
    def test_guard_prints_message_and_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".mnemo").mkdir()
            printed = []
            with patch("builtins.input", return_value="2"), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("builtins.print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))), \
                 self.assertRaises(SystemExit) as ctx:
                from init_mnemo import main
                main()
            self.assertEqual(ctx.exception.code, 0)
            combined = " ".join(printed)
            self.assertIn("already exists", combined)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests — expect ImportError (module does not exist yet)**

```bash
python3 -m pytest tests/test_init_mnemo.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'init_mnemo'`

- [ ] **Step 3: Commit the tests**

```bash
git add tests/test_init_mnemo.py
git commit -m "test: add tests for init_mnemo.py (red)"
```

---

## Task 4: Implement init_mnemo.py

**Files:**
- Create: `scripts/init_mnemo.py`

- [ ] **Step 1: Write the implementation**

```python
#!/usr/bin/env python3
"""Bootstrap a mnemo knowledge base. Python 3.10+ stdlib only.

Usage:
  python scripts/init_mnemo.py              # current directory
  python scripts/init_mnemo.py ./my-project # specific directory
"""
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
    print("mnemo — Agentic Knowledge Management System\n")
    print("How would you like to initialize mnemo?\n")
    print("  [1] Project + Global (recommended)")
    print("      → .mnemo/   knowledge specific to this project")
    print("      → ~/.mnemo/ knowledge reusable across all projects")
    print("      Best when you work across multiple projects.\n")
    print("  [2] Project only")
    print("      → .mnemo/   self-contained knowledge base for this project\n")
    print("  [3] Global only")
    print("      → ~/.mnemo/ single vault shared across all projects\n")
    raw = input("Choice [1/2/3] (default: 1): ").strip()
    return raw if raw in ("1", "2", "3") else "1"


def main() -> None:
    target = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else pathlib.Path.cwd()

    if guard(target):
        print(".mnemo/ already exists.")
        print("Use /mnemo:init to re-initialize or /mnemo:schema to revise the taxonomy.")
        sys.exit(0)

    choice = prompt_choice()
    initialized: list[str] = []

    if choice in ("1", "2"):
        create_structure(target / ".mnemo")
        initialized.append(f"✓ .mnemo/ initialized in {target}")

    if choice in ("1", "3"):
        global_root = pathlib.Path.home() / ".mnemo"
        if not global_root.exists():
            create_structure(global_root)
            initialized.append("✓ ~/.mnemo/ initialized")
        else:
            initialized.append("~/.mnemo/ already exists — skipped")

    print()
    for line in initialized:
        print(line)

    print("\nNext steps:")
    print("  Run /mnemo:schema to define your domain taxonomy")
    print("  Drop files into .mnemo/raw/ and run /mnemo:ingest")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the tests — expect all green**

```bash
python3 -m pytest tests/test_init_mnemo.py -v
```

Expected: all tests PASS

- [ ] **Step 3: Run the script manually to verify the interactive prompt**

```bash
python3 scripts/init_mnemo.py /tmp/mnemo-test-run
```

Walk through option `1`, verify `.mnemo/` is created with correct structure:

```bash
find /tmp/mnemo-test-run/.mnemo -type f
```

Expected:
```
/tmp/mnemo-test-run/.mnemo/index.md
/tmp/mnemo-test-run/.mnemo/log.md
/tmp/mnemo-test-run/.mnemo/SCHEMA.md
```

- [ ] **Step 4: Verify guard clause works**

```bash
python3 scripts/init_mnemo.py /tmp/mnemo-test-run
```

Expected output:
```
.mnemo/ already exists.
Use /mnemo:init to re-initialize or /mnemo:schema to revise the taxonomy.
```

- [ ] **Step 5: Commit**

```bash
git add scripts/init_mnemo.py
git commit -m "feat: add init_mnemo.py — Python stdlib bootstrap script with two-tier setup"
```

---

## Task 5: Add CLAUDE.md auto-wiring to skills/init/SKILL.md

**Files:**
- Modify: `skills/init/SKILL.md`

The existing init skill ends at **step 6** (the report). Add a new **step 7** after it.

- [ ] **Step 1: Append the CLAUDE.md wiring step**

In `skills/init/SKILL.md`, replace the final step 6 block:

```markdown
**6. Report:**
> "Knowledge base initialized at `.mnemo/`.
> Search backend: **<qmd | BM25>**.
> Next: drop files into `.mnemo/raw/` and run `/mnemo:ingest`."
> (If schema was not defined in step 4, add: "Run `/mnemo:schema` to define your domain taxonomy first.")
```

With:

```markdown
**6. Report:**
> "Knowledge base initialized at `.mnemo/`.
> Search backend: **<qmd | BM25>**.
> Next: drop files into `.mnemo/raw/` and run `/mnemo:ingest`."
> (If schema was not defined in step 4, add: "Run `/mnemo:schema` to define your domain taxonomy first.")

**7. CLAUDE.md wiring** — offer to persist the wiki in the project's agent memory:

Ask the user:
> "Want me to add a memory stanza to `CLAUDE.md` so I remember this wiki in future sessions? [y/n]"

If `[n]`: do nothing. Do not ask again.

If `[y]`:

Check if `CLAUDE.md` already contains the string `mnemo knowledge base`. If yes: skip silently.

Otherwise:

Build the stanza based on what was initialized in steps 2–5:

```markdown
## mnemo

This project has a mnemo knowledge base in `.mnemo/`.
- Query it with `/mnemo:query <term>` before answering factual questions
- Ingest new sources with `/mnemo:ingest`
```

If global vault was also initialized (choice `1` in `init_mnemo.py` or global confirmed in this session), append this line to the stanza:
```markdown
- Global knowledge base available at `~/.mnemo/`
```

Then:
- If `CLAUDE.md` exists: append the stanza at the end of the file, preceded by a blank line.
- If `CLAUDE.md` does not exist: create it with the stanza as the only content.

Confirm:
> "Done — stanza added to `CLAUDE.md`. I'll remember this wiki in future sessions."
```

- [ ] **Step 2: Verify the file ends correctly (no truncation)**

Read the last 30 lines of `skills/init/SKILL.md` and confirm step 7 is present and complete.

- [ ] **Step 3: Commit**

```bash
git add skills/init/SKILL.md
git commit -m "feat: add CLAUDE.md auto-wiring step to /mnemo:init skill"
```

---

## Task 6: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the Installation section**

Find the existing `## Installation` section and replace it with:

```markdown
## Installation

**Requirements:** [Claude Code](https://claude.ai/code) CLI

### Claude Code marketplace (recommended)

```
/plugin marketplace add craft-man/mnemo
```

Once installed, mnemo is available in any project — no `--plugin-dir` needed.

### Manual (git clone)

```bash
git clone https://github.com/craft-man/mnemo
claude --plugin-dir ./mnemo
```

To avoid typing `--plugin-dir` on every invocation:

```bash
echo 'alias claude="claude --plugin-dir /path/to/mnemo"' >> ~/.bashrc
source ~/.bashrc
```
```

- [ ] **Step 2: Add a Quick start section after Installation**

Insert after the Installation section, before the existing `## Search backends` section:

```markdown
## Quick start

Bootstrap a new knowledge base without Claude:

```bash
python scripts/init_mnemo.py
```

You'll be prompted to choose between project-only, global, or both tiers. Then in Claude Code:

```
/mnemo:schema      # define your domain taxonomy
# drop files into .mnemo/raw/
/mnemo:ingest      # synthesize → wiki pages
/mnemo:query <term>
```
```

- [ ] **Step 3: Update the Typical workflow section**

Find the existing `## Typical workflow` section. Replace the first comment line:

Old:
```markdown
/mnemo:init                          # bootstrap once per project
```

New:
```markdown
python scripts/init_mnemo.py         # bootstrap once — no Claude needed
/mnemo:init                          # optional: re-init or configure qmd
```

- [ ] **Step 4: Verify README renders correctly**

```bash
python3 -c "
import re, pathlib
text = pathlib.Path('README.md').read_text()
assert '/plugin marketplace add craft-man/mnemo' in text
assert 'python scripts/init_mnemo.py' in text
assert '## Quick start' in text
print('README OK')
"
```

Expected: `README OK`

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: update README with marketplace install and Quick start section"
```

---

## Self-review

**Spec coverage check:**

| Spec requirement | Task |
|---|---|
| `plugin.json` — add `repository`, `keywords`, `category` | Task 1 |
| `commands/mnemo/` — 7 command files | Task 2 |
| `scripts/init_mnemo.py` — interactive two-tier bootstrap | Task 4 |
| Interactive prompt with 3 options + explanation | Task 4 |
| Guard clause for existing `.mnemo/` | Task 4 |
| CLAUDE.md wiring in `/mnemo:init` | Task 5 |
| README — marketplace install + Quick start | Task 6 |

All spec requirements covered. No gaps.
