"""Your scorer. Reference solution, from ./lab catch-up scorer. scripts/eval_reviewer.py runs it."""
from __future__ import annotations

from collections import Counter

MAX_MISSES = 0
MAX_FALSE_ALARMS = 2
MAX_EXTRA_RULES_PER_PROBLEM_PR = 1  # on average, so one chatty review doesn't fail the bar


def _wanted(label: dict) -> set[str]:
    return {rule.strip() for rule in (label["rules"] or "").split(";") if rule.strip()}


def _named(answer: dict) -> set[str]:
    return {str(finding.get("rule")) for finding in answer.get("findings", [])}


def _needs_changes(label: dict) -> bool:
    return label["needs_changes"].strip().lower() == "yes"


def result(label: dict, answer: dict) -> str:
    """One PR's result, shown in the table. No answer counts against the reviewer."""
    verdict = answer.get("verdict")
    if not _needs_changes(label):
        return "correct" if verdict == "approve" else "false alarm"
    if verdict != "request_changes":
        return "missed"
    return "caught" if _wanted(label) <= _named(answer) else "wrong rule"


def score(labels: dict[str, dict], results: dict[str, dict]) -> dict[str, float | int | str | bool]:
    """Your measures, ending with clears_bar."""
    counts = Counter(result(label, results.get(pr, {})) for pr, label in labels.items())
    problems = [pr for pr, label in labels.items() if _needs_changes(label)]
    extra = sum(len(_named(results.get(pr, {})) - _wanted(labels[pr])) for pr in problems)
    return {
        "caught": f"{counts['caught']} of {len(problems)}",
        "right verdict, wrong rule": counts["wrong rule"],
        "false alarms": f"{counts['false alarm']} of {len(labels) - len(problems)}",
        "extra rules named": extra,
        "clears_bar": len(problems) - counts["caught"] <= MAX_MISSES
        and counts["false alarm"] <= MAX_FALSE_ALARMS
        and extra <= MAX_EXTRA_RULES_PER_PROBLEM_PR * len(problems),
    }
