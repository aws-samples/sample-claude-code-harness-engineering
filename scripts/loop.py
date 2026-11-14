#!/usr/bin/env python3
"""./lab loop PR: closes the loop on one PR. Each round runs your checks, reviewer, specialist and gate. When the
gate sends the PR back, a fresh headless Claude fixes it in a temporary copy, and the new version goes round again,
until it merges or goes to a person. Your own files are never touched.
"""
from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_data  # noqa: E402
import run_reviewer as runner  # noqa: E402
from gate import route  # noqa: E402
from review_pipeline import QUEUE, ROUTES, review_one  # noqa: E402
from run_checks import check_pr  # noqa: E402

NOTES = Path("my-work/notes.md")
HARD_LIMIT = 4  # stops a gate with no limit of its own from looping for the rest of the session
WIDTH = 100
AUTHOR = """You wrote this pull request, and it was sent back. The code is in the current directory, with your PR already applied.
Fix what the feedback found, with the smallest change that does it properly, and keep to what the PR set out to do.
Read the code your change calls before you edit. Edit only files under appointment_reminders/. Don't weaken tests.
End with one JSON object: {"description": "the PR's description, updated so it's true of the new code, on one line", "changed": "one sentence on what you changed"}"""


class Stop(Exception):
    """A round that can't go on, with why."""


def say(text: str, indent: int = 4) -> None:
    print(textwrap.fill(text, WIDTH, initial_indent=" " * indent, subsequent_indent=" " * (indent + 2)))


def git(cwd: Path, *args: str) -> str:
    identity = ["-c", "user.name=Workshop", "-c", "user.email=workshop@example.com", "-c", "commit.gpgsign=false"]
    return subprocess.run(["git", *identity, *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def fix(pr_text: str, feedback: str) -> tuple[str, str]:
    """Claude's new version of the PR, and what it says it changed. The PR is "" if Claude reverted all of it."""
    head, _, body = pr_text.partition("\n\n")
    with tempfile.TemporaryDirectory(prefix="loop-fix-") as call:
        work = Path(call, "code")
        shutil.copytree("appointment_reminders", work / "appointment_reminders", ignore=shutil.ignore_patterns("__pycache__"))
        git(work, "init", "-q")
        git(work, "add", "-A")
        git(work, "commit", "-qm", "base")
        Path(call, "pr.diff").write_text(body)
        git(work, "apply", "../pr.diff")
        reply = runner.run_claude(f"{pr_text}\n\nFeedback:\n{feedback}", AUTHOR, "", str(work), runner.AUTHOR_MODEL, author=True)
        if "error" in reply:
            raise Stop(f"Claude's fix failed: {reply['error']}")
        try:
            said = runner.last_json(reply.get("result") or "", "changed")
        except ValueError:
            raise Stop("Claude's fix didn't end with the JSON it was asked for, so the loop stops here.")
        git(work, "add", "-A")
        diff = git(work, "diff", "--cached")
    title = head.splitlines()[0]
    description = str(said.get("description") or "").replace("\n", " ")
    return (f"{title}\nDescription: {description}\n\n{diff}" if diff else ""), str(said.get("changed", ""))


def one_round(name: str, pr_text: str, fixes: int, code: str, specialist: tuple[str, str] | None) -> tuple[str, str, str]:
    """Where this version of the PR goes, why, and the feedback for Claude if it goes back."""
    blocks = [finding for _, level, finding in check_pr(pr_text) if level == "block"]
    if blocks:
        rules = ", ".join(sorted({f.rule for f in blocks}))
        return "claude", f"your checks blocked it ({rules})", "\n".join(f"{f.rule}: {f.message}" for f in blocks)
    print(f"  Reviewing{' and asking your specialist' if specialist else ''}...", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, f"{name}.diff")
        path.write_text(pr_text)
        review = review_one(path, runner.system_prompt(runner.AGENT), runner.agent_tools(runner.AGENT), code, specialist)
        pr = dataclasses.replace(pr_data.load_pr(path), fixes=fixes)
    where, why = route(pr, review)
    if where not in ROUTES:
        raise SystemExit(f"route() sent {name} to {where!r}. It must return \"merge\", \"claude\" or \"human\".")
    said = review.verdict or "nothing, it failed"
    for finding in review.findings:
        say(f"{finding.get('rule')}: {finding.get('why', '')}")
    return where, f"reviewer said {said}: {why}", "\n".join(f"{f.get('rule')}: {f.get('why')}" for f in review.findings)


def find(name: str) -> Path:
    found = sorted(Path("data/review-prs").glob(f"*/{name}.diff"))
    if not found:
        raise SystemExit(f"There's no open PR called {name}. Try one the pipeline sent back to Claude, such as pr-03. The holdout is sealed.")
    return found[0]


def note(name: str, ending: str, fixes: int) -> None:
    """A line in notes.md for every loop that ran, so you (and Claude) can see which ones you've done."""
    if NOTES.exists():
        with NOTES.open("a") as out:
            out.write(f"- {time.strftime('%H:%M')} loop {name} | {ending} after {fixes} fix{'' if fixes == 1 else 'es'}\n")


def main(name: str) -> int:
    pr_text = find(name).read_text()
    runner.check_agent(runner.AGENT)
    gate_agent = runner.GATE_AGENT
    specialist = (runner.system_prompt(gate_agent), runner.agent_tools(gate_agent)) if runner.written(gate_agent) else None
    code = runner.code_copy()
    where = ""
    try:
        for fixes in range(HARD_LIMIT + 1):
            print(f"\nRound {fixes + 1}: {pr_text.splitlines()[0]}")
            where, why, feedback = one_round(name, pr_text, fixes, code, specialist)
            print(f"  -> {where}: {why}")
            if where != "claude":
                if fixes == 0:
                    print("\nNothing to fix. Try one the pipeline sent back to Claude.")
                    return 0
                break
            if fixes == HARD_LIMIT:
                print(f"\nStopped after {HARD_LIMIT} fixes. Your gate has no limit on fixes.")
                break
            print(f"  Claude is fixing it ({runner.AUTHOR_MODEL})...", flush=True)
            pr_text, changed = fix(pr_text, feedback)
            say(f"Claude: {changed}", 2)
            if not pr_text:
                print("\nClaude reverted the whole change, so there's nothing left to merge.")
                note(name, "reverted", fixes + 1)
                return 0
    except Stop as stopped:
        print(f"\n{stopped}")
        return 1
    finally:
        shutil.rmtree(code, ignore_errors=True)
    print(f"\nFinal PR:\n\n{pr_text}")
    note(name, "to a person" if where == "human" else "merged" if where == "merge" else f"stopped at {where}", fixes)
    if where == "human":
        with QUEUE.open("a") as queue:
            queue.write(f"## {name}, after ./lab loop\n\n```diff\n{pr_text}\n```\n\n")
        print(f"It went to a person, so it's in {QUEUE}.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: ./lab loop PR, such as ./lab loop pr-03")
    raise SystemExit(main(sys.argv[1]))
