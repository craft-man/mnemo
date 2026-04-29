#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run_script(script: pathlib.Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], text=True, capture_output=True, env=env)


class TestCreateVault(unittest.TestCase):
    def test_creates_project_vault(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "project"
            project.mkdir()
            result = run_script(ROOT / "skills/init/scripts/create_vault.py", "--project-root", str(project))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "created")
            vault = project / ".mnemo" / "project"
            self.assertTrue((vault / "raw").is_dir())
            self.assertTrue((vault / "wiki" / "sources").is_dir())
            self.assertTrue((vault / "SCHEMA.md").exists())

    def test_existing_vault_reports_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "project"
            vault = project / ".mnemo" / "project"
            vault.mkdir(parents=True)
            result = run_script(ROOT / "skills/init/scripts/create_vault.py", "--project-root", str(project))
            self.assertEqual(json.loads(result.stdout)["status"], "already_exists")


class TestSchemaAndProfileScripts(unittest.TestCase):
    def test_write_schema_materializes_validated_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp) / ".mnemo" / "project"
            vault.mkdir(parents=True)
            result = run_script(
                ROOT / "skills/schema/scripts/write_schema.py",
                "--vault",
                str(vault),
                "--domain",
                "Research notes for testing.",
                "--entity-types",
                "Person, Dataset, Tool",
                "--concept-categories",
                "Question, Method, Finding",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            schema = (vault / "SCHEMA.md").read_text(encoding="utf-8")
            self.assertIn("Research notes for testing.", schema)
            self.assertIn("**Dataset**", schema)
            self.assertIn("**Finding**", schema)

    def test_write_profile_creates_once_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = pathlib.Path(tmp) / "home"
            args = [
                "--home",
                str(home),
                "--role",
                "Researcher",
                "--technical-level",
                "CLI comfortable",
                "--language",
                "English",
                "--domains",
                "testing",
                "--proactivity",
                "Moderate",
                "--register",
                "Direct",
            ]
            script = ROOT / "skills/onboard/scripts/write_profile.py"
            first = run_script(script, *args)
            second = run_script(script, *args)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(first.stdout)["status"], "created")
            self.assertEqual(json.loads(second.stdout)["status"], "unchanged")


class TestSearchGitignoreBriefMemory(unittest.TestCase):
    def test_configure_search_bm25(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = pathlib.Path(tmp) / "project" / ".mnemo" / "project"
            vault.mkdir(parents=True)
            result = run_script(ROOT / "skills/init/scripts/configure_search.py", "--vault", str(vault), "--backend", "bm25")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((vault / "config.json").read_text(encoding="utf-8"))["search_backend"], "bm25")

    def test_update_gitignore_requires_accept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "project"
            project.mkdir()
            script = ROOT / "skills/init/scripts/update_gitignore.py"
            skipped = run_script(script, "--project-root", str(project))
            updated = run_script(script, "--project-root", str(project), "--accept")
            self.assertEqual(json.loads(skipped.stdout)["status"], "skipped")
            self.assertEqual(json.loads(updated.stdout)["status"], "updated")
            self.assertIn(".mnemo/", (project / ".gitignore").read_text(encoding="utf-8"))

    def test_session_brief_and_agent_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "project"
            vault = project / ".mnemo" / "project"
            vault.mkdir(parents=True)
            (vault / "wiki").mkdir()
            (vault / "index.md").write_text("# Index\n", encoding="utf-8")
            (vault / "log.md").write_text("# Log\n", encoding="utf-8")
            (vault / "config.json").write_text('{"search_backend":"bm25"}', encoding="utf-8")
            brief = run_script(ROOT / "skills/init/scripts/update_session_brief.py", "--vault", str(vault))
            memory = run_script(ROOT / "skills/init/scripts/wire_agent_memory.py", "--project-root", str(project), "--project-name", "project")
            self.assertEqual(brief.returncode, 0, brief.stderr)
            self.assertEqual(memory.returncode, 0, memory.stderr)
            self.assertTrue((vault / "SESSION_BRIEF.md").exists())
            self.assertIn("## mnemo", (project / "AGENTS.md").read_text(encoding="utf-8"))


class TestGraphifyScript(unittest.TestCase):
    def test_integrates_existing_graphify_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = pathlib.Path(tmp) / "project"
            vault = project / ".mnemo" / "project"
            graph_dir = project / "graphify-out"
            (vault / "wiki" / "synthesis").mkdir(parents=True)
            graph_dir.mkdir(parents=True)
            (vault / "index.md").write_text("# Index\n\n## Synthesis\n", encoding="utf-8")
            (vault / "log.md").write_text("# Log\n", encoding="utf-8")
            (graph_dir / "GRAPH_REPORT.md").write_text("# Report\n", encoding="utf-8")
            (graph_dir / "graph.json").write_text(json.dumps({"nodes": [{"id": "a"}], "edges": []}), encoding="utf-8")
            result = run_script(ROOT / "skills/graphify/scripts/run_graphify.py", "--project-root", str(project), "--vault", str(vault), "--skip-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((vault / "wiki" / "synthesis" / "codebase-graph-report.md").exists())
            self.assertIn("Codebase Graph Report", (vault / "index.md").read_text(encoding="utf-8"))


class TestStaticSkillContract(unittest.TestCase):
    def test_init_skill_contract_mentions_scripts_and_delegation(self) -> None:
        content = (ROOT / "skills/init/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: mnemo-init", content)
        self.assertIn("skills/init/scripts/create_vault.py", content)
        self.assertIn("skills/schema/scripts/write_schema.py", content)
        self.assertIn("skills/onboard/scripts/write_profile.py", content)
        self.assertIn("skills/graphify/scripts/run_graphify.py", content)
        self.assertIn("Delegate to the schema skill", content)
        self.assertIn("delegate to the onboard skill", content)
        self.assertIn("delegate to the graphify skill", content)
        self.assertIn("mandatory schema setup", content)
        self.assertIn("mandatory onboarding", content)

    def test_init_skill_has_no_optional_handoffs(self) -> None:
        content = (ROOT / "skills/init/SKILL.md").read_text(encoding="utf-8")
        forbidden = [
            "Run `/mnemo:schema`",
            "Run `/mnemo:onboard`",
            "Run `/mnemo:graphify`",
            "wait for the user to run",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, content)

    def test_public_wrapper_removed_and_command_renamed(self) -> None:
        self.assertFalse((ROOT / "scripts/init_mnemo.py").exists())
        self.assertFalse((ROOT / "commands/mnemo/init.md").exists())
        self.assertTrue((ROOT / "commands/mnemo/mnemo-init.md").exists())

    def test_scripts_are_under_skill_scripts_directories(self) -> None:
        expected = [
            ROOT / "skills/init/scripts/create_vault.py",
            ROOT / "skills/init/scripts/configure_search.py",
            ROOT / "skills/init/scripts/update_gitignore.py",
            ROOT / "skills/init/scripts/update_session_brief.py",
            ROOT / "skills/init/scripts/wire_agent_memory.py",
            ROOT / "skills/schema/scripts/write_schema.py",
            ROOT / "skills/onboard/scripts/write_profile.py",
            ROOT / "skills/graphify/scripts/run_graphify.py",
        ]
        for script in expected:
            self.assertTrue(script.exists(), script)
            help_result = run_script(script, "--help")
            self.assertEqual(help_result.returncode, 0, help_result.stderr)


if __name__ == "__main__":
    unittest.main()
