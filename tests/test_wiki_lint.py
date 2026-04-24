#!/usr/bin/env python3
import io
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from wiki_lint import parse_frontmatter, main


SUPERSEDED_PAGE = """\
---
title: Old Tool
category: entities
tags: [tool]
superseded_by: New Tool
created: 2025-01-01
updated: 2026-01-01
---

# Old Tool

> *Type: Tool*

---

## Description

This tool does things.

## Sources

- [[Some Source]]

## Links

- [[Some Source]]
"""

SUPERSEDED_PAGE_WITH_HISTORY = """\
---
title: Old Tool
category: entities
tags: [tool]
superseded_by: New Tool
created: 2025-01-01
updated: 2026-01-01
---

# Old Tool

> *Type: Tool*

---

## Description

This tool does things.

## History

- **2026-01-01**: Replaced by [[New Tool]] — see [[Some Source]]

## Sources

- [[Some Source]]

## Links

- [[Some Source]]
"""

HEALTHY_PAGE = """\
---
title: Active Tool
category: entities
tags: [tool]
created: 2025-01-01
updated: 2026-01-01
---

# Active Tool

> *Type: Tool*

---

## Description

This tool is active.

## Sources

- [[Some Source]]

## Links

- [[Some Source]]
"""


def _make_wiki(root: pathlib.Path, pages: dict) -> pathlib.Path:
    mnemo = root / ".mnemo"
    for subdir in ["wiki/sources", "wiki/entities", "wiki/concepts",
                   "wiki/synthesis", "wiki/indexes"]:
        (mnemo / subdir).mkdir(parents=True, exist_ok=True)
    (mnemo / "SCHEMA.md").write_text("# Schema\n")
    (mnemo / "raw").mkdir(exist_ok=True)
    (mnemo / "log.md").write_text("")
    index_lines = []
    for rel_path, content in pages.items():
        dest = mnemo / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        title = next(
            (line[2:].strip() for line in content.splitlines() if line.startswith("# ")),
            rel_path,
        )
        index_lines.append(f"- [{title}]({rel_path})\n")
    (mnemo / "index.md").write_text("## Entities\n\n" + "".join(index_lines))
    return mnemo


def _run_lint(mnemo_dir: pathlib.Path) -> str:
    buf = io.StringIO()
    with patch("sys.argv", ["wiki_lint.py", str(mnemo_dir)]):
        with redirect_stdout(buf):
            main()
    return buf.getvalue()


class TestSupersededWithoutHistory(unittest.TestCase):
    def test_superseded_page_without_history_is_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            mnemo = _make_wiki(
                pathlib.Path(tmp),
                {"wiki/entities/tool-old.md": SUPERSEDED_PAGE},
            )
            output = _run_lint(mnemo)
        self.assertIn("superseded_without_history", output)

    def test_superseded_page_with_history_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            mnemo = _make_wiki(
                pathlib.Path(tmp),
                {"wiki/entities/tool-old.md": SUPERSEDED_PAGE_WITH_HISTORY},
            )
            output = _run_lint(mnemo)
        self.assertNotIn("superseded_without_history", output)

    def test_healthy_page_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            mnemo = _make_wiki(
                pathlib.Path(tmp),
                {"wiki/entities/tool-active.md": HEALTHY_PAGE},
            )
            output = _run_lint(mnemo)
        self.assertNotIn("superseded_without_history", output)

    def test_supersedes_page_without_history_is_flagged(self):
        page = """\
---
title: New Tool
category: entities
tags: [tool]
supersedes: Old Tool
created: 2025-01-01
updated: 2026-01-01
---

# New Tool

> *Type: Tool*

---

## Description

This tool replaced the old one.

## Sources

- [[Some Source]]

## Links

- [[Some Source]]
"""
        with tempfile.TemporaryDirectory() as tmp:
            mnemo = _make_wiki(
                pathlib.Path(tmp),
                {"wiki/entities/tool-new.md": page},
            )
            output = _run_lint(mnemo)
        self.assertIn("superseded_without_history", output)


class TestParseFrontmatterTemporalFields(unittest.TestCase):
    def test_parses_superseded_by(self):
        fm = parse_frontmatter(SUPERSEDED_PAGE)
        self.assertEqual(fm.get("superseded_by"), "New Tool")

    def test_parses_supersedes(self):
        text = "---\ntitle: New Tool\nsupersedes: Old Tool\n---\n# New Tool\n"
        fm = parse_frontmatter(text)
        self.assertEqual(fm.get("supersedes"), "Old Tool")

    def test_healthy_page_has_no_superseded_by(self):
        fm = parse_frontmatter(HEALTHY_PAGE)
        self.assertNotIn("superseded_by", fm)


if __name__ == "__main__":
    unittest.main()
