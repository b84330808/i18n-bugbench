"""Checks every task in tasks/: metadata, patches, support files, README."""

import json
import re
import unittest

from bugbench import cli, patches, tasks


class TasksTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = tasks.load_all()

    def test_there_are_tasks(self):
        self.assertGreaterEqual(len(self.tasks), 1)

    def test_problem_statements_do_not_point_at_the_fix(self):
        for task in self.tasks:
            text = task.problem_statement
            # Tracebacks in code blocks may name files, as real bug reports do; prose may not.
            prose = re.sub(r"```.*?```", "", text, flags=re.S)
            with self.subTest(task=task.id):
                self.assertGreater(len(text.strip()), 100)
                self.assertNotIn(task.upstream_pr, text)
                self.assertNotIn("/pull/", text)
                # Names of files the gold patch changes would tell the agent where to look.
                for path in patches.touched_paths(task.gold_patch_text):
                    self.assertNotIn(path, prose)

    def test_hidden_tests_exist(self):
        for task in self.tasks:
            with self.subTest(task=task.id):
                self.assertTrue(task.test_patch_text or task.hidden_tests.get("support_files"),
                                "a task needs a test patch or a test script")

    def test_validation_records(self):
        for task in self.tasks:
            for record in task.validation_records():
                with self.subTest(task=task.id, platform=record["environment"]["platform"]):
                    self.assertIn("ok", record)
                    if record["ok"]:
                        self.assertEqual(record["gold"]["status"], "resolved")
                        self.assertEqual(record["base"]["status"], "unresolved")
                        self.assertTrue(task.reproduces_here(record["environment"]["platform"]))

    def test_prompt_has_no_hidden_test_names(self):
        for task in self.tasks:
            prompt = cli.prompt_text(task)
            with self.subTest(task=task.id):
                self.assertIn(task.base_commit, prompt)
                for path in patches.created_paths(task.test_patch_text):
                    self.assertNotIn(path, prompt)

    def test_readme_lists_every_task(self):
        readme = (tasks.ROOT / "README.md").read_text(encoding="utf-8")
        for task in self.tasks:
            with self.subTest(task=task.id):
                self.assertIn(f"`{task.id}`", readme)
        self.assertIn(cli.task_table(self.tasks), readme, "README task table is stale: run `python -m bugbench list --markdown`")

    def test_task_json_is_canonical(self):
        for task in self.tasks:
            with self.subTest(task=task.id):
                raw = (task.dir / "task.json").read_text(encoding="utf-8")
                self.assertEqual(json.loads(raw)["id"], task.id)
                self.assertNotIn("\r", raw)


if __name__ == "__main__":
    unittest.main()
