#!/usr/bin/env python3
"""Checks that a part of the lab is finished."""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

os.chdir(Path(__file__).resolve().parent.parent)  # paths are repo-relative wherever this is run from
sys.path.insert(0, "scripts")
from my_work import todos_left  # noqa: E402


def _passes(script: str, *args: str) -> bool:
    """Run one of the lab's own check scripts in this process and say whether it exited 0. It runs as if from the
    command line, with its output hidden, and no new process: so no command line is built at all."""
    saved_argv, saved_path = sys.argv, sys.path[:]
    sys.argv = [script, *args]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            runpy.run_path(script, run_name="__main__")
        return True
    except SystemExit as done:
        return done.code in (0, None)
    except Exception:  # a crash in the participant's code is a failed check, not a crashed verify
        return False
    finally:
        sys.argv, sys.path[:] = saved_argv, saved_path


def _todo(path: Path) -> bool:
    return not path.exists() or todos_left(path) > 0


def _hook_wired() -> bool:
    settings = Path(".claude/settings.json").read_text()
    if "run_checks" in settings:
        return True
    configured = subprocess.run(["git", "config", "core.hooksPath"], capture_output=True, text=True).stdout.strip()
    pre_commit = Path(configured or ".git/hooks") / "pre-commit"
    return pre_commit.exists() and os.access(pre_commit, os.X_OK) and "run_checks" in pre_commit.read_text()


def part1() -> list[tuple[str, str]]:
    errors = []
    if _todo(Path("my-work/1-rule-sort.md")):
        errors.append(("1-rule-sort.md missing or has TODOs", "Finish chunk 1"))
    if _todo(Path("my-work/2-checks-plan.md")):
        errors.append(("2-checks-plan.md missing or has TODOs", "Finish chunk 2"))
    if not _passes("scripts/test_checks.py"):
        errors.append(("the checks don't pass ./lab test-checks", "Finish chunk 2"))
    if not _hook_wired():
        errors.append(("run_checks.py isn't wired into a hook", "Paste it into .claude/settings.json, or add a git pre-commit hook and make it executable (chunk 2)"))
    agent = Path("my-work/3-reviewer-agent.md")
    if _todo(agent) or "request_changes" not in agent.read_text():
        errors.append(("reviewer agent unfinished, or doesn't give a verdict", "Run /interview-reviewer (chunk 3)"))
    tried = json.loads(Path("results-try.json").read_text()) if Path("results-try.json").exists() else {}
    if not tried:
        errors.append(("the agent hasn't been run on the practice PRs", "./lab review try (chunk 3)"))
    elif all(answer.get("verdict") != "request_changes" for answer in tried.values()):
        errors.append(("the agent approved every practice PR", "try-3 breaks R8. Fix the agent (chunk 3)"))
    return errors


def part2() -> list[tuple[str, str]]:
    errors = []
    for name, chunk in (("4-gold-labels.md", 4), ("5-eval-design.md", 4), ("6-human-gate.md", 6)):
        if _todo(Path("my-work") / name):
            errors.append((f"{name} missing or has TODOs", f"Finish chunk {chunk}"))
    held_out = json.loads(Path("results-holdout.json").read_text()) if Path("results-holdout.json").exists() else {}
    if not any(answer.get("verdict") for answer in held_out.values()):
        errors.append(("results-holdout.json missing", "./lab review holdout (chunk 5)"))
    if not _passes("scripts/eval_reviewer.py", "--results", "data/eval-fixtures/always-approves.json"):
        errors.append(("score() isn't built", "Build it with Claude, or ./lab catch-up eval (chunk 5)"))
    if not _passes("scripts/test_gate.py"):
        errors.append(("the gate doesn't pass ./lab test-gate", "Finish chunk 6"))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", required=True, choices=["1", "2"])
    args = parser.parse_args()
    errors = part1() if args.part == "1" else part2()
    for name, fix in errors:
        print(f"[ERROR] Part {args.part}: {name}\n  Fix: {fix}")
    if errors:
        return 1
    print(f"[OK] Part {args.part}: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
