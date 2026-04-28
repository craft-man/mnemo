#!/usr/bin/env python3
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_stats_vault(tmp: pathlib.Path, pages: int, backend: str) -> pathlib.Path:
    vault = tmp / "vault"
    sources = vault / "wiki" / "sources"
    sources.mkdir(parents=True)
    for i in range(pages):
        (sources / f"page-{i}.md").write_text(f"# Page {i}\n", encoding="utf-8")
    config = {"search_backend": backend}
    if backend == "qmd":
        config["qmd_collection"] = "mnemo-wiki"
    (vault / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return vault


class TestWikiStatsBackendWarnings(unittest.TestCase):
    def run_stats(self, vault: pathlib.Path) -> str:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "wiki_stats.py"), str(vault)],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_small_bm25_has_no_qmd_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.run_stats(make_stats_vault(pathlib.Path(tmp), 3, "bm25"))
            self.assertIn("Search backend: bm25", out)
            self.assertNotIn("qmd recommended", out)

    def test_large_bm25_warns_qmd_recommended(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.run_stats(make_stats_vault(pathlib.Path(tmp), 300, "bm25"))
            self.assertIn("qmd recommended", out)

    def test_qmd_has_no_bm25_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = self.run_stats(make_stats_vault(pathlib.Path(tmp), 300, "qmd"))
            self.assertIn("qmd configured", out)
            self.assertNotIn("BM25 remains available as fallback", out)


if __name__ == "__main__":
    unittest.main()
