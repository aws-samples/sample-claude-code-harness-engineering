#!/usr/bin/env python3
"""Scores your reviewer's last run with your scorer in scripts/score.py, against the lead's labels.

  ./lab eval             runs the reviewer on the dev PRs, then this
  ./lab score            your last ./lab eval again
  ./lab score --results data/eval-fixtures/always-approves.json

It shows where your reviewer and the lead disagree, a table of every PR, and your measures last, so they're on screen.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import textwrap
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

LABELS = {"dev": ROOT / "data/review-prs/lead-labels.csv", "holdout": ROOT / "data/review-prs/holdout/labels.csv"}
PRS = {"dev": ROOT / "data/review-prs/dev", "holdout": ROOT / "data/review-prs/holdout"}
LAST_EVAL = ROOT / ".claude/last-eval.json"
NOTES = ROOT / "my-work/notes.md"


def read_labels(pr_set: str) -> dict[str, dict]:
    path = LABELS[pr_set]
    return {row["pr"]: row for row in csv.DictReader(path.open(newline=""))} if path.exists() else {}


NOT_BUILT = "Build your scorer first: run /design-eval in Claude, or ./lab catch-up scorer."


def scorer_problem() -> str:
    """What's wrong with the scorer, or "" when it's built: score() returns a dict with clears_bar. It's tried the way
    the eval calls it, with one answer for every labeled PR, here from a reviewer that failed on all of them."""
    labels = read_labels("dev")
    try:
        from score import score
        measures = score(labels, {name: {"verdict": None, "findings": []} for name in labels})
    except Exception as exc:  # the participant's code can fail any way
        return f"Your scorer raised {type(exc).__name__}: {exc}, on a reviewer that failed on every PR. Fix scripts/score.py, and check it with ./lab test-scorer."
    return "" if isinstance(measures, dict) and "clears_bar" in measures else NOT_BUILT


def scorer_built() -> bool:
    return not scorer_problem()


def wanted(label: dict) -> list[str]:
    return [rule.strip() for rule in (label.get("rules") or "").split(";") if rule.strip()]


def needs_changes(label: dict) -> bool:
    return label.get("needs_changes", "").strip().lower() == "yes"


def lead_says(label: dict) -> str:
    return ", ".join(wanted(label)) or "R?" if needs_changes(label) else "fine"


def reviewer_says(answer: dict) -> str:
    rules = ", ".join(dict.fromkeys(str(f.get("rule")) for f in answer.get("findings", [])))  # each rule once, in order
    verdict = answer.get("verdict")
    if verdict is None:
        said = "no answer"
    elif verdict == "request_changes":
        said = f"changes: {rules}" if rules else "changes"
    else:
        said = f"approve (comment: {rules})" if rules else "approve"
    said += " (asks a person)" if answer.get("ask_human") else ""
    return said if len(said) <= 30 else said[:29] + "…"


def disagrees(label: dict, answer: dict) -> bool:
    """A different verdict from the label, or a labeled rule not named. The same whatever the scorer counts."""
    verdict = answer.get("verdict")
    if verdict != ("request_changes" if needs_changes(label) else "approve"):
        return True
    named = {str(f.get("rule")) for f in answer.get("findings", [])}
    return needs_changes(label) and not set(wanted(label)) <= named


def checks_on(pr_set: str, names: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    """What your checks would say about each PR: warnings to show, and blocks, which never reach the reviewer."""
    try:
        from run_checks import check_pr
        warned, blocked = {}, {}
        for name in names:
            path = PRS[pr_set] / f"{name}.diff"
            found = check_pr(path.read_text()) if path.exists() else []
            warns = sorted({f.rule for _, level, f in found if level == "warn"})
            blocks = sorted({f.rule for _, level, f in found if level == "block"})
            if warns:
                warned[name] = "warn " + ", ".join(warns)
            if blocks:
                blocked[name] = blocks
        return warned, blocked
    except Exception as exc:  # the participant's checks shouldn't stop the eval
        print(f"Your checks raised {type(exc).__name__}: {exc}. Scoring without them.")
        return {}, {}


def safe_result(result, label: dict, answer: dict) -> str:
    try:
        return str(result(label, answer))
    except Exception as exc:
        return f"error: {type(exc).__name__}"


def comparison(changed: int) -> str:
    """Whether the reviewer changed since the last ./lab eval, from the fingerprint lab writes. "" when there's nothing to compare."""
    try:
        state = json.loads(LAST_EVAL.read_text())
    except (OSError, ValueError):
        return ""
    if not state.get("previous"):
        return ""
    if state.get("fingerprint") == state.get("previous"):
        return f"Same reviewer as last run, {changed} result{'s' if changed != 1 else ''} changed (noise)."
    return f"Reviewer changed since last run, {changed} result{'s' if changed != 1 else ''} changed."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--set", choices=["dev", "holdout"], default="dev")
    parser.add_argument("--compare", default="", help="an earlier results file, to mark what changed")
    parser.add_argument("--note", default="", help="what you changed, for my-work/notes.md")
    parser.add_argument("--record", action="store_true", help="add a line to my-work/notes.md")
    parser.add_argument("--agent", default="", help="the reviewer file, if it wasn't yours")
    parser.add_argument("--model", default="", help="the model the reviewer ran on, for the notes line")
    parser.add_argument("--tools", default="", help="the reviewer's tools, for the notes line")
    args = parser.parse_args()
    labels = read_labels(args.set)
    if not labels:
        raise SystemExit("The holdout is sealed. To run it: ./lab holdout" if args.set == "holdout" else "The lead's labels aren't open yet: ./lab goto scorer")
    problem = scorer_problem()
    if problem:
        raise SystemExit(problem)
    from score import result, score
    path = Path(args.results)
    if not path.exists():
        raise SystemExit(f"No results in {args.results} yet. Run {'./lab holdout' if args.set == 'holdout' else './lab eval'} first.")
    results = json.loads(path.read_text())
    if any(isinstance(answer, list) for answer in results.values()):
        raise SystemExit(f"{args.results} holds several runs of each PR. The scorer takes one: run ./lab eval twice instead.")
    previous = json.loads(Path(args.compare).read_text()) if args.compare and Path(args.compare).exists() else {}
    names = sorted(labels)
    warned, blocked = checks_on(args.set, names)
    answers = {name: results.get(name, {"verdict": None, "findings": []}) for name in names}

    shown = [name for name in names if name not in blocked and disagrees(labels[name], answers[name])]
    if shown:
        print("Where your reviewer and the lead disagree")
        for name in shown:
            finding = next(iter(answers[name].get("findings") or []), {})
            said = f"{finding.get('rule')}: {finding.get('why', '')}" if finding else (answers[name].get("error") or reviewer_says(answers[name]))
            print(f"  {name:<6} lead: {lead_says(labels[name])}. {textwrap.shorten(labels[name].get('reason', ''), 150)}")
            print(f"         reviewer: {textwrap.shorten(str(said), 200)}\n")
    changed = 0
    print(f"  {'PR':<6} {'Lead says':<11} {'Reviewer says':<30} {'Checks':<10} {'Result':<13} Since last run")
    for name in names:
        if name in blocked:
            continue
        now = safe_result(result, labels[name], answers[name])
        before = safe_result(result, labels[name], previous[name]) if name in previous and not isinstance(previous[name], list) else ""
        since = f"was: {before}" if before and before != now else ""
        changed += bool(since)
        print(f"  {name:<6} {lead_says(labels[name]):<11} {reviewer_says(answers[name]):<30} {warned.get(name, ''):<10} {now:<13} {since}".rstrip())
    if blocked:
        agrees = lambda name: "the lead agrees" if needs_changes(labels[name]) else "the lead says it's fine"
        print("\nBlocked by your checks, so not scored: " + ", ".join(f"{name} ({', '.join(rules)}, {agrees(name)})" for name, rules in blocked.items()))
    scored_labels = {name: label for name, label in labels.items() if name not in blocked}
    try:
        measures = score(scored_labels, {name: answers[name] for name in scored_labels})
    except Exception as exc:  # the participant's code: say what broke, and that the reviews are saved
        raise SystemExit(f"\nYour scorer raised {type(exc).__name__}: {exc}\nFix scripts/score.py, then run ./lab score. The reviews are saved, so there's no need to run the reviewer again.")
    line = comparison(changed) if previous else ""
    print(f"\n{line}" if line else "")
    for key, value in measures.items():
        if key != "clears_bar":
            print(f"{key}: {value}")
    print(f"Clears your bar: {'yes' if measures.get('clears_bar') else 'no'}")
    if args.record and NOTES.exists():
        about = f"{args.set}, {args.model or 'haiku'}, tools: {args.tools or 'none'}"
        about += f", note: {args.note}" if args.note else ""
        about += f", reviewer: {args.agent}" if args.agent else ""
        with NOTES.open("a") as out:
            out.write(f"- {time.strftime('%H:%M')} {about} | " + "; ".join(f"{key}: {value}" for key, value in measures.items()) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
