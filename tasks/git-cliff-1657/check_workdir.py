"""Hidden test for git-cliff-1657, written for i18n-bugbench (MIT).

Builds a small repository with commits inside and outside `sub/dir` and checks
that `git cliff --workdir sub/dir` only lists the commits that touch `sub/dir`.

Usage: python check_workdir.py <git-cliff repository checkout>
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

GIT_ENV = {
    "GIT_AUTHOR_NAME": "bugbench", "GIT_AUTHOR_EMAIL": "bugbench@example.com",
    "GIT_COMMITTER_NAME": "bugbench", "GIT_COMMITTER_EMAIL": "bugbench@example.com",
    "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
}

INSIDE = ["add the sub feature", "repair the sub parser"]
OUTSIDE = ["add the readme", "repair the other module"]


def find_binary(checkout: Path) -> Path:
    for name in ("git-cliff.exe", "git-cliff"):
        exe = checkout / "target" / "debug" / name
        if exe.exists():
            return exe
    sys.exit(f"git-cliff binary not found under {checkout / 'target' / 'debug'}")


def make_repo(root: Path) -> None:
    env = {**os.environ, **GIT_ENV}

    def git(*args):
        subprocess.run(["git", *args], cwd=root, env=env, check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    commits = [
        ("README.md", "feat: " + OUTSIDE[0]),
        ("sub/dir/a.txt", "feat: " + INSIDE[0]),
        ("other/b.txt", "fix: " + OUTSIDE[1]),
        ("sub/dir/nested/c.txt", "fix: " + INSIDE[1]),
    ]
    for i, (path, message) in enumerate(commits):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"{i}\n", encoding="utf-8")
        git("add", path)
        git("commit", "-q", "-m", message)


def main() -> None:
    # The changelog has emoji headings; don't crash on a cp932 console.
    sys.stdout.reconfigure(errors="backslashreplace")
    exe = find_binary(Path(sys.argv[1]))
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        make_repo(repo)
        # The native separator is `\` on Windows; both spellings name the same directory.
        for workdir in sorted({"sub/dir", os.path.join("sub", "dir")}):
            r = subprocess.run([str(exe), "--workdir", workdir], cwd=repo, capture_output=True,
                               encoding="utf-8", errors="replace", env={**os.environ, "NO_COLOR": "1"})
            out = r.stdout.lower()
            if r.returncode != 0:
                failures.append(f"--workdir {workdir}: exit {r.returncode}\n{r.stderr}")
                continue
            missing = [m for m in INSIDE if m not in out]
            extra = [m for m in OUTSIDE if m in out]
            if missing or extra:
                failures.append(f"--workdir {workdir}: missing {missing}, unexpected {extra}\n{r.stdout}")
    if failures:
        print("\n".join(failures))
        sys.exit(1)
    print("ok")


if __name__ == "__main__":
    main()
