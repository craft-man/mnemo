#!/usr/bin/env python3
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def make_vault(root: pathlib.Path, with_brief: bool = True) -> pathlib.Path:
    vault = root / ".mnemo" / root.name
    vault.mkdir(parents=True, exist_ok=True)
    (vault / "index.md").write_text("# Index\n", encoding="utf-8")
    (vault / "log.md").write_text("# Log\n", encoding="utf-8")
    (vault / "config.json").write_text('{"search_backend": "bm25"}', encoding="utf-8")
    if with_brief:
        (vault / "SESSION_BRIEF.md").write_text("# Session Brief\n\nRead this file first.\n", encoding="utf-8")
    return vault


def run_show(vault: pathlib.Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "show_session_brief.py"), "--vault", str(vault), *extra],
        text=True,
        capture_output=True,
    )


class TestShowSessionBrief(unittest.TestCase):
    def test_prints_minimal_vault_brief(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project")
            result = run_show(vault)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("# Session Brief", result.stdout)
            self.assertEqual(result.stderr, "")

    def test_missing_brief_exits_nonzero_with_regeneration_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project", with_brief=False)
            result = run_show(vault)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing session brief", result.stderr)
            self.assertIn("python scripts/update_session_brief.py --vault", result.stderr)

    def test_stale_brief_warns_but_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project")
            brief = vault / "SESSION_BRIEF.md"
            old = time.time() - 60
            os.utime(brief, (old, old))
            result = run_show(vault)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("# Session Brief", result.stdout)
            self.assertIn("may be stale", result.stderr)
            self.assertIn("Regenerate with:", result.stderr)

    def test_code_appends_graph_report_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "project"
            vault = make_vault(root)
            graph_dir = root / "graphify-out"
            graph_dir.mkdir()
            (graph_dir / "GRAPH_REPORT.md").write_text("# Graph Report\n\nCode map.\n", encoding="utf-8")
            result = run_show(vault, "--code")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("# Session Brief", result.stdout)
            self.assertIn("# Codebase Context", result.stdout)
            self.assertIn("# Graph Report", result.stdout)

    def test_code_notes_missing_graph_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = make_vault(pathlib.Path(tmp) / "project")
            result = run_show(vault, "--code")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("graphify-out/GRAPH_REPORT.md not present", result.stdout)


class TestContextDocsStructure(unittest.TestCase):
    def test_command_and_skill_exist_with_read_only_guardrails(self):
        command = ROOT / "commands" / "mnemo" / "context.md"
        skill = ROOT / "skills" / "context" / "SKILL.md"
        self.assertTrue(command.exists())
        self.assertTrue(skill.exists())
        content = skill.read_text(encoding="utf-8")
        self.assertIn("Never read `wiki/**/*.md`", content)
        self.assertIn("Do not write, edit, create, delete, move, or regenerate any file.", content)

    def test_readme_mentions_context_command_and_cli(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("/mnemo:context", readme)
        self.assertIn("scripts/show_session_brief.py", readme)


if __name__ == "__main__":
    unittest.main()
