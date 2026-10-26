"""End-to-end test of the runner on a throwaway repository with a UTF-8 truncation bug."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bugbench import runner, tasks

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "bugbench", "GIT_AUTHOR_EMAIL": "bugbench@example.com",
    "GIT_COMMITTER_NAME": "bugbench", "GIT_COMMITTER_EMAIL": "bugbench@example.com",
}

BUGGY = '''def truncate(text, max_bytes):
    """Encode text as UTF-8 and cut it to max_bytes without splitting a character."""
    return text.encode("utf-8")[:max_bytes]
'''
FIXED = '''def truncate(text, max_bytes):
    """Encode text as UTF-8 and cut it to max_bytes without splitting a character."""
    return text.encode("utf-8")[:max_bytes].decode("utf-8", "ignore").encode("utf-8")
'''
HIDDEN_TEST = '''import unittest

from textutil import truncate


class TruncateTest(unittest.TestCase):
    def test_cjk(self):
        self.assertEqual(truncate("日本語", 4), "日".encode("utf-8"))
'''


def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, env=GIT_ENV, check=True, capture_output=True,
                          text=True, encoding="utf-8").stdout


def write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


class RunnerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="bugbench-test-"))
        repo = cls.tmp / "upstream"
        repo.mkdir()
        git("init", "-q", "-b", "main", cwd=repo)
        git("config", "core.autocrlf", "false", cwd=repo)
        write(repo / "textutil.py", BUGGY)
        git("add", ".", cwd=repo)
        git("commit", "-q", "-m", "initial", cwd=repo)
        base = git("rev-parse", "HEAD", cwd=repo).strip()

        task_dir = cls.tmp / "tasks" / "fixture-1"
        task_dir.mkdir(parents=True)
        write(repo / "textutil.py", FIXED)
        write(task_dir / "gold.patch", git("diff", cwd=repo))
        git("checkout", "--", "textutil.py", cwd=repo)
        write(repo / "test_truncate.py", HIDDEN_TEST)
        git("add", "-N", "test_truncate.py", cwd=repo)
        write(task_dir / "test.patch", git("diff", cwd=repo))
        git("reset", "-q", cwd=repo)
        (repo / "test_truncate.py").unlink()

        write(task_dir / "problem.md", "# truncate() splits multi-byte characters\n")
        task = {
            "id": "fixture-1",
            "title": "truncate() splits multi-byte characters",
            "repo": repo.as_uri(),
            "upstream_pr": "https://example.com/pr/1",
            "upstream_status": "open",
            "base_commit": base,
            "language": "python",
            "category": "multibyte-text",
            "license": "MIT",
            "environment": {"reproduces_on": ["any"]},
            "test_command": ["{python}", "-m", "unittest", "-q", "test_truncate"],
            "regression_command": ["{python}", "-c", "import textutil; assert textutil.truncate('abc', 2) == b'ab'"],
            "hidden_tests": {"source": "benchmark", "tests": ["test_truncate.py"]},
            "gold_patch": "gold.patch",
            "test_patch": "test.patch",
            "timeout_sec": 120,
        }
        write(task_dir / "task.json", json.dumps(task, indent=2))
        cls.task = tasks.load("fixture-1", cls.tmp / "tasks")
        cls.work = cls.tmp / "work"

    @classmethod
    def tearDownClass(cls):
        def onerror(func, path, _exc):
            os.chmod(path, 0o700)  # git marks pack files read-only on Windows
            func(path)
        shutil.rmtree(cls.tmp, onerror=onerror)

    def _patch(self, name: str, text: str) -> Path:
        path = self.tmp / name
        write(path, text)
        return path

    def test_validate(self):
        record = runner.validate(self.task, work_root=self.work, write=False)
        self.assertTrue(record["ok"], record)
        self.assertEqual(record["base"]["status"], "unresolved")
        self.assertEqual(record["gold"]["status"], "resolved")

    def test_gold_patch_as_candidate(self):
        result = runner.run(self.task, "candidate", self.task.dir / "gold.patch", work_root=self.work)
        self.assertTrue(result["resolved"], result["log_tail"])

    def test_empty_candidate(self):
        result = runner.run(self.task, "candidate", self._patch("empty.patch", ""), work_root=self.work)
        self.assertEqual(result["status"], "unresolved")

    def test_patch_that_does_not_apply(self):
        bad = "diff --git a/textutil.py b/textutil.py\n--- a/textutil.py\n+++ b/textutil.py\n@@ -1 +1 @@\n-nothing like this\n+x\n"
        result = runner.run(self.task, "candidate", self._patch("bad.patch", bad), work_root=self.work)
        self.assertEqual(result["status"], "patch_failed")

    def test_candidate_cannot_replace_hidden_tests(self):
        # A candidate that ships its own passing test_truncate.py gets the hidden one instead.
        fake = HIDDEN_TEST.replace('"日".encode("utf-8")', 'truncate("日本語", 4)')
        repo = self.tmp / "scratch"
        if repo.exists():
            shutil.rmtree(repo)
        repo.mkdir()
        git("init", "-q", cwd=repo)
        write(repo / "test_truncate.py", fake)
        git("add", "-N", "test_truncate.py", cwd=repo)
        cheat = git("diff", cwd=repo)
        result = runner.run(self.task, "candidate", self._patch("cheat.patch", cheat), work_root=self.work)
        self.assertEqual(result["status"], "unresolved")

    def test_regression_failure_is_unresolved(self):
        breaking = self.task.gold_patch_text.replace('.encode("utf-8")\n', '.encode("utf-8")[:1]\n')
        self.assertNotEqual(breaking, self.task.gold_patch_text)
        result = runner.run(self.task, "candidate", self._patch("breaking.patch", breaking), work_root=self.work)
        self.assertEqual(result["status"], "unresolved")
        self.assertNotEqual(result["regression_exit"], 0)


class PlatformTest(unittest.TestCase):
    def test_current_platform(self):
        self.assertIn(runner.current_platform(), tasks.PLATFORMS)

    def test_python_is_usable(self):
        self.assertTrue(Path(sys.executable).exists())


if __name__ == "__main__":
    unittest.main()
