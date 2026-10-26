"""Task metadata: loading, validation, splits."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import patches

ROOT = Path(__file__).resolve().parent.parent
TASKS_DIR = ROOT / "tasks"
VALIDATION_DIR = ROOT / "validation"

CATEGORIES = {
    "windows-path": "Drive letters, backslashes, verbatim paths, MAX_PATH, paths passed as URLs",
    "line-endings": "CRLF input handled differently from LF",
    "locale-encoding": "Text read or written with the locale's legacy code page (cp932, cp950, ...)",
    "multibyte-text": "Byte length vs character length, splitting UTF-8 in the middle of a character",
    "cjk-parsing": "Parsing CJK numerals, dates or text",
    "url-encoding": "Percent-encoded non-ASCII or reserved characters in URLs and forms",
    "locale-terminology": "Regional vocabulary in conversion data (zh-CN to zh-TW)",
}
LANGUAGES = {"python", "rust", "go", "typescript", "javascript", "data"}
PLATFORMS = {"windows", "linux", "macos"}
SPLITS = ("main", "pending", "unvalidated")

_SHA = re.compile(r"^[0-9a-f]{40}$")


class TaskError(ValueError):
    pass


@dataclass
class Task:
    id: str
    dir: Path
    data: dict = field(repr=False)

    def __getattr__(self, name):
        try:
            return self.data[name]
        except KeyError:
            raise AttributeError(name) from None

    @property
    def gold_patch_text(self) -> str:
        return (self.dir / self.data["gold_patch"]).read_text(encoding="utf-8")

    @property
    def test_patch_text(self) -> str:
        name = self.data.get("test_patch")
        return (self.dir / name).read_text(encoding="utf-8") if name else ""

    @property
    def test_commands(self) -> list[list[str]]:
        cmd = self.data["test_command"]
        return cmd if isinstance(cmd[0], list) else [cmd]

    @property
    def problem_statement(self) -> str:
        return (self.dir / "problem.md").read_text(encoding="utf-8")

    @property
    def reproduces_on(self) -> list[str]:
        return self.data["environment"]["reproduces_on"]

    def reproduces_here(self, platform: str) -> bool:
        return "any" in self.reproduces_on or platform in self.reproduces_on

    def validation_records(self) -> list[dict]:
        path = VALIDATION_DIR / f"{self.id}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    @property
    def validated(self) -> bool:
        return any(r.get("ok") for r in self.validation_records())

    @property
    def split(self) -> str:
        if not self.validated:
            return "unvalidated"
        return "main" if self.data["upstream_status"] == "merged" else "pending"


def load(task_id: str, tasks_dir: Path = TASKS_DIR) -> Task:
    d = tasks_dir / task_id
    path = d / "task.json"
    if not path.exists():
        raise TaskError(f"no such task: {task_id}")
    task = Task(task_id, d, json.loads(path.read_text(encoding="utf-8")))
    validate(task)
    return task


def load_all(tasks_dir: Path = TASKS_DIR) -> list[Task]:
    return [load(p.parent.name, tasks_dir) for p in sorted(tasks_dir.glob("*/task.json"))]


def _require(cond: bool, task: Task, msg: str) -> None:
    if not cond:
        raise TaskError(f"{task.id}: {msg}")


def _is_argv(value) -> bool:
    return isinstance(value, list) and value and all(isinstance(a, str) for a in value)


def validate(task: Task) -> None:
    """Check a task's metadata and files. Raises TaskError."""
    d = task.data
    for key in ("id", "title", "repo", "upstream_pr", "upstream_status", "base_commit",
                "language", "category", "license", "environment", "test_command",
                "gold_patch", "hidden_tests"):
        _require(key in d, task, f"missing field {key!r}")
    _require(d["id"] == task.id, task, "id does not match the directory name")
    _require(d["repo"].startswith(("https://github.com/", "file://")), task, "repo must be a URL")
    _require(d["upstream_status"] in ("merged", "open"), task, "upstream_status must be merged or open")
    _require(bool(_SHA.match(d["base_commit"])), task, "base_commit must be a full sha")
    if d["upstream_status"] == "merged":
        _require(bool(_SHA.match(d.get("merge_commit", ""))), task, "merged tasks need merge_commit")
    _require(d["language"] in LANGUAGES, task, f"unknown language {d['language']!r}")
    _require(d["category"] in CATEGORIES, task, f"unknown category {d['category']!r}")

    env = d["environment"]
    _require(isinstance(env.get("reproduces_on"), list) and env["reproduces_on"], task,
             "environment.reproduces_on must be a non-empty list")
    for p in env["reproduces_on"]:
        _require(p == "any" or p in PLATFORMS, task, f"unknown platform {p!r}")

    for cmd in d.get("setup", []):
        _require(_is_argv(cmd), task, "setup entries must be argv lists")
    _require(_is_argv(d["test_command"]) or (isinstance(d["test_command"], list) and d["test_command"]
                                             and all(_is_argv(c) for c in d["test_command"])),
             task, "test_command must be an argv list or a list of argv lists")
    if "regression_command" in d:
        _require(_is_argv(d["regression_command"]), task, "regression_command must be an argv list")

    hidden = d["hidden_tests"]
    _require(hidden.get("source") in ("upstream-pr", "benchmark"), task,
             "hidden_tests.source must be upstream-pr or benchmark")

    _require((task.dir / "problem.md").exists(), task, "problem.md is missing")
    gold = task.gold_patch_text
    _require(bool(patches.parse(gold)), task, "gold patch is empty")
    test = task.test_patch_text
    if d.get("test_patch"):
        _require(bool(patches.parse(test)), task, "test patch is empty")
        overlap = set(patches.touched_paths(gold)) & set(patches.touched_paths(test))
        _require(not overlap, task, f"gold and test patches both touch {sorted(overlap)}")
    for name in hidden.get("support_files", []):
        _require((task.dir / name).exists(), task, f"support file {name} is missing")
