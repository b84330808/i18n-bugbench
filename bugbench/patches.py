"""Small helpers for unified diffs: list touched files, split a PR diff."""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass

_DIFF_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+?)$")


@dataclass
class FileDiff:
    old_path: str | None  # None when the file is created
    new_path: str | None  # None when the file is deleted
    text: str

    @property
    def path(self) -> str:
        return self.new_path or self.old_path or ""


def parse(diff_text: str) -> list[FileDiff]:
    """Split a `git diff` into one chunk per file."""
    chunks: list[list[str]] = []
    for line in diff_text.splitlines(keepends=True):
        if line.startswith("diff --git "):
            chunks.append([line])
        elif chunks:
            chunks[-1].append(line)
        elif line.strip():
            raise ValueError("diff does not start with 'diff --git'")
    files = []
    for chunk in chunks:
        m = _DIFF_HEADER.match(chunk[0].rstrip("\r\n"))
        if not m:
            raise ValueError(f"cannot parse diff header: {chunk[0]!r}")
        old_path, new_path = m.group(1), m.group(2)
        for line in chunk[1:6]:
            if line.startswith("new file mode"):
                old_path = None
            elif line.startswith("deleted file mode"):
                new_path = None
        files.append(FileDiff(old_path, new_path, "".join(chunk)))
    return files


def touched_paths(diff_text: str) -> list[str]:
    return [f.path for f in parse(diff_text)]


def created_paths(diff_text: str) -> list[str]:
    return [f.path for f in parse(diff_text) if f.old_path is None]


def split(diff_text: str, test_globs: list[str], drop_globs: list[str] = ()) -> tuple[str, str]:
    """Split a PR diff into (source patch, test patch).

    Files matching `test_globs` go to the test patch, files matching
    `drop_globs` (changelogs, changesets) are left out, the rest is source.
    """
    gold, test = [], []
    for f in parse(diff_text):
        if any(fnmatch.fnmatch(f.path, g) for g in drop_globs):
            continue
        (test if any(fnmatch.fnmatch(f.path, g) for g in test_globs) else gold).append(f.text)
    return "".join(gold), "".join(test)
