#!/usr/bin/env python3
"""Runs your scorer from scripts/score.py against the gold labels. You don't need to change this file.

  ./lab score            your last ./lab review dev
  ./lab score holdout    your last ./lab review holdout
  ./lab score --results data/eval-fixtures/always-approves.json

Before you trust your scorer, try it on the canned agents in data/eval-fixtures/: one approves everything, one flags everything.
Neither should look good.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from my_work import my_labels, unclear_labels  # noqa: E402
from score import score  # noqa: E402


def _read(path: Path) -> dict[str, dict]:
    return {row["pr"]: row for row in csv.DictReader(path.open(newline=""))} if path.exists() else {}


def load_labels(pr_set: str) -> dict[str, dict]:
    """Gold labels: the lead's, with yours replacing them on the PRs you labeled."""
    if pr_set == "holdout":
        return _read(ROOT / "data/review-prs/holdout/labels.csv")
    return {**_read(ROOT / "data/review-prs/lead-labels.csv"), **my_labels()}


def show_disagreements() -> None:
    """Where you and the lead differ. Two careful people disagreeing is the ceiling on any reviewer."""
    lead = _read(ROOT / "data/review-prs/lead-labels.csv")
    for pr, mine in my_labels().items():
        if pr in lead and mine["needs_changes"] != lead[pr]["needs_changes"]:
            print(f"you and the lead differ on {pr}: you said {mine['needs_changes']}, lead said {lead[pr]['needs_changes']} ({lead[pr]['rules'] or 'no rule'}): {lead[pr]['reason']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--set", choices=["dev", "holdout"], default="dev")
    args = parser.parse_args()
    if args.set == "holdout" and not (ROOT / "data/review-prs/holdout/labels.csv").exists():
        raise SystemExit("The held-out PRs aren't open yet. When you're ready: ./lab goto holdout")
    if args.set == "dev" and not (ROOT / "data/review-prs/lead-labels.csv").exists():
        raise SystemExit("The lead's labels aren't open yet. When you're ready: ./lab goto eval")
    labels = load_labels(args.set)
    if args.set == "dev":
        for pr, cell in unclear_labels().items():
            print(f"Couldn't tell whether {cell!r} means yes or no for {pr}, so the lead's label is used. Edit my-work/4-gold-labels.md to change that.")
    if not Path(args.results).exists():
        raise SystemExit(f"No results in {args.results} yet. Run ./lab review {args.set} first.")
    results = json.loads(Path(args.results).read_text())
    missing = sorted(pr for pr in labels if results.get(pr, {}).get("verdict") is None)
    if missing:
        print(f"No answer from the agent on {len(missing)} PRs: {', '.join(missing)}")
    if args.set == "dev":
        show_disagreements()
    for name, value in score(labels, results).items():
        print(f"{name}: {value}")
    print("The labels cover every rule. A miss on a rule your checks own may be fine, since the checks catch it: read it rather than count it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
