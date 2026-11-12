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
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from score import score  # noqa: E402


def _read(path: Path) -> dict[str, dict]:
    return {row["pr"]: row for row in csv.DictReader(path.open(newline=""))} if path.exists() else {}


def load_labels(pr_set: str) -> dict[str, dict]:
    """Gold labels: the lead's good answer for each PR."""
    return _read(ROOT / ("data/review-prs/holdout/labels.csv" if pr_set == "holdout" else "data/review-prs/lead-labels.csv"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="results.json")
    parser.add_argument("--set", choices=["dev", "holdout"], default="dev")
    args = parser.parse_args()
    if args.set == "holdout" and not (ROOT / "data/review-prs/holdout/labels.csv").exists():
        raise SystemExit("The held-out PRs aren't open yet. When you're ready: ./lab goto holdout")
    if args.set == "dev" and not (ROOT / "data/review-prs/lead-labels.csv").exists():
        raise SystemExit("The lead's labels aren't open yet. When you're ready: ./lab goto label")
    labels = load_labels(args.set)
    if not Path(args.results).exists():
        raise SystemExit(f"No results in {args.results} yet. Run ./lab review {args.set} first.")
    results = json.loads(Path(args.results).read_text())
    missing = sorted(pr for pr in labels if results.get(pr, {}).get("verdict") is None)
    if missing:
        print(f"No answer from the agent on {len(missing)} PRs: {', '.join(missing)}")
    measures = score(labels, results)
    for name, value in measures.items():
        print(f"{name}: {value}")
    notes = ROOT / "my-work/notes.md"
    if args.results in ("results.json", "results-holdout.json") and notes.exists():  # a record of each run, to see what each change did
        with notes.open("a") as out:
            out.write(f"- {time.strftime('%H:%M')} {args.set}: " + "; ".join(f"{name}: {value}" for name, value in measures.items()) + "\n")
        print("Added to my-work/notes.md.")
    print("The labels cover every rule. A miss on a rule your checks own may be fine, since the checks catch it: read it rather than count it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
