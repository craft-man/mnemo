#!/usr/bin/env python3
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "skills" / "init"))
from init_mnemo import create_structure, guard, update_gitignore, prompt_qmd, prompt_graphify, prompt_onboard, wire_agent_memory, DIRS


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
            (target / ".mnemo" / target.name).mkdir(parents=True)
            self.assertTrue(guard(target))

    def test_returns_false_when_mnemo_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(guard(pathlib.Path(tmp)))


class TestMainProjectOnly(unittest.TestCase):
    def test_choice_2_creates_local_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # inputs: choice=2, schema prompts, onboard six answers + confirm, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / target.name / "wiki" / "sources").is_dir())
            schema = (target / ".mnemo" / target.name / "SCHEMA.md").read_text(encoding="utf-8")
            self.assertIn("Project notes", schema)

    def test_choice_2_does_not_create_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # inputs: choice=2, schema prompts, onboarding skipped because profile exists, qmd=n, graphify=n, obsidian=n
            (fake_home / ".mnemo" / "wiki" / "entities").mkdir(parents=True)
            (fake_home / ".mnemo" / "wiki" / "entities" / "person-user.md").write_text("# User Profile\n", encoding="utf-8")
            with patch("builtins.input", side_effect=["2", "", "", "", "n", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((fake_home / ".mnemo").exists())


class TestMainGlobalOnly(unittest.TestCase):
    def test_choice_3_creates_global_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # choice=3: no qmd, no gitignore, no graphify prompts
            with patch("builtins.input", side_effect=["3", "1", "2", "English", "testing", "2", "1", ""]), \
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
            # inputs: choice=1, schema prompts, onboard six answers + confirm, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["1", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / target.name / "wiki" / "sources").is_dir())
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "sources").is_dir())

    def test_default_choice_is_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # inputs: choice="" (->1), schema defaults, onboard defaults, qmd default, graphify default, obsidian default
            with patch("builtins.input", side_effect=["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home), \
                 patch("shutil.which", return_value=None), \
                 patch("init_mnemo._install_qmd", return_value=False), \
                 patch("init_mnemo._install_graphify", return_value=False):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / target.name / "wiki" / "sources").is_dir())
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "sources").is_dir())

    def test_main_minimal_answers_completes_config_profile_schema_and_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()

            with patch("builtins.input", side_effect=["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home), \
                 patch("shutil.which", return_value=None), \
                 patch("init_mnemo._install_qmd", return_value=False) as install_qmd, \
                 patch("init_mnemo._install_graphify", return_value=False) as install_graphify:
                from init_mnemo import main
                main()

            local_root = target / ".mnemo" / target.name
            self.assertTrue((local_root / "SCHEMA.md").exists())
            self.assertIn("General knowledge base for this project.", (local_root / "SCHEMA.md").read_text(encoding="utf-8"))
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "entities" / "person-user.md").exists())
            config = json.loads((local_root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "bm25")
            self.assertTrue((target / "AGENTS.md").exists())
            self.assertIn(".mnemo/" + target.name + "/wiki/", (target / "AGENTS.md").read_text(encoding="utf-8"))
            install_qmd.assert_called_once()
            install_graphify.assert_called_once()


class TestGuardClause(unittest.TestCase):
    def test_guard_prints_message_and_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".mnemo" / target.name).mkdir(parents=True)
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


class TestPromptQmd(unittest.TestCase):
    def test_writes_bm25_config_on_no(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with patch("builtins.input", return_value="n"):
                prompt_qmd(root, "project")
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "bm25")

    def test_writes_qmd_config_on_yes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value="y"), \
                 patch("shutil.which", return_value="/usr/bin/qmd"), \
                 patch("subprocess.run", return_value=mock_result):
                prompt_qmd(root, "project")
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "qmd")
            self.assertEqual(config["qmd_collection"], "mnemo-wiki")

    def test_auto_installs_qmd_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            install_result = MagicMock()
            install_result.returncode = 0
            collection_result = MagicMock()
            collection_result.returncode = 0
            with patch("builtins.input", side_effect=["y"]), \
                 patch("shutil.which", side_effect=[None, "C:/bin/npm", None, "C:/bin/qmd", "C:/bin/qmd"]), \
                 patch("subprocess.run", side_effect=[install_result, collection_result]) as mock_run:
                prompt_qmd(root, "project")
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "qmd")
            self.assertEqual(mock_run.call_args_list[0].args[0], ["npm", "install", "-g", "@tobilu/qmd"])
            self.assertEqual(mock_run.call_args_list[1].args[0], ["qmd", "collection", "add", "mnemo-wiki", ".mnemo/project/wiki", "**/*.md"])

    def test_writes_qmd_config_on_default_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value="/usr/bin/qmd"), \
                 patch("subprocess.run", return_value=mock_result):
                prompt_qmd(root, "project")
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "qmd")

    def test_default_empty_attempts_qmd_install_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value=None), \
                 patch("init_mnemo._install_qmd", return_value=False) as install_qmd:
                prompt_qmd(root, "project")
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "bm25")
            install_qmd.assert_called_once()

    def test_main_creates_config_json_for_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # inputs: choice=2, schema prompts, onboard six answers + confirm, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / target.name / "config.json").exists())


class TestPromptGraphify(unittest.TestCase):
    def test_returns_false_on_no(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            with patch("builtins.input", return_value="n"):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_returns_false_on_default_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            with patch("builtins.input", return_value="n"):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_returns_true_when_graphify_installed_and_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value="/usr/bin/graphify"), \
                 patch("subprocess.run", return_value=mock_result):
                result = prompt_graphify(target)
            self.assertTrue(result)

    def test_returns_false_when_graphify_installed_but_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 1
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value="/usr/bin/graphify"), \
                 patch("subprocess.run", return_value=mock_result):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_reports_graphify_not_enabled_when_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            printed = []
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value=None), \
                 patch("init_mnemo._install_graphify", return_value=False), \
                 patch("builtins.print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))):
                result = prompt_graphify(target)
            self.assertFalse(result)
            combined = " ".join(printed)
            self.assertIn("graphify still not found -- codebase graph mapping was not enabled.", combined)

    def test_proceeds_after_install_when_graphify_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            install_result = MagicMock()
            install_result.returncode = 0
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", side_effect=[None, "C:/bin/graphify", "C:/bin/graphify"]), \
                 patch("subprocess.run", side_effect=[install_result, install_result, mock_result]):
                result = prompt_graphify(target)
            self.assertTrue(result)

    def test_default_empty_attempts_graphify_install_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value=None), \
                 patch("init_mnemo._install_graphify", return_value=False) as install_graphify:
                result = prompt_graphify(target)
            self.assertFalse(result)
            install_graphify.assert_called_once()

    def test_returns_false_if_still_not_found_after_install_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", side_effect=[None, None, None]), \
                 patch("subprocess.run", return_value=MagicMock(returncode=0)):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_subprocess_called_with_correct_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value=""), \
                 patch("shutil.which", return_value="/usr/bin/graphify"), \
                 patch("subprocess.run", return_value=mock_result) as mock_run:
                prompt_graphify(target)
            mock_run.assert_called_once_with(["graphify", "."], cwd=target)


class TestUpdateGitignore(unittest.TestCase):
    def test_creates_gitignore_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            update_gitignore(target)
            content = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn(".mnemo/", content)

    def test_appends_to_existing_gitignore(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            update_gitignore(target)
            content = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("node_modules/", content)
            self.assertIn(".mnemo/", content)

    def test_idempotent_when_entry_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".gitignore").write_text(".mnemo/\n", encoding="utf-8")
            update_gitignore(target)
            content = (target / ".gitignore").read_text(encoding="utf-8")
            self.assertEqual(content.count(".mnemo/"), 1)

    def test_main_offers_gitignore_when_git_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            (target / ".git").mkdir()
            # inputs: choice=2, schema prompts, onboard six answers + confirm, qmd=n, gitignore=y, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "y", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertIn(".mnemo/", (target / ".gitignore").read_text(encoding="utf-8"))

    def test_main_skips_gitignore_when_no_git_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # inputs: choice=2, schema prompts, onboard six answers + confirm, qmd=n, graphify=n, obsidian=n (no gitignore prompt)
            with patch("builtins.input", side_effect=["2", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertFalse((target / ".gitignore").exists())

    def test_main_skips_gitignore_on_n_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            (target / ".git").mkdir()
            # inputs: choice=2, schema prompts, onboard six answers + confirm, qmd=n, gitignore=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertFalse((target / ".gitignore").exists())


class TestAgentMemoryWiring(unittest.TestCase):
    def test_prefers_existing_claude_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / "CLAUDE.md").write_text("# Project Instructions\n", encoding="utf-8")

            wired = wire_agent_memory(target, "demo-project", graphify_done=False)

            self.assertEqual(wired, "CLAUDE.md")
            content = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("## mnemo", content)
            self.assertIn(".mnemo/demo-project/SESSION_BRIEF.md", content)
            settings = json.loads((target / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
            self.assertIn("hooks", settings)
            self.assertIn("Stop", settings["hooks"])

    def test_creates_agents_md_when_no_agent_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)

            wired = wire_agent_memory(target, "demo-project", graphify_done=False)

            self.assertEqual(wired, "AGENTS.md")
            content = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("## Knowledge Base (mnemo)", content)
            self.assertIn(".mnemo/demo-project/wiki/", content)

    def test_main_wires_existing_claude_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            (target / "CLAUDE.md").write_text("# Project Instructions\n", encoding="utf-8")
            with patch("builtins.input", side_effect=["2", "", "", "", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            content = (target / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("## mnemo", content)
            self.assertIn(".mnemo/" + target.name + "/SESSION_BRIEF.md", content)


class TestPromptOnboard(unittest.TestCase):
    def test_skips_existing_profile_without_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_home = pathlib.Path(tmp) / "fakehome"
            profile = fake_home / ".mnemo" / "wiki" / "entities" / "person-user.md"
            profile.parent.mkdir(parents=True)
            profile.write_text("# User Profile\n", encoding="utf-8")
            printed = []

            with patch("pathlib.Path.home", return_value=fake_home), \
                 patch("builtins.print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))):
                prompt_onboard()

            self.assertTrue(any("keeping it unchanged" in line for line in printed))


class TestMainCompletionMessage(unittest.TestCase):
    def test_does_not_suggest_schema_as_follow_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            printed = []

            with patch("builtins.input", side_effect=["2", "Project notes", "Person, Tool, Project", "Pattern, Technique, Problem", "", "1", "2", "English", "testing", "2", "1", "", "n", "n", "n"]), \
                 patch("builtins.print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()

            combined = "\n".join(printed)
            forbidden = [
                "Run /mnemo:graphify manually later",
                "Run /mnemo:graphify",
                "Run /mnemo:schema",
                "Run /mnemo:onboard",
                "install manually",
                "manually to retry",
            ]
            for phrase in forbidden:
                self.assertNotIn(phrase, combined)
            self.assertNotIn("run /mnemo:schema", combined.lower())
            self.assertNotIn("run /mnemo:onboard", combined.lower())
            self.assertNotIn("run /mnemo:graphify", combined.lower())
            self.assertIn(f"Add source files to .mnemo/{target.name}/raw/ and run /mnemo:ingest", combined)


class TestInitSkillContract(unittest.TestCase):
    def test_skill_does_not_make_schema_or_onboard_optional_followups(self):
        skill_path = pathlib.Path(__file__).parent.parent / "skills" / "init" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        self.assertIn("mandatory schema setup", content)
        self.assertIn("mandatory onboarding", content)
        self.assertIn("This is part of init, not an optional follow-up", content)
        self.assertIn("Do not add `/mnemo:schema`, `/mnemo:onboard`, `/mnemo:graphify`", content)
        self.assertNotIn("The Python fast path is a filesystem bootstrap", content)
        self.assertNotIn("offers to run `/mnemo:schema` immediately", content)

    def test_skill_does_not_define_manual_handoff_contracts(self):
        skill_path = pathlib.Path(__file__).parent.parent / "skills" / "init" / "SKILL.md"
        content = skill_path.read_text(encoding="utf-8")

        forbidden = [
            "wait for the user to run",
            "show the install command",
            "Run `/mnemo:graphify`",
            "You can run `/mnemo:graphify` anytime",
            "Want me to add a mnemo memory stanza",
            "Want me to add a session-end reminder",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, content)


if __name__ == "__main__":
    unittest.main()
