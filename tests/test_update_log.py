#!/usr/bin/env python3
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).parent.parent / "scripts" / "update_log.py"


def _run(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True
    )


def _make_vault(root: pathlib.Path) -> pathlib.Path:
    vault = root / "vault"
    vault.mkdir()
    (vault / "wiki").mkdir()
    return vault


class TestAppendToEmptyLog(unittest.TestCase):
    def test_creates_log_with_header_and_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault), "--file", "wiki/sources/foo.md", "--op", "ingest")
            self.assertEqual(r.returncode, 0)
            log = (vault / "log.md").read_text()
            self.assertIn("# Log", log)
            self.assertIn("wiki/sources/foo.md", log)
            self.assertIn("ingest", log)


class TestAppendPreservesExisting(unittest.TestCase):
    def test_preserves_previous_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            (vault / "log.md").write_text("# Log\n- old | 2026-01-01T00:00:00+00:00 | ingest\n")
            r = _run("--vault", str(vault), "--file", "wiki/sources/bar.md", "--op", "generated")
            self.assertEqual(r.returncode, 0)
            log = (vault / "log.md").read_text()
            self.assertIn("old", log)
            self.assertIn("bar.md", log)


class TestTimestampFormat(unittest.TestCase):
    def test_custom_timestamp_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault), "--file", "wiki/x.md", "--op", "init",
                     "--timestamp", "2026-04-26T10:00:00+00:00")
            self.assertEqual(r.returncode, 0)
            log = (vault / "log.md").read_text()
            self.assertIn("2026-04-26T10:00:00+00:00", log)

    def test_auto_timestamp_is_iso8601(self):
        import re
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault), "--file", "wiki/x.md", "--op", "ingest")
            self.assertEqual(r.returncode, 0)
            log = (vault / "log.md").read_text()
            self.assertRegex(log, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00")


class TestFileValidation(unittest.TestCase):
    def test_exit_1_on_pipe_in_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault), "--file", "wiki/foo.md | bad", "--op", "ingest")
            self.assertEqual(r.returncode, 1)
            self.assertIn("error", r.stderr)

    def test_exit_1_on_newline_in_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault), "--file", "wiki/foo.md\nbad", "--op", "ingest")
            self.assertEqual(r.returncode, 1)
            self.assertIn("error", r.stderr)


class TestInvalidOp(unittest.TestCase):
    def test_exit_1_on_invalid_op(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            r = _run("--vault", str(vault), "--file", "wiki/x.md", "--op", "badop")
            self.assertEqual(r.returncode, 1)
            self.assertIn("invalid op", r.stderr)


class TestVaultNotFound(unittest.TestCase):
    def test_exit_1_when_vault_missing(self):
        r = _run("--vault", "/nonexistent/path", "--file", "wiki/x.md", "--op", "ingest")
        self.assertEqual(r.returncode, 1)


class TestLintHeader(unittest.TestCase):
    def test_lint_op_writes_header_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            (vault / "log.md").write_text("# Log\n")
            r = _run("--vault", str(vault), "--op", "lint",
                     "--timestamp", "2026-04-26T12:00:00+00:00")
            self.assertEqual(r.returncode, 0)
            log = (vault / "log.md").read_text()
            self.assertIn("# Last lint: 2026-04-26T12:00:00+00:00", log)

    def test_lint_op_replaces_existing_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = _make_vault(pathlib.Path(tmp))
            (vault / "log.md").write_text("# Last lint: 2026-01-01T00:00:00+00:00\n# Log\n")
            r = _run("--vault", str(vault), "--op", "lint",
                     "--timestamp", "2026-04-26T12:00:00+00:00")
            self.assertEqual(r.returncode, 0)
            log = (vault / "log.md").read_text()
            self.assertIn("2026-04-26T12:00:00+00:00", log)
            self.assertNotIn("2026-01-01", log)


if __name__ == "__main__":
    unittest.main()
