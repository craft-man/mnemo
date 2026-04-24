#!/usr/bin/env python3
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
from init_mnemo import create_structure, guard, update_gitignore, prompt_qmd, prompt_graphify, DIRS


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
            # inputs: choice=2, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / target.name / "wiki" / "sources").is_dir())

    def test_choice_2_does_not_create_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            fake_home = pathlib.Path(tmp) / "fakehome"
            fake_home.mkdir()
            # inputs: choice=2, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "n", "n", "n"]), \
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
            # choice=3: no qmd, no gitignore, no graphify prompts
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
            # inputs: choice=1, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["1", "n", "n", "n"]), \
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
            # inputs: choice="" (→1), qmd="", graphify="", obsidian=""
            with patch("builtins.input", side_effect=["", "", "", ""]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]), \
                 patch("pathlib.Path.home", return_value=fake_home):
                from init_mnemo import main
                main()
            self.assertTrue((target / ".mnemo" / target.name / "wiki" / "sources").is_dir())
            self.assertTrue((fake_home / ".mnemo" / "wiki" / "sources").is_dir())


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
                prompt_qmd(root)
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "bm25")

    def test_writes_qmd_config_on_yes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with patch("builtins.input", return_value="y"):
                prompt_qmd(root)
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "qmd")
            self.assertEqual(config["qmd_collection"], "mnemo-wiki")

    def test_writes_bm25_config_on_default_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            with patch("builtins.input", return_value=""):
                prompt_qmd(root)
            config = json.loads((root / "config.json").read_text(encoding="utf-8"))
            self.assertEqual(config["search_backend"], "bm25")

    def test_main_creates_config_json_for_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            # inputs: choice=2, qmd=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]):
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
            with patch("builtins.input", return_value=""):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_returns_true_when_graphify_installed_and_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value="y"), \
                 patch("shutil.which", return_value="/usr/bin/graphify"), \
                 patch("subprocess.run", return_value=mock_result):
                result = prompt_graphify(target)
            self.assertTrue(result)

    def test_returns_false_when_graphify_installed_but_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 1
            with patch("builtins.input", return_value="y"), \
                 patch("shutil.which", return_value="/usr/bin/graphify"), \
                 patch("subprocess.run", return_value=mock_result):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_shows_install_instructions_when_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            printed = []
            # user says y, then skips install
            with patch("builtins.input", side_effect=["y", "s"]), \
                 patch("shutil.which", return_value=None), \
                 patch("builtins.print", side_effect=lambda *a, **k: printed.append(" ".join(str(x) for x in a))):
                result = prompt_graphify(target)
            self.assertFalse(result)
            combined = " ".join(printed)
            self.assertIn("pip install graphifyy", combined)

    def test_proceeds_after_install_when_graphify_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            # which returns None first (not installed), then path (after install)
            with patch("builtins.input", side_effect=["y", ""]), \
                 patch("shutil.which", side_effect=[None, "/usr/bin/graphify"]), \
                 patch("subprocess.run", return_value=mock_result):
                result = prompt_graphify(target)
            self.assertTrue(result)

    def test_returns_false_if_still_not_found_after_install_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            with patch("builtins.input", side_effect=["y", ""]), \
                 patch("shutil.which", return_value=None):
                result = prompt_graphify(target)
            self.assertFalse(result)

    def test_subprocess_called_with_correct_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            mock_result = MagicMock()
            mock_result.returncode = 0
            with patch("builtins.input", return_value="y"), \
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
            (target / ".git").mkdir()
            # inputs: choice=2, qmd=n, gitignore=y, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "n", "y", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]):
                from init_mnemo import main
                main()
            self.assertIn(".mnemo/", (target / ".gitignore").read_text(encoding="utf-8"))

    def test_main_skips_gitignore_when_no_git_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            # inputs: choice=2, qmd=n, graphify=n, obsidian=n (no gitignore prompt — no .git)
            with patch("builtins.input", side_effect=["2", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]):
                from init_mnemo import main
                main()
            self.assertFalse((target / ".gitignore").exists())

    def test_main_skips_gitignore_on_n_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp)
            (target / ".git").mkdir()
            # inputs: choice=2, qmd=n, gitignore=n, graphify=n, obsidian=n
            with patch("builtins.input", side_effect=["2", "n", "n", "n", "n"]), \
                 patch("sys.argv", ["init_mnemo.py", str(target)]):
                from init_mnemo import main
                main()
            self.assertFalse((target / ".gitignore").exists())


if __name__ == "__main__":
    unittest.main()
