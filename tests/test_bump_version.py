#!/usr/bin/env python3
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "bump_version.py"


def _copy_repo_subset(dest: pathlib.Path) -> None:
    for rel in [
        "scripts/bump_version.py",
        "README.md",
        "CHANGELOG.md",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
    ]:
        src = ROOT / rel
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)

    skills_src = ROOT / "skills"
    skills_dest = dest / "skills"
    for skill_file in skills_src.glob("*/SKILL.md"):
        target = skills_dest / skill_file.relative_to(skills_src)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_file, target)


def _run(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo / "scripts" / "bump_version.py"), *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )


class TestBumpVersion(unittest.TestCase):
    def test_updates_both_plugin_manifests(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _copy_repo_subset(repo)

            for rel in [".claude-plugin/plugin.json", ".codex-plugin/plugin.json"]:
                path = repo / rel
                data = json.loads(path.read_text(encoding="utf-8"))
                data["version"] = "0.16.0"
                path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            result = _run(repo, "0.16.1")
            self.assertEqual(result.returncode, 0, result.stderr)

            claude = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
            codex = json.loads((repo / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(claude["version"], "0.16.1")
            self.assertEqual(codex["version"], "0.16.1")

    def test_fails_when_plugin_versions_are_out_of_sync(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            _copy_repo_subset(repo)

            claude_path = repo / ".claude-plugin" / "plugin.json"
            codex_path = repo / ".codex-plugin" / "plugin.json"

            claude = json.loads(claude_path.read_text(encoding="utf-8"))
            codex = json.loads(codex_path.read_text(encoding="utf-8"))
            claude["version"] = "0.16.0"
            codex["version"] = "0.15.0"
            claude_path.write_text(json.dumps(claude, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            codex_path.write_text(json.dumps(codex, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            result = _run(repo, "0.16.1")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("out of sync", result.stderr)
            self.assertIn(".claude-plugin/plugin.json=0.16.0", result.stderr)
            self.assertIn(".codex-plugin/plugin.json=0.15.0", result.stderr)


if __name__ == "__main__":
    unittest.main()
