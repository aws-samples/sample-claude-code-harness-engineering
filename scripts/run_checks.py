#!/usr/bin/env python3
"""One script that runs all the team's deterministic checks. Fill in the two TODOs with Claude, from my-work/2-checks-plan.md.

  python3 scripts/run_checks.py FILE...       check these files
  python3 scripts/run_checks.py --staged      check what's staged, for a git pre-commit hook
  python3 scripts/run_checks.py --from-hook   read a Claude Code hook's JSON from stdin, for any hook event

A check that blocks makes the script exit 2. A Claude Code hook or a git hook treats that as a stop, and Claude reads the message.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE = "appointment_reminders/"  # the checks only look at the service


@dataclass
class Finding:
    rule: str
    line: int
    message: str  # tell whoever hit it how to fix it


# TODO: your decisions from the plan. {"R2": ("block", "new")}, where the second word is "new" or "all".
POLICY: dict[str, tuple[str, str]] = {}


def check_source(path: str, source: str) -> list[Finding]:
    """Findings for one file, given its path from the repo root, such as appointment_reminders/app/api/health.py."""
    # TODO: one check for each rule in your plan.
    return []


def _at_head(path: str) -> str:
    done = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=ROOT, capture_output=True, text=True)
    return done.stdout if done.returncode == 0 else ""


def _text_of(source: str, finding: Finding) -> str:
    lines = source.splitlines()
    return lines[finding.line - 1].strip() if 0 < finding.line <= len(lines) else ""


def findings_for(path: str, source: str) -> list[Finding]:
    """Apply each rule's scope: a "new" rule ignores what was already there at the last commit."""
    found = check_source(path, source)
    old_source = _at_head(path)
    old = Counter((f.rule, _text_of(old_source, f)) for f in check_source(path, old_source))
    kept = []
    for finding in found:
        key = (finding.rule, _text_of(source, finding))
        if POLICY.get(finding.rule, ("block", "new"))[1] == "new" and old[key] > 0:
            old[key] -= 1  # the same problem at the same text was already there
            continue
        kept.append(finding)
    return kept


def _relative(name: str) -> str | None:
    try:
        return str((ROOT / name).resolve().relative_to(ROOT))
    except ValueError:
        return None


def _git_files(*git_args: str) -> list[str]:
    done = subprocess.run(["git", *git_args, "-z"], cwd=ROOT, capture_output=True, text=True)
    return [name for name in done.stdout.split("\0") if name]


def _changed_files() -> list[str]:
    """Everything that differs from the last commit, including new files that aren't staged yet."""
    return _git_files("diff", "HEAD", "--name-only") + _git_files("ls-files", "-o", "--exclude-standard")


def _read(path: str, staged: bool) -> str | None:
    """The file's text, as staged if that's what's being committed. None if it's gone or isn't text."""
    if staged:
        done = subprocess.run(["git", "show", f":{path}"], cwd=ROOT, capture_output=True)
        data = done.stdout if done.returncode == 0 else None
    else:
        data = (ROOT / path).read_bytes() if (ROOT / path).is_file() else None
    try:
        return data.decode() if data is not None else None
    except UnicodeDecodeError:
        return None


def _about_to_write(event: dict, path: str) -> str | None:
    """A PreToolUse hook runs before the write lands, so check what the file is about to become."""
    if event.get("hook_event_name") != "PreToolUse":
        return None
    tool_input = event.get("tool_input") or {}
    if "content" in tool_input:
        return tool_input["content"]
    current = _read(path, staged=False) or ""
    edits = tool_input.get("edits") or ([tool_input] if "new_string" in tool_input else [])
    for edit in edits:
        count = -1 if edit.get("replace_all") else 1
        current = current.replace(edit.get("old_string", ""), edit.get("new_string", ""), count)
    return current if edits else None


def _files_from_hook(event: dict) -> list[str]:
    """Whichever event you chose: a write gives one file, a git commit or the end of a turn gives everything that's changed, since the command may also run git add."""
    if event.get("stop_hook_active"):
        return []  # Claude has already been told once this turn, so don't trap it in a loop
    tool_input = event.get("tool_input") or {}
    if event.get("tool_name") == "Bash":
        return _changed_files() if "git commit" in tool_input.get("command", "") else []
    if tool_input.get("file_path"):
        return [tool_input["file_path"]]
    return _changed_files()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--from-hook", action="store_true")
    args = parser.parse_args()
    event = {}
    if args.from_hook:
        try:
            event = json.load(sys.stdin)
        except ValueError:
            pass
    names = _files_from_hook(event) if args.from_hook else _git_files("diff", "--cached", "--name-only") if args.staged else args.files
    worst = 0
    warnings = []
    for name in names:
        path = _relative(name)
        if not path or not path.startswith(CODE):
            continue
        source = _about_to_write(event, path)
        source = source if source is not None else _read(path, args.staged)
        if source is None:
            continue
        for finding in findings_for(path, source):
            level = POLICY.get(finding.rule, ("block", "new"))[0]
            line = f"{level.upper()} {finding.rule} {path}:{finding.line} {finding.message}"
            print(line, file=sys.stderr)
            worst = max(worst, 2 if level == "block" else 0)
            if level != "block":
                warnings.append(line)
    if warnings and not worst and event.get("hook_event_name") == "PostToolUse":
        # A hook's stderr only reaches Claude on a block, so a warning has to go this way.
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n".join(warnings)}}))
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
