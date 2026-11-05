"""Your scorer. Reference solution: rule-matched recall, and false alarms on clean PRs. scripts/eval_reviewer.py runs it."""
from __future__ import annotations


def score(labels: dict[str, dict], results: dict[str, dict]) -> dict[str, float | int | str]:
    """Your measures, from my-work/5-eval-design.md. ./lab score prints what this returns.

    labels[pr]  has needs_changes ("yes" or "no"), rules ("R5;R6") and reason.
    results[pr] has verdict ("approve", "request_changes", or None if the call failed) and findings ([{"rule", "why"}]).
    """
    caught = missed = false_alarms = clean = wrong_rule = 0
    for pr, label in sorted(labels.items()):
        answer = results.get(pr, {})
        if answer.get("verdict") is None:
            print(f"NO ANSWER    {pr}. It counts against the agent")
            if label["needs_changes"].strip().lower() == "yes":
                missed += 1
            else:
                false_alarms += 1
            continue
        wanted = {r.strip() for r in (label["rules"] or "").split(";") if r.strip()}
        named = {str(f.get("rule")) for f in answer.get("findings", [])}
        flagged = answer["verdict"] == "request_changes"
        if label["needs_changes"].strip().lower() == "yes":
            if flagged and (not wanted or wanted & named):
                caught += 1
            else:
                missed += 1
                wrong_rule += flagged
                print(f"{'WRONG RULE' if flagged else 'MISSED':12} {pr}  you: {label['rules']}  agent: {','.join(sorted(named)) or '-'}")
        elif flagged:
            false_alarms += 1
            print(f"FALSE ALARM  {pr}  agent: {','.join(sorted(named)) or '-'}")
        else:
            clean += 1
    return {"caught, with the right rule": f"{caught} of {caught + missed}", "right verdict, wrong rule": wrong_rule, "false alarms": f"{false_alarms} of {false_alarms + clean}"}
