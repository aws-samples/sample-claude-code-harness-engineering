#!/usr/bin/env python3
"""./lab test-scorer: tries your scorer on fake reviewers, with no model calls. Each should get the score it deserves."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from score import result, score  # noqa: E402

LABELS_FILE = ROOT / "data/review-prs/lead-labels.csv"
if not LABELS_FILE.exists():
    sys.exit("The lead's labels aren't open yet: ./lab goto scorer")
LABELS = {row["pr"]: row for row in csv.DictReader(LABELS_FILE.open(newline=""))}
ALL_RULES = [f"R{n}" for n in range(1, 14)]


def needs_changes(label: dict) -> bool:
    return label["needs_changes"].strip().lower() == "yes"


def answer(verdict: str | None, rules: list[str], why: str = "") -> dict:
    return {"verdict": verdict, "findings": [{"rule": rule, "why": why or "Breaks the rule."} for rule in rules]}


def fixture(name: str) -> dict:
    return json.loads((ROOT / "data/eval-fixtures" / name).read_text())


def perfect() -> dict:
    return {pr: answer("request_changes", label["rules"].split(";")) if needs_changes(label) else answer("approve", []) for pr, label in LABELS.items()}


def chatty() -> dict:
    """Every verdict right, but every rule named on each problem PR. Built here, since a file of it would give away the labels."""
    return {pr: answer("request_changes", ALL_RULES, "Looks risky.") if needs_changes(label) else answer("approve", []) for pr, label in LABELS.items()}


def bar(measures: dict) -> bool | None:
    return measures.get("clears_bar") if isinstance(measures, dict) else None


def try_it(results: dict) -> dict | str:
    try:
        return score(LABELS, results)
    except Exception as exc:  # the test is for the participant's code, so any failure is a finding
        return f"raised {type(exc).__name__}: {exc}"


def show(measures) -> str:
    return measures if isinstance(measures, str) else "; ".join(f"{key}: {value}" for key, value in measures.items())


def main() -> int:
    best = try_it(perfect())
    if isinstance(best, str) or "clears_bar" not in best:
        print("Your scorer isn't built yet: score() has to return a dict that includes \"clears_bar\". Run /design-eval in Claude, or ./lab catch-up scorer.")
        return 1
    cases = [
        ("Approves every PR", fixture("always-approves.json"), lambda m: bar(m) is False, "It approves everything, and it clears your bar"),
        ("Flags every PR", fixture("flags-everything.json"), lambda m: bar(m) is False, "It blocks everything, and it clears your bar"),
        ("Right verdicts, all thirteen rules named", chatty(), lambda m: isinstance(m, dict) and m != best,
         "It gets every verdict right but names all thirteen rules each time, and your scorer rates it as perfect"),
        ("Perfect: the lead's labels", perfect(), lambda m: bar(m) is True, "A perfect reviewer doesn't clear your bar"),
        ("Crashed on every PR", {pr: answer(None, []) for pr in LABELS}, lambda m: bar(m) is False, "A reviewer that crashed on every PR must not pass"),
    ]
    failures = 0
    for name, results, passes, why in cases:
        measures = try_it(results)
        good = not isinstance(measures, str) and passes(measures)
        failures += not good
        print(f"{'ok  ' if good else 'FAIL'} {name}\n       {show(measures)}")
        if not good:
            print(f"       {why}.")
    try:
        result({"needs_changes": "yes", "rules": "R5;R6", "reason": ""}, answer("request_changes", ["R5"]))
        print("ok   A PR that breaks two rules")
    except Exception as exc:
        failures += 1
        print(f"FAIL A PR that breaks two rules\n       result() raised {type(exc).__name__}: {exc}\n       The holdout may have PRs that break two rules.")
    print("All passing." if not failures else f"{failures} to fix.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
