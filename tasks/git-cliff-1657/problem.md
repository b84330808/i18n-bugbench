# `git cliff --workdir <subdir>` lists every commit on Windows

`--workdir` (`-w`) is supposed to scope the changelog to a directory: only commits that touch files inside it should be listed. On Linux and macOS this works. On Windows, running from the repository root

```
git cliff --workdir sub/dir
```

lists every commit in the repository, including the ones that only touch files outside `sub/dir`. Writing the directory as `sub\dir` doesn't help.

Expected: on Windows, `--workdir sub/dir` and `--workdir sub\dir` give the same result as `--workdir sub/dir` on Linux: only commits touching `sub/dir` (including nested directories) are listed.
