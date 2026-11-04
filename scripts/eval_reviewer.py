#!/usr/bin/env python3
"""Score your reviewer agent. The plumbing is done. Build score() with Claude, from my-work/5-eval-design.md.

  ./lab score            your last ./lab review dev
  ./lab score holdout    your last ./lab review holdout
  ./lab score --results data/eval-fixtures/always-approves.json

Before you trust it, try it on the canned agents in data/eval-fixtures/: one approves everything, one flags everything.
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
from my_work import my_labels, sort_finished, sorted_rules, unclear_labels  # noqa: E402


def _read(path: Path) -> dict[str, dict]:
    return {row["pr"]: row for row in csv.DictReader(path.open(newline=""))} if path.exists() else {}


def rules_for_reviewer() -> set[str] | None:
    """The rules you gave the reviewer. A PR about a rule your checks own isn't the reviewer's to catch."""
    return set(sorted_rules("reviewer", "both")) if sort_finished() else None


def load_labels(pr_set: str) -> dict[str, dict]:
    """Gold labels: the lead's, with yours replacing them on the PRs you labeled. Rows you left unfinished keep the lead's."""
    if pr_set == "holdout":
        labels = _read(ROOT / "data/review-prs/holdout/labels.csv")
    else:
        labels = _read(ROOT / "data/review-prs/lead-labels.csv")
        labels.update(my_labels())
    scope = rules_for_reviewer()
    if scope is None:
        return labels
    in_scope = {}
    for pr, label in labels.items():
        rules = {r.strip() for r in (label["rules"] or "").split(";") if r.strip()}
        if not rules or rules & scope:
            in_scope[pr] = label
        else:
            print(f"left out {pr}: {','.join(sorted(rules))} isn't a rule you gave the reviewer")
    return in_scope


def show_disagreements() -> None:
    """Where you and the lead differ. Two careful people disagreeing is the ceiling on any reviewer."""
    lead = _read(ROOT / "data/review-prs/lead-labels.csv")
    for pr, mine in my_labels().items():
        if pr in lead and mine["needs_changes"] != lead[pr]["needs_changes"]:
            print(f"you and the lead differ on {pr}: you said {mine['needs_changes']}, lead said {lead[pr]['needs_changes']} ({lead[pr]['rules'] or 'no rule'}): {lead[pr]['reason']}")


def score(labels: dict[str, dict], results: dict[str, dict]) -> dict[str, float | int | str]:
    """Your measures, from my-work/5-eval-design.md.

    labels[pr]  has needs_changes ("yes" or "no"), rules ("R5;R6") and reason.
    results[pr] has verdict ("approve", "request_changes", or None if the call failed) and findings ([{"rule", "why"}]).
    """
    # TODO: build this with Claude. Print each error as you go, so that you can read them.
    raise SystemExit("score() isn't built yet. Ask Claude to build it from my-work/5-eval-design.md, or take ours with ./lab catch-up eval.")


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
    for pr in unclear_labels():
        print(f"Couldn't read your label for {pr}: use yes or no. Using the lead's for now.")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
