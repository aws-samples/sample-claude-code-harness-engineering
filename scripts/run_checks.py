#!/usr/bin/env python3
"""Runs your checks from scripts/checks.py. You don't need to change this file.

  python3 scripts/run_checks.py FILE...    check these files
  python3 scripts/run_checks.py --staged   check what's staged, for the git pre-commit hook
  python3 scripts/run_checks.py --pr DIFF  check what a PR would add, as the hook would check its commit

A check that blocks makes the script exit 1, which stops the commit. Claude reads the message.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from checks import POLICY, SCOPE, check_source  # noqa: E402

CODE = "appointment_reminders/"  # the checks only look at the service


def level_of(rule: str) -> str:
    """ "block" or "warn", however POLICY spells it. Anything unclear blocks, because a missed block is the worse mistake."""
    return "warn" if str(POLICY.get(rule, "block")).strip().lower().startswith("warn") else "block"


def new_only() -> bool:
    return not str(SCOPE).strip().lower().startswith("all")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True)


def _text_of(source: str, finding) -> str:
    lines = source.splitlines()
    return lines[finding.line - 1].strip() if 0 < finding.line <= len(lines) else ""


def findings_for(path: str, source: str) -> list:
    """With SCOPE "new", a problem that was already there at the last commit is left alone."""
    at_head = _git("show", f"HEAD:{path}")
    return findings_against(path, source, at_head.stdout.decode(errors="replace") if at_head.returncode == 0 else "")


def findings_against(path: str, source: str, old_source: str) -> list:
    """Findings in source. With SCOPE "new", those already in old_source are left alone."""
    found = check_source(path, source)
    if not new_only():
        return found
    old = Counter((f.rule, _text_of(old_source, f)) for f in check_source(path, old_source))
    kept = []
    for finding in found:
        key = (finding.rule, _text_of(source, finding))
        if old[key] > 0:
            old[key] -= 1  # the same problem at the same text was already there
            continue
        kept.append(finding)
    return kept


def check_pr(diff_text: str) -> list:
    """(path, level, finding) for each problem a PR's diff would bring in, against the code as it is now."""
    body = diff_text.partition("\n\n")[2]
    found = []
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp)
        shutil.copytree(ROOT / CODE, copy / CODE, ignore=shutil.ignore_patterns("__pycache__"))
        (copy / "pr.diff").write_text(body)
        subprocess.run(["git", "apply", "pr.diff"], cwd=copy, check=True, capture_output=True)
        for path in re.findall(r"^\+\+\+ b/(\S+)", body, re.M):
            if not path.startswith(CODE) or not (copy / path).is_file():
                continue
            before = (ROOT / path).read_text() if (ROOT / path).is_file() else ""
            found += [(path, level_of(f.rule), f) for f in findings_against(path, (copy / path).read_text(), before)]
    return found


def _read(path: str, staged: bool) -> str | None:
    """The file's text, as staged if that's what's being committed. None if it's gone or isn't text."""
    if staged:
        done = _git("show", f":{path}")
        data = done.stdout if done.returncode == 0 else None
    else:
        data = (ROOT / path).read_bytes() if (ROOT / path).is_file() else None
    try:
        return data.decode() if data is not None else None
    except UnicodeDecodeError:
        return None


def _relative(name: str) -> str | None:
    try:
        return str((ROOT / name).resolve().relative_to(ROOT))
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--pr", help="a PR's .diff file")
    args = parser.parse_args()
    if args.pr:
        found = check_pr(Path(args.pr).read_text())
        for path, level, finding in found:
            print(f"{level.upper()} {finding.rule} {path}:{finding.line} {finding.message}", file=sys.stderr)
        return 1 if any(level == "block" for _, level, _ in found) else 0
    names = _git("diff", "--cached", "--name-only", "-z").stdout.decode().split("\0") if args.staged else args.files
    blocked = False
    for name in filter(None, names):
        path = _relative(name)
        source = _read(path, args.staged) if path and path.startswith(CODE) else None
        if source is None:
            continue
        for finding in findings_for(path, source):
            level = level_of(finding.rule)
            print(f"{level.upper()} {finding.rule} {path}:{finding.line} {finding.message}", file=sys.stderr)
            blocked = blocked or level == "block"
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
