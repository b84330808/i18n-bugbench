"""Command line: list, prompt, run, validate, evaluate, split-diff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import patches, runner, tasks


def _select(args) -> list[tasks.Task]:
    all_tasks = tasks.load_all()
    if getattr(args, "task", None):
        wanted = set(args.task)
        unknown = wanted - {t.id for t in all_tasks}
        if unknown:
            sys.exit(f"unknown task(s): {', '.join(sorted(unknown))}")
        return [t for t in all_tasks if t.id in wanted]
    if getattr(args, "split", None):
        return [t for t in all_tasks if t.split == args.split]
    return all_tasks


def task_table(selected: list[tasks.Task]) -> str:
    lines = ["| Task | Upstream PR | Language | Category | Bug shows on | Upstream | Hidden tests | Split |",
             "|---|---|---|---|---|---|---|---|"]
    for t in selected:
        repo = t.repo.removeprefix("https://github.com/")
        number = t.upstream_pr.rstrip("/").split("/")[-1]
        lines.append(f"| `{t.id}` | [{repo}#{number}]({t.upstream_pr}) | {t.language} | {t.category} "
                     f"| {', '.join(t.reproduces_on)} | {t.upstream_status} | {t.hidden_tests['source']} | {t.split} |")
    return "\n".join(lines) + "\n"


def cmd_list(args) -> None:
    if args.markdown:
        sys.stdout.write(task_table(_select(args)))
        return
    rows = [(t.id, t.split, t.language, t.category, ",".join(t.reproduces_on)) for t in _select(args)]
    if args.json:
        print(json.dumps([dict(zip(("id", "split", "language", "category", "reproduces_on"), r))
                          for r in rows], indent=2))
        return
    widths = [max(len(str(r[i])) for r in rows + [("id", "split", "language", "category", "os")])
              for i in range(5)]
    for r in [("id", "split", "language", "category", "os"), *rows]:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip())


def prompt_text(task: tasks.Task) -> str:
    env = task.environment
    lines = [
        f"Repository: {task.repo}",
        f"Base commit: {task.base_commit}",
        f"Reproduces on: {', '.join(env['reproduces_on'])}",
    ]
    for key in ("locale", "tz"):
        if env.get(key):
            lines.append(f"{key.upper() if key == 'tz' else key.capitalize()}: {env[key]}")
    lines += ["", task.problem_statement.strip(), "",
              "Make the smallest change to the repository that fixes this problem. "
              "Hidden tests will be run against your change."]
    return "\n".join(lines) + "\n"


def cmd_prompt(args) -> None:
    # Always UTF-8: `bugbench prompt x > prompt.txt` must not produce a cp932 file.
    sys.stdout.flush()
    sys.stdout.buffer.write(prompt_text(tasks.load(args.task_id)).encode("utf-8"))
    sys.stdout.buffer.flush()


def cmd_run(args) -> None:
    task = tasks.load(args.task_id)
    patch = Path(args.patch) if args.patch else None
    mode = "candidate" if patch else args.mode
    result = runner.run(task, mode, patch, work_root=Path(args.work), fresh=args.fresh)
    tail = result.pop("log_tail")
    if args.verbose:
        print(tail)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["resolved"] else 1)


def cmd_validate(args) -> None:
    failed = 0
    for task in _select(args):
        record = runner.validate(task, work_root=Path(args.work), fresh=args.fresh, write=not args.dry_run)
        status = "ok" if record["ok"] else "FAIL"
        print(f"{task.id}: {status} ({record['reason']})", flush=True)
        if not record["ok"] and args.verbose and "base_log_tail" in record:
            print("--- base log ---\n" + record["base_log_tail"])
            print("--- gold log ---\n" + record["gold_log_tail"])
        failed += not record["ok"]
    sys.exit(1 if failed else 0)


def cmd_evaluate(args) -> None:
    """Run predictions from a JSONL file: {"task_id": ..., "model_patch": "<diff>"} per line."""
    out_dir = Path(args.out)
    patch_dir = out_dir / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    selected = {t.id: t for t in _select(args)}
    results = []
    for line in Path(args.predictions).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pred = json.loads(line)
        task = selected.get(pred["task_id"])
        if task is None:
            continue
        patch = patch_dir / f"{task.id}.patch"
        patch.write_text(pred.get("model_patch") or "", encoding="utf-8", newline="\n")
        result = runner.run(task, "candidate", patch, work_root=Path(args.work), log_dir=out_dir / "logs")
        result.pop("log_tail")
        result["split"] = task.split
        results.append(result)
        print(f"{task.id}: {result['status']}", flush=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (out_dir / "summary.md").write_text(summary_table(results, args.name), encoding="utf-8")
    print((out_dir / "summary.md").read_text(encoding="utf-8"))


def summary_table(results: list[dict], name: str) -> str:
    def rate(rows):
        valid = [r for r in rows if r["reproduces_here"]]
        if not valid:
            return "n/a"
        return f"{sum(r['resolved'] for r in valid)}/{len(valid)}"
    by_split = {s: [r for r in results if r["split"] == s] for s in tasks.SPLITS}
    cells = [rate(by_split[s]) for s in tasks.SPLITS]
    lines = ["| Agent | " + " | ".join(tasks.SPLITS) + " | platform |",
             "|---|" + "---|" * len(tasks.SPLITS) + "---|",
             f"| {name} | " + " | ".join(cells) + f" | {runner.current_platform()} |", ""]
    skipped = [r["task_id"] for r in results if not r["reproduces_here"]]
    if skipped:
        lines.append("Not counted (the bug does not reproduce on this platform): " + ", ".join(skipped))
    return "\n".join(lines) + "\n"


def cmd_split_diff(args) -> None:
    text = Path(args.diff).read_text(encoding="utf-8")
    gold, test = patches.split(text, args.test, args.drop)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "gold.patch").write_text(gold, encoding="utf-8", newline="\n")
    if test:
        (out / "test.patch").write_text(test, encoding="utf-8", newline="\n")
    print(f"gold: {patches.touched_paths(gold)}\ntest: {patches.touched_paths(test)}")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="bugbench", description=__doc__)
    p.add_argument("--work", default=str(runner.DEFAULT_WORK_ROOT),
                   help="cache for clones, worktrees and logs (default: .work or $BUGBENCH_WORK)")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("list", help="list tasks")
    s.add_argument("--split", choices=tasks.SPLITS)
    s.add_argument("--json", action="store_true")
    s.add_argument("--markdown", action="store_true", help="the task table used in README.md")
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("prompt", help="print the problem statement given to an agent")
    s.add_argument("task_id")
    s.set_defaults(func=cmd_prompt)

    s = sub.add_parser("run", help="run one task with no patch, the gold patch or a candidate patch")
    s.add_argument("task_id")
    s.add_argument("--mode", choices=("base", "gold"), default="base")
    s.add_argument("--patch", help="candidate patch file (unified diff)")
    s.add_argument("--fresh", action="store_true", help="recreate the worktree")
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("validate", help="check that base fails and gold passes, record the result")
    s.add_argument("task", nargs="*")
    s.add_argument("--split", choices=tasks.SPLITS)
    s.add_argument("--fresh", action="store_true")
    s.add_argument("--dry-run", action="store_true", help="don't write validation/<task>.json")
    s.add_argument("-v", "--verbose", action="store_true")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("evaluate", help="run a JSONL file of predictions")
    s.add_argument("predictions")
    s.add_argument("--name", default="agent")
    s.add_argument("--out", default="results")
    s.add_argument("--split", choices=tasks.SPLITS)
    s.add_argument("task", nargs="*")
    s.set_defaults(func=cmd_evaluate)

    s = sub.add_parser("split-diff", help="split a PR diff into gold.patch and test.patch")
    s.add_argument("diff")
    s.add_argument("--test", action="append", default=[], help="glob for hidden-test files")
    s.add_argument("--drop", action="append", default=[], help="glob for files to leave out")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_split_diff)

    args = p.parse_args(argv)
    # Logs and problem statements contain CJK text and symbols; don't crash on a
    # console that uses a legacy code page such as cp932.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    args.func(args)
