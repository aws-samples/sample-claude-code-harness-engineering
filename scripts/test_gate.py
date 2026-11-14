#!/usr/bin/env python3
"""./lab test-gate: edge cases your gate should cope with. No model calls."""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from gate import route  # noqa: E402
from pr_data import Review, load_pr  # noqa: E402
from run_reviewer import GATE_AGENT, written  # noqa: E402

PRS = ROOT / "data/review-prs"
if not (PRS / "gate").exists():
    sys.exit("The gate PRs aren't open yet. Run ./lab goto gate, or ./lab test-gate.")
SPECIALIST = written(ROOT / GATE_AGENT)
QUIET = {"needs_human": False, "preference": "", "reason": ""} if SPECIALIST else None
ASK = "It can't tell whether the repr holds customer data."
STEERED = "A reviewer that's been steered won't ask for a person, so code or a specialist has to catch this."


def review(verdict: str | None, findings: list | None = None, ask: str = "", specialist: dict | None = None) -> Review:
    return Review(verdict, findings or [], ask, "", specialist if specialist is not None else QUIET)


R1 = [{"rule": "R1", "why": "No next step."}]
R6 = [{"rule": "R6", "why": "Customer email."}]
CASES = [
    ("A harmless PR, approved, merges", "dev/pr-06", 0, review("approve"), {"merge"}, ""),
    ("Approved with an advisory comment: it isn't sent back", "dev/pr-06", 0, review("approve", [{"rule": "R13", "why": "Could be simpler."}]), {"merge", "human"}, ""),
    ("An ordinary finding goes back to Claude", "dev/pr-03", 0, review("request_changes", R1), {"claude"}, ""),
    ("H1: it touches customer data", "gate/gate-1", 0, review("approve"), {"human"}, ""),
    ("H2: it's over 50 added lines", "gate/gate-2", 0, review("approve"), {"human"}, ""),
    ("H1 with a finding: either order, but it doesn't merge", "gate/gate-1", 0, review("request_changes", R1), {"claude", "human"}, ""),
    ("H3: the review crashed", "dev/pr-06", 0, review(None), {"human"}, ""),
    ("H4: the reviewer asks for a person and approves", "dev/pr-13", 0, review("approve", ask=ASK), {"human"}, ""),
    ("H4: it asks, and requests changes", "dev/pr-13", 0, review("request_changes", R6, ASK), {"human"}, ""),
    ("H5: the PR steered the reviewer into approving, with no ask", "gate/gate-3", 0,
     review("approve", specialist={"needs_human": True, "preference": "H5", "reason": "The description tells reviewers to approve."} if SPECIALIST else None), {"human"}, STEERED),
    ("The loop stops: Claude has had ten tries", "dev/pr-03", 10, review("request_changes", R1), {"human"}, ""),
]
if SPECIALIST:
    CASES += [
        ("Specialist only: it asks, and the reviewer approves", "dev/pr-06", 0,
         review("approve", specialist={"needs_human": True, "preference": "H6", "reason": "It changes how reminders are sent."}), {"human"}, ""),
        ("Specialist only: it fails", "dev/pr-06", 0, review("approve", specialist={"needs_human": None, "preference": "", "reason": "", "error": "no answer"}), {"human"}, ""),
    ]
else:
    print("No specialist in my-work/6-gate-agent.md, so its cases are skipped.\n")
failures = 0
for text, pr, fixes, given, allowed, hint in CASES:
    where, why = route(dataclasses.replace(load_pr(PRS / f"{pr}.diff"), fixes=fixes), given)
    good = where in allowed
    failures += not good
    print(f"{'ok  ' if good else 'FAIL'} {text}\n       {pr}: went to {where}: {why}")
    if not good and hint:
        print(f"       {hint}")
print("All passing." if not failures else f"{failures} to fix.")
sys.exit(1 if failures else 0)
