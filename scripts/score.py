"""Your scorer. Build score() with Claude, from my-work/4-eval-design.md. scripts/eval_reviewer.py runs it."""
from __future__ import annotations


def score(labels: dict[str, dict], results: dict[str, dict]) -> dict[str, float | int | str]:
    """Your measures, from my-work/4-eval-design.md. ./lab score prints what this returns.

    labels[pr]  has needs_changes ("yes" or "no"), rules ("R5;R6") and reason.
    results[pr] has verdict ("approve", "request_changes", or None if the call failed) and findings ([{"rule", "why"}]).
    """
    # TODO: build this with Claude. Print each error as you go, so that you can read them.
    raise SystemExit("score() isn't built yet. Ask Claude to build it from my-work/4-eval-design.md, or take ours with ./lab catch-up eval.")
