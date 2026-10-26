"""Check out a task at its base commit, apply a patch and the hidden tests, run them."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import locale
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import patches
from .tasks import ROOT, VALIDATION_DIR, Task

DEFAULT_WORK_ROOT = Path(os.environ.get("BUGBENCH_WORK", ROOT / ".work"))
DEFAULT_KEEP = ["node_modules", "target", ".bbvenv", ".pnpm-store"]
LOG_TAIL = 4000


def current_platform() -> str:
    return {"win32": "windows", "darwin": "macos"}.get(sys.platform, "linux")


def _git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=check, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _mirror_dir(work_root: Path, repo: str) -> Path:
    name = repo.rstrip("/").removesuffix(".git").split("/")[-2:]
    return work_root / "repos" / ("__".join(name) + ".git")


def ensure_checkout(task: Task, work_root: Path, fresh: bool = False) -> Path:
    """Return a worktree of the task's repo at its base commit, cleaned of earlier runs.

    Ignored build caches listed in `keep_paths` (node_modules, target, ...) survive
    so that a second run doesn't reinstall everything.
    """
    mirror = _mirror_dir(work_root, task.repo)
    if not mirror.exists():
        mirror.parent.mkdir(parents=True, exist_ok=True)
        _git("clone", "--bare", "--filter=blob:none", "--quiet", task.repo, str(mirror))
    # Patches and hidden tests assume the bytes in the repository, whatever the
    # local Git defaults are (Git for Windows ships core.autocrlf=true).
    _git("config", "core.autocrlf", "false", cwd=mirror)
    _git("config", "core.longpaths", "true", cwd=mirror)
    sha = task.base_commit
    if _git("cat-file", "-e", f"{sha}^{{commit}}", cwd=mirror, check=False).returncode:
        _git("fetch", "--quiet", "--filter=blob:none", "origin", sha, cwd=mirror)

    ws = work_root / "ws" / task.id
    if ws.exists() and fresh:
        _git("worktree", "remove", "--force", str(ws), cwd=mirror, check=False)
        shutil.rmtree(ws, ignore_errors=True)
        _git("worktree", "prune", cwd=mirror)
    if not (ws / ".git").exists():
        shutil.rmtree(ws, ignore_errors=True)
        _git("worktree", "prune", cwd=mirror)
        ws.parent.mkdir(parents=True, exist_ok=True)
        _git("worktree", "add", "--detach", "--force", str(ws), sha, cwd=mirror)
    else:
        _git("checkout", "--force", "--detach", sha, cwd=ws)
        _git("reset", "--hard", "--quiet", sha, cwd=ws)
        keep = task.data.get("keep_paths", DEFAULT_KEEP)
        _git("clean", "-ffdx", "--quiet", *[f"-e{k}" for k in keep], cwd=ws)
    return ws


def _apply(ws: Path, patch: Path) -> tuple[bool, str]:
    # `git apply` applies all of a patch or nothing, so a failed try leaves no trace.
    out = ""
    for extra in ([], ["--ignore-whitespace"]):
        r = _git("apply", "--whitespace=nowarn", *extra, str(patch.resolve()), cwd=ws, check=False)
        if r.returncode == 0:
            return True, " ".join(["git apply", *extra])
        out = r.stderr
    return False, out


def _restore_test_files(task: Task, ws: Path) -> None:
    """Undo a candidate's edits to files the hidden tests own."""
    for f in patches.parse(task.test_patch_text):
        path = f.path
        if f.old_path is None:
            target = ws / path
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
        else:
            _git("checkout", task.base_commit, "--", path, cwd=ws, check=False)


def _expand(value: str, subs: dict[str, str]) -> str:
    for key, sub in subs.items():
        value = value.replace("{" + key + "}", sub)
    return value


def _run_cmd(argv: list[str], ws: Path, env: dict, log, timeout: int) -> int:
    exe = argv[0]
    if not os.path.isabs(exe):
        exe = shutil.which(exe, path=env.get("PATH")) or exe
    log.write(f"\n$ {' '.join(argv)}\n")
    log.flush()
    try:
        r = subprocess.run([exe, *argv[1:]], cwd=ws, env=env, stdout=log, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.write(f"\n[bugbench] timed out after {timeout}s\n")
        return -1
    except OSError as e:
        log.write(f"\n[bugbench] could not start {argv[0]}: {e}\n")
        return -2
    log.write(f"[bugbench] exit {r.returncode}\n")
    return r.returncode


def _tail(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[-LOG_TAIL:]


def run(task: Task, mode: str, candidate: Path | None = None, work_root: Path = DEFAULT_WORK_ROOT,
        fresh: bool = False, log_dir: Path | None = None) -> dict:
    """Run one task.

    mode: "base" (no patch), "gold" (reference fix) or "candidate" (a patch file).
    """
    assert mode in ("base", "gold", "candidate")
    started = time.time()
    plat = current_platform()
    result = {
        "task_id": task.id,
        "mode": mode,
        "platform": plat,
        "reproduces_here": task.reproduces_here(plat),
        "started": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
    }
    patch = {"gold": task.dir / task.gold_patch, "candidate": candidate}.get(mode)
    if patch is not None:
        result["patch_sha256"] = hashlib.sha256(patch.read_bytes()).hexdigest()

    log_dir = log_dir or work_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{task.id}.{mode}.log"
    result["log"] = str(log_path)

    with open(log_path, "w", encoding="utf-8", errors="replace") as log:
        status = _execute(task, patch, result, log, work_root, fresh)
    result["status"] = status
    result["resolved"] = status == "resolved"
    result["duration_sec"] = round(time.time() - started, 1)
    result["log_tail"] = _tail(log_path)
    return result


def _execute(task: Task, patch: Path | None, result: dict, log, work_root: Path, fresh: bool) -> str:
    """Check out, patch, set up and test; return the run's status."""
    try:
        ws = ensure_checkout(task, work_root, fresh=fresh)
    except subprocess.CalledProcessError as e:
        log.write(f"[bugbench] checkout failed: {e.stderr}\n")
        return "error"

    if patch is not None and patch.read_text(encoding="utf-8", errors="replace").strip():
        ok, how = _apply(ws, patch)
        log.write(f"[bugbench] candidate patch: {how}\n")
        if not ok:
            return "patch_failed"
    if task.test_patch_text:
        _restore_test_files(task, ws)
        ok, how = _apply(ws, task.dir / task.test_patch)
        if not ok:
            log.write(f"[bugbench] hidden tests do not apply: {how}\n")
            return "error"

    env = dict(os.environ)
    python = sys.executable
    if task.data.get("python_venv"):
        venv = ws / ".bbvenv"
        bindir = venv / ("Scripts" if os.name == "nt" else "bin")
        if not bindir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
        python = str(bindir / ("python.exe" if os.name == "nt" else "python"))
        env["PATH"] = str(bindir) + os.pathsep + env.get("PATH", "")
        env["VIRTUAL_ENV"] = str(venv)
    subs = {"python": python, "task_dir": str(task.dir.resolve()), "workdir": str(ws.resolve()),
            "bench": str(ROOT), "pathsep": os.pathsep}
    for key, value in task.data.get("env", {}).items():
        env[key] = _expand(value, {**subs, f"env:{key}": env.get(key, "")})
    timeout = int(task.data.get("timeout_sec", 1800))

    def run_argv(argv: list[str]) -> int:
        return _run_cmd([_expand(a, subs) for a in argv], ws, env, log, timeout)

    for argv in task.data.get("setup", []):
        code = run_argv(argv)
        if code != 0:
            result["setup_exit"] = code
            return "setup_failed"

    test_exit = 0
    for argv in task.test_commands:
        # Run every hidden test command, even after a failure, so the log shows all of them.
        test_exit = run_argv(argv) or test_exit
    result["test_exit"] = test_exit
    status = "resolved" if test_exit == 0 else "unresolved"
    if "regression_command" in task.data:
        result["regression_exit"] = run_argv(task.regression_command)
        if result["regression_exit"] != 0:
            status = "unresolved"
    return status


def _version(argv: list[str]) -> str | None:
    exe = shutil.which(argv[0])
    if not exe:
        return None
    try:
        r = subprocess.run([exe, *argv[1:]], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr).strip() else None


def _os_name() -> str:
    if sys.platform == "win32":
        build = int(platform.win32_ver()[1].split(".")[-1] or 0)
        # platform.release() still says "10" on Windows 11
        return f"Windows {11 if build >= 22000 else platform.release()} (build {build})"
    return platform.platform(terse=True)


def environment_info() -> dict:
    return {
        "platform": current_platform(),
        "os": _os_name(),
        "locale_encoding": locale.getpreferredencoding(False),
        "tz": os.environ.get("TZ") or time.tzname[0],
        "tools": {
            name: _version(argv) for name, argv in {
                "python": [sys.executable, "--version"], "node": ["node", "--version"],
                "cargo": ["cargo", "--version"], "go": ["go", "version"], "git": ["git", "--version"],
            }.items()
        },
    }


def validate(task: Task, work_root: Path = DEFAULT_WORK_ROOT, fresh: bool = False,
             write: bool = True) -> dict:
    """Check that the hidden tests fail at the base commit and pass with the gold patch."""
    plat = current_platform()
    record = {
        "date": dt.date.today().isoformat(),
        "environment": environment_info(),
    }
    if not task.reproduces_here(plat):
        record.update(ok=False, reason=f"bug reproduces on {task.reproduces_on}, not {plat}")
        return record
    base = run(task, "base", work_root=work_root, fresh=fresh)
    gold = run(task, "gold", work_root=work_root)
    reasons = []
    if base["status"] != "unresolved" or base.get("test_exit") in (None, 0):
        reasons.append(f"base should fail the hidden tests, got {base['status']}")
    if base.get("regression_exit", 0) != 0:
        reasons.append("regression tests fail at base")
    if gold["status"] != "resolved":
        reasons.append(f"gold patch should pass, got {gold['status']}")
    keep = ("status", "test_exit", "regression_exit", "setup_exit", "duration_sec")
    record.update(
        ok=not reasons,
        reason="; ".join(reasons) or "base fails, gold passes",
        base={k: base[k] for k in keep if k in base},
        gold={k: gold[k] for k in keep if k in gold},
    )
    if write:
        _write_record(task, record)
    record["base_log_tail"] = base["log_tail"]
    record["gold_log_tail"] = gold["log_tail"]
    return record


def _write_record(task: Task, record: dict) -> None:
    VALIDATION_DIR.mkdir(exist_ok=True)
    path = VALIDATION_DIR / f"{task.id}.json"
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    plat = record["environment"]["platform"]
    records = [r for r in records if r["environment"]["platform"] != plat] + [record]
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
