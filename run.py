#!/usr/bin/env python3
"""Run benchmark tasks against any coding-agent CLI and grade the results.

Example:
    python3 run.py --name sonnet --agent 'claude -p {prompt} --model sonnet --dangerously-skip-permissions'
    python3 run.py --name modelB --agent 'my-agent --task-file {prompt_file}' --runs 3
    python3 run.py --name copilot-chat --manual          # IDE / chat agents driven by hand
    python3 report.py
"""
import argparse
import difflib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS_DIR = ROOT / "tasks"
GIT = ["git", "-c", "user.name=bench", "-c", "user.email=bench@localhost",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]


def load_tasks(selected):
    tasks = sorted(p for p in TASKS_DIR.iterdir() if (p / "task.json").exists())
    if selected:
        tasks = [t for t in tasks if any(t.name == s or t.name.startswith(s) for s in selected)]
    if not tasks:
        sys.exit(f"No tasks matched {selected!r} in {TASKS_DIR}")
    return tasks


def git(cwd, *args):
    return subprocess.run([*GIT, *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def snapshot_paths(work, rel_paths):
    """Contents of every file under the protected paths (missing files simply don't appear)."""
    out = {}
    for rel in rel_paths:
        base = work / rel
        files = [base] if base.is_file() else sorted(base.rglob("*")) if base.is_dir() else []
        for f in files:
            if f.is_file() and "__pycache__" not in f.parts:
                out[str(f.relative_to(work))] = f.read_bytes()
    return out


SKIP_RE = re.compile(rb"\b(skip|skipif|xfail|importorskip)\b")


def check_protected(before, after):
    """Tampering = an existing protected file was deleted, or any of its lines were removed or changed,
    or an added line skips/xfails tests. Pure additions (new tests appended, new test files) are
    allowed and only reported, since grading uses a pristine copy of the visible tests anyway."""
    tampered, added_to = [], []
    for path in sorted(before.keys() | after.keys()):
        old, new = before.get(path), after.get(path)
        if old == new:
            continue
        if new is None:
            tampered.append(path)
            continue
        old_lines = old.splitlines() if old is not None else []
        added = []
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new.splitlines(),
                                                           autojunk=False).get_opcodes():
            if op in ("replace", "delete"):
                break
            if op == "insert":
                added += new.splitlines()[j1:j2]
        else:
            if any(SKIP_RE.search(line) for line in added):
                tampered.append(path)
            else:
                added_to.append(path)
            continue
        tampered.append(path)
    return tampered, added_to


def prepare_workdir(task, work):
    shutil.copytree(task / "repo", work)
    (work / ".gitignore").write_text("__pycache__/\n.pytest_cache/\n*.pyc\n")
    git(work, "init", "-q")
    git(work, "add", "-A")
    git(work, "commit", "-q", "-m", "baseline")


def run_agent(cmd_tpl, prompt, task_name, work, log_path, timeout):
    prompt_file = work.parent / "PROMPT.txt"
    prompt_file.write_text(prompt)
    cmd = (cmd_tpl.replace("{prompt_file}", shlex.quote(str(prompt_file)))
                  .replace("{workdir}", shlex.quote(str(work)))
                  .replace("{prompt}", shlex.quote(prompt)))
    env = {**os.environ, "BENCH_PROMPT": prompt, "BENCH_TASK": task_name}
    t0 = time.monotonic()
    with open(log_path, "w") as log:
        log.write(f"$ {cmd}\n\n")
        log.flush()
        proc = subprocess.Popen(cmd, shell=True, cwd=work, env=env, stdout=log,
                                stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            rc = proc.wait(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            rc, timed_out = None, True
        finally:
            # Always kill the whole session, so background processes the agent left behind
            # can't keep changing files while we check and grade them.
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.wait()
    return rc, timed_out, round(time.monotonic() - t0, 2)


def run_manual(prompt, task_name, run_label, work, log_path, open_editor):
    """Human-driven run: show the prompt, optionally open VS Code, and wait for keypresses.
    Returns (followups, gave_up, seconds). Only "continue" follow-ups are allowed; each is logged."""
    prompt_file = work.parent / "PROMPT.txt"
    prompt_file.write_text(prompt)
    bar = "=" * 72
    print(f"\n{bar}\n{task_name} {run_label}\n  folder: {work}\n  prompt file: {prompt_file}\n{bar}\n"
          f"{prompt}\n{bar}")
    if open_editor:
        if shutil.which("code"):
            subprocess.run(["code", "--new-window", str(work)], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            print("  ('code' not on PATH; open the folder yourself)")
    print("Open the folder in a FRESH chat, paste the prompt exactly, let the agent work.\n"
          "Rules: the only follow-up allowed is \"continue\"; don't edit files yourself.\n"
          "  c + Enter  = I sent \"continue\" (logged)\n"
          "  Enter      = agent finished, grade it\n"
          "  g + Enter  = gave up (still graded, marked gave_up)")
    t0 = time.monotonic()
    followups, gave_up = [], False
    with open(log_path, "w") as log:
        log.write(f"manual run of {task_name} {run_label}\nprompt shown at "
                  f"{datetime.now(timezone.utc).isoformat()}\n")
        while True:
            try:
                line = input("> ").strip().lower()
            except EOFError:
                sys.exit("\nstdin closed; aborting (this run was not recorded)")
            now = datetime.now(timezone.utc).isoformat()
            if line == "c":
                followups.append({"t": round(time.monotonic() - t0, 2), "at": now, "text": "continue"})
                log.write(f"{now} continue\n")
                print(f"  logged continue #{len(followups)}")
            elif line in ("", "g"):
                gave_up = line == "g"
                log.write(f"{now} {'gave up' if gave_up else 'done'}\n")
                break
            else:
                print("  unknown input; use c, g, or just Enter")
    return followups, gave_up, round(time.monotonic() - t0, 2)


def read_cost(log_path):
    """Best effort: the last 'total_cost_usd' the agent printed (Claude Code --output-format json).
    Returns None for agents that don't report cost."""
    try:
        hits = re.findall(r'"total_cost_usd"\s*:\s*([0-9.]+)', Path(log_path).read_text(errors="replace"))
    except OSError:
        return None
    return round(float(hits[-1]), 4) if hits else None


def diff_stats(work):
    git(work, "add", "-A")
    added = removed = 0
    files = []
    for line in git(work, "diff", "--cached", "--numstat", "HEAD").splitlines():
        a, r, path = line.split("\t", 2)
        files.append(path)
        added += int(a) if a.isdigit() else 0
        removed += int(r) if r.isdigit() else 0
    return {"files_changed": files, "lines_added": added, "lines_removed": removed}


GRADER_PY = sys.executable


def ensure_pytest():
    """Return a Python that has pytest. Uses this Python if it already does; otherwise creates
    .venv/ inside the kit once and installs pytest there (works on distros that block system pip)."""
    if subprocess.run([sys.executable, "-c", "import pytest"], capture_output=True).returncode == 0:
        return sys.executable
    venv_py = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not venv_py.exists() or subprocess.run([str(venv_py), "-c", "import pytest"],
                                              capture_output=True).returncode != 0:
        print(f"pytest not found for {sys.executable}; installing it into {ROOT / '.venv'} (one time)...",
              flush=True)
        try:
            subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
            subprocess.run([str(venv_py), "-m", "pip", "install", "-q", "pytest"], check=True)
        except (subprocess.CalledProcessError, OSError) as e:
            sys.exit(f"could not set up pytest automatically ({e}). Install it yourself: "
                     f"pip install pytest  (Debian/Ubuntu may need: sudo apt install python3-venv)")
    return str(venv_py)


def grade(task, work):
    """Run the hidden tests plus a pristine copy of the visible tests.

    Hardened against an agent gaming the grader: tests and the junit report live in a fresh temp dir
    the agent never saw; Python runs isolated (-I: no PYTHONPATH, no user site, no cwd on sys.path),
    so a planted pytest.py / sitecustomize.py in the repo can't load before pytest. The repo is only
    added to sys.path by pytest's `pythonpath` option once pytest is running. Agent-written
    conftest.py / pytest.ini files are ignored; skipped tests count as failures."""
    gdir = Path(tempfile.mkdtemp(prefix="bench-grade-"))
    try:
        hidden = gdir / "tests"
        shutil.copytree(task / "hidden", hidden)
        if (task / "repo" / "tests").is_dir():
            shutil.copytree(task / "repo" / "tests", hidden / "_visible")
        junit = gdir / "junit.xml"
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        cmd = [GRADER_PY, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--noconftest",
               "-c", str(ROOT / "grader.ini"), "--rootdir", str(gdir), "-o", f"pythonpath={work}",
               "--import-mode=importlib", f"--junitxml={junit}", str(hidden)]
        try:
            proc = subprocess.run(cmd, cwd=gdir, env=env, capture_output=True, text=True, timeout=180)
            output = proc.stdout + proc.stderr
        except subprocess.TimeoutExpired:
            return {"tests": 0, "passed": 0, "score": 0.0, "test_output": "grader timed out"}
        (work.parent / "grade.log").write_text(output)
        tests = failed = 0
        if junit.exists():
            for suite in ET.parse(junit).getroot().iter("testsuite"):
                tests += int(suite.get("tests", 0))
                failed += sum(int(suite.get(k, 0)) for k in ("failures", "errors", "skipped"))
        passed = tests - failed
        return {"tests": tests, "passed": passed, "score": round(passed / tests, 3) if tests else 0.0,
                "test_output": output[-2000:]}
    finally:
        shutil.rmtree(gdir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True, help="label for this model/agent config, e.g. 'sonnet'")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--manual", action="store_true",
                      help="human-driven run for IDE/chat agents: prints each prompt and waits for you")
    mode.add_argument("--agent",
                    help="shell command run inside the task repo. Placeholders: {prompt} {prompt_file} {workdir}. "
                         "Env vars BENCH_PROMPT and BENCH_TASK are also set.")
    ap.add_argument("--tasks", nargs="*", default=None, help="task names or prefixes (default: all)")
    ap.add_argument("--runs", type=int, default=3, help="repeats per task (default 3)")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per agent run (default 300)")
    ap.add_argument("--jobs", type=int, default=6,
                    help="agent runs in parallel (default 6; --manual always runs one at a time)")
    ap.add_argument("--results", default=str(ROOT / "results" / "results.jsonl"))
    ap.add_argument("--workdir", default=None,
                    help="where task copies are created (default: a temp dir outside this kit, "
                         "so the agent can't stumble on hidden tests)")
    ap.add_argument("--note", default=None,
                    help="free text describing the agent (model, extension version, settings). "
                         "Asked interactively in --manual mode if omitted")
    ap.add_argument("--no-open", action="store_true", help="--manual: don't try to open VS Code")
    args = ap.parse_args()
    if args.manual and args.note is None:
        try:
            args.note = input("Describe this agent (model, extension + version, settings): ").strip()
        except EOFError:
            args.note = ""

    global GRADER_PY
    GRADER_PY = ensure_pytest()
    tasks = load_tasks(args.tasks)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    base = Path(args.workdir or Path(tempfile.gettempdir()) / "ai-coding-bench") / run_id / args.name
    results_path = Path(args.results)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"run {run_id}: {len(tasks)} tasks x {args.runs} runs for '{args.name}'"
          f"{'' if args.manual else f', {args.jobs} in parallel, {args.timeout}s timeout each'}"
          f"\nworkdirs: {base}\n")

    lock = threading.Lock()
    t_start = time.monotonic()

    def one_run(task, spec, r):
        run_dir = base / task.name / f"r{r}"
        work = run_dir / "repo"
        prepare_workdir(task, work)
        protected = spec.get("protected", ["tests"])
        before = snapshot_paths(work, protected)

        followups, gave_up = [], False
        if args.manual:
            followups, gave_up, secs = run_manual(spec["prompt"], task.name, f"r{r}/{args.runs}",
                                                  work, run_dir / "agent.log", not args.no_open)
            rc, timed_out = None, False
        else:
            rc, timed_out, secs = run_agent(args.agent, spec["prompt"], task.name, work,
                                            run_dir / "agent.log", args.timeout)

        tampered, tests_added_to = check_protected(before, snapshot_paths(work, protected))
        diff = diff_stats(work)
        g = grade(task, work)
        # The agent exited with an error and changed nothing: almost always the provider or the harness
        # failing (billing, auth, rate limit, bad flag), not the model trying and failing. Recorded,
        # but left out of the scores by report.py.
        infra_error = (not args.manual and not timed_out and rc not in (0, None)
                       and not diff["files_changed"])
        passed = g["tests"] > 0 and g["passed"] == g["tests"] and not tampered and not infra_error
        result = {
            "run_id": run_id, "agent": args.name, "agent_cmd": args.agent, "task": task.name,
            "mode": "manual" if args.manual else "cli", "agent_note": args.note,
            "timing": "manual" if args.manual else "cli", "continues": len(followups),
            "followups": followups, "gave_up": gave_up,
            "difficulty": spec.get("difficulty"), "repeat": r, "pass": passed,
            "score": g["score"], "tests_passed": g["passed"], "tests_total": g["tests"],
            "tampered_files": tampered, "tests_added_to": tests_added_to, "timed_out": timed_out,
            "exit_code": rc, "infra_error": infra_error, "seconds": secs, "cost_usd": read_cost(run_dir / "agent.log"),
            **diff, "workdir": str(work), "log": str(run_dir / "agent.log"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        notes = []
        if tampered: notes.append(f"TAMPERED {tampered}")
        if tests_added_to: notes.append(f"added tests to {tests_added_to}")
        if timed_out: notes.append("TIMEOUT")
        if followups: notes.append(f"continues={len(followups)}")
        if gave_up: notes.append("GAVE_UP")
        if infra_error: notes.append(f"INFRA_ERROR exit {rc}, nothing changed; excluded from scores, see agent.log")
        if result["cost_usd"] is not None: notes.insert(0, f"${result['cost_usd']:.2f}")
        with lock:
            with open(results_path, "a") as f:
                f.write(json.dumps(result) + "\n")
            print(f"[{'INFRA' if infra_error else 'PASS' if passed else 'FAIL'}] {task.name:<24} r{r}  tests {g['passed']}/{g['tests']}  "
                  f"{secs:>7.1f}s  +{diff['lines_added']}/-{diff['lines_removed']}  {' '.join(notes)}",
                  flush=True)

    jobs = [(t, json.loads((t / "task.json").read_text()), r) for t in tasks for r in range(1, args.runs + 1)]
    with ThreadPoolExecutor(max_workers=1 if args.manual else max(1, args.jobs)) as pool:
        for fut in [pool.submit(one_run, *j) for j in jobs]:
            fut.result()
    print(f"\nall {len(jobs)} runs done in {(time.monotonic() - t_start) / 60:.1f} min")

    print(f"\nresults appended to {results_path}\nnext: python3 {ROOT / 'report.py'}")


if __name__ == "__main__":
    main()
