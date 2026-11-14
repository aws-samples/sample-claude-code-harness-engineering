"""Your scorer. Build it with /design-eval, from my-work/4-eval-design.md. scripts/eval_reviewer.py runs it."""
from __future__ import annotations


def result(label: dict, answer: dict) -> str:
    """One PR's result, in a word or two, such as "caught" or "false alarm". It's shown in the table.

    label  has needs_changes ("yes" or "no"), rules ("R5", or "R5;R6" when a PR breaks two) and reason.
    answer has verdict ("approve", "request_changes", or None if the call failed) and findings ([{"rule", "why"}]).
    """
    # TODO: from your design.
    return ""


def score(labels: dict[str, dict], results: dict[str, dict]) -> dict[str, float | int | str | bool]:
    """Your measures over every PR in labels. Include "clears_bar": True or False, from the bar you set."""
    # TODO: from your design.
    return {}
