#!/usr/bin/env python3
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from update_session_brief import render_brief


ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_vault(root: pathlib.Path) -> pathlib.Path:
    vault = root / ".mnemo" / root.name
    for subdir in ("wiki/sources", "wiki/entities", "wiki/concepts", "wiki/synthesis", "wiki/activity", "wiki/indexes", "raw"):
        (vault / subdir).mkdir(parents=True, exist_ok=True)
    (vault / "index.md").write_text("# Index\n\n## Sources\n\n- [Alpha](wiki/sources/alpha.md)\n", encoding="utf-8")
    (vault / "log.md").write_text("# Log\n- raw/alpha.md | 2026-04-28T10:00:00+00:00 | ingest\n", encoding="utf-8")
    (vault / "config.json").write_text('{"search_backend": "bm25"}', encoding="utf-8")
    (vault / "SCHEMA.md").write_text("# Knowledge Base Schema\n\n## Domain\nTest notes\n", encoding="utf-8")
    return vault


class TestUpdateSessionBrief(unittest.TestCase):
    def test_creates_brief_on_minimal_vault(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "update_session_brief.py"), "--vault", str(vault)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            content = (vault / "SESSION_BRIEF.md").read_text(encoding="utf-8")
            self.assertIn("# Session Brief", content)
            self.assertIn("Read this file first", content)
            self.assertIn("[Alpha](wiki/sources/alpha.md)", content)

    def test_idempotent_output_for_same_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project")
            first = render_brief(vault, None, 8)
            second = render_brief(vault, None, 8)
            self.assertEqual(first, second)

    def test_handles_missing_log_index_and_graphify(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "project"
            vault = root / ".mnemo" / "project"
            (vault / "wiki" / "sources").mkdir(parents=True)
            content = render_brief(vault, "Short summary", 5)
            self.assertIn("No index entries yet", content)
            self.assertIn("No log entries yet", content)
            self.assertIn("Codebase map: not present", content)

    def test_mentions_graph_report_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "project"
            vault = make_vault(root)
            graph_dir = root / "graphify-out"
            graph_dir.mkdir()
            (graph_dir / "GRAPH_REPORT.md").write_text("# Report\n", encoding="utf-8")
            content = render_brief(vault, None, 8)
            self.assertIn("graphify-out/GRAPH_REPORT.md", content)


class TestPublicWrappers(unittest.TestCase):
    def test_wiki_stats_public_wrapper_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project")
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "wiki_stats.py"), str(vault)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Knowledge Base Stats", result.stdout)

    def test_init_public_wrapper_runs_project_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / "project"
            target.mkdir()
            fake_home = pathlib.Path(tmp) / "home"
            fake_home.mkdir()
            env = os.environ.copy()
            env["HOME"] = str(fake_home)
            env["USERPROFILE"] = str(fake_home)
            inputs = "\n".join(["2", "n", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]) + "\n"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "init_mnemo.py"), str(target)],
                input=inputs,
                text=True,
                capture_output=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            vault = target / ".mnemo" / target.name
            self.assertTrue((vault / "wiki" / "sources").is_dir())
            self.assertTrue((vault / "SESSION_BRIEF.md").exists())


if __name__ == "__main__":
    unittest.main()
