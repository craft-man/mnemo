#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "update_index.py"


def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )


def _make_vault(root: pathlib.Path, pages: dict[str, str] | None = None) -> pathlib.Path:
    """Create a minimal vault. pages = {relative_path: content}."""
    vault = root / "vault"
    for d in ["wiki/sources", "wiki/entities", "wiki/concepts", "wiki/synthesis",
              "wiki/indexes", "wiki/activity"]:
        (vault / d).mkdir(parents=True)
    if pages:
        for rel, content in pages.items():
            p = vault / "wiki" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
    return vault


SAMPLE_PAGE = """\
---
title: Redis — In-Memory Store
category: entities
summary: Fast key-value store used as cache and message broker
updated: 2026-04-20
---

# Redis — In-Memory Store

Body text.
"""


class TestEmptyVault(unittest.TestCase):
    def test_generates_valid_index_with_no_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("# Index", index)


class TestRegenerateFromFrontmatter(unittest.TestCase):
    def test_page_appears_in_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"entities/tool-redis.md": SAMPLE_PAGE})
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("Redis — In-Memory Store", index)
            self.assertIn("wiki/entities/tool-redis.md", index)
            self.assertIn("Fast key-value store", index)

    def test_updated_date_appears(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"entities/tool-redis.md": SAMPLE_PAGE})
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("upd 2026-04-20", index)


class TestTitleInference(unittest.TestCase):
    def test_infers_title_from_filename_when_no_frontmatter(self):
        page = "# My Page\n\nBody.\n"
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"concepts/my-concept.md": page})
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("My Concept", index)


class TestExclusions(unittest.TestCase):
    def test_excludes_activity_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"activity/2026-04-26.md": SAMPLE_PAGE})
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertNotIn("Redis", index)

    def test_excludes_indexes_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"indexes/entities.md": SAMPLE_PAGE})
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertNotIn("Redis", index)

    def test_excludes_index_md_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            (vault / "wiki" / "index.md").write_text("# Index\n")
            r = _run("--vault", str(vault))
            self.assertEqual(r.returncode, 0)


class TestDryRun(unittest.TestCase):
    def test_dry_run_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"sources/foo.md": SAMPLE_PAGE})
            original = "# Index\n"
            (vault / "index.md").write_text(original, encoding="utf-8")
            r = _run("--vault", str(vault), "--dry-run")
            self.assertEqual(r.returncode, 0)
            self.assertEqual((vault / "index.md").read_text(encoding="utf-8"), original)

    def test_dry_run_prints_to_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"sources/foo.md": SAMPLE_PAGE})
            r = _run("--vault", str(vault), "--dry-run")
            self.assertEqual(r.returncode, 0)
            self.assertIn("# Index", r.stdout)


class TestJsonOutput(unittest.TestCase):
    def test_json_flag_emits_parseable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp), {"entities/tool-redis.md": SAMPLE_PAGE})
            r = _run("--vault", str(vault), "--json")
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["total_pages"], 1)
            self.assertIn("entities", data["by_category"])


class TestShardingThreshold(unittest.TestCase):
    def test_sharding_at_150_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            for i in range(151):
                cat = ["sources", "entities", "concepts", "synthesis"][i % 4]
                content = f"---\ntitle: Page {i}\ncategory: {cat}\n---\n# Page {i}\n"
                (vault / "wiki" / cat / f"page-{i}.md").write_text(content)
            r = _run("--vault", str(vault), "--json")
            self.assertEqual(r.returncode, 0)
            data = json.loads(r.stdout)
            self.assertTrue(data["sharded"])
            self.assertTrue((vault / "wiki" / "indexes" / "sources.md").exists())
            index = (vault / "index.md").read_text(encoding="utf-8")
            self.assertIn("wiki/indexes/sources.md", index)


class TestVaultNotFound(unittest.TestCase):
    def test_exit_1_when_vault_missing(self):
        r = _run("--vault", "/nonexistent/path")
        self.assertEqual(r.returncode, 1)


if __name__ == "__main__":
    unittest.main()
