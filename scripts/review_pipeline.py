#!/usr/bin/env python3
"""The whole system: your checks, then your reviewer and specialist, then your gate routes each PR.

  ./lab pipeline

Runs the sixteen dev PRs and the five gate PRs. A PR your checks block goes back to Claude without a review.
Anything routed to a person lands in human-review-queue.md. Nobody is really alerted.
"""
from __future__ import annotations

import csv
import shutil
import sys
import textwrap
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_data  # noqa: E402
import run_reviewer as runner  # noqa: E402
from gate import route  # noqa: E402
from run_checks import check_pr  # noqa: E402

QUEUE = Path("human-review-queue.md")
NOTES = Path("my-work/notes.md")
ROUTES = ("merge", "claude", "human")
SETS = ("dev", "gate")


def review_one(path: Path, system: str, tools: str, code: str, specialist: tuple[str, str] | None) -> pr_data.Review:
    """The reviewer's answer and the specialist's, made at the same time."""
    diff = path.read_text()
    with ThreadPoolExecutor(max_workers=2) as pool:
        asked = pool.submit(runner.review, diff, system, tools, code)
        checked = pool.submit(runner.gate_check, diff, *specialist, code) if specialist else None
        answer = asked.result()
        said = checked.result() if checked else None
    return pr_data.Review(answer["verdict"], answer["findings"], str(answer.get("ask_human") or ""), answer.get("error", ""), said)


def read_csv(path: Path) -> dict[str, dict]:
    return {row["pr"]: row for row in csv.DictReader(path.open(newline=""))} if path.exists() else {}


def specialist_said(review: pr_data.Review) -> str:
    if review.specialist is None:
        return ""
    needs = review.specialist.get("needs_human")
    return ", specialist: failed" if needs is None else f", specialist: {review.specialist.get('preference') or 'yes'}" if needs else ", specialist: no"


def main() -> int:
    runner.check_agent(runner.AGENT)
    labels = {**read_csv(Path("data/review-prs/lead-labels.csv")), **read_csv(Path("data/review-prs/gate/labels.csv"))}
    wanted = read_csv(Path("data/review-prs/gate/needs-human.csv"))
    paths = [path for name in SETS for path in runner.pr_paths(name, "")]
    if not paths:
        raise SystemExit("No PRs to run. If they aren't open yet: ./lab goto gate")
    sent_back = {}
    for path in paths:
        blocks = sorted({finding.rule for _, level, finding in check_pr(path.read_text()) if level == "block"})
        if blocks:
            sent_back[path] = blocks
    to_review = [path for path in paths if path not in sent_back]
    gate_agent = runner.GATE_AGENT
    specialist = (runner.system_prompt(gate_agent), runner.agent_tools(gate_agent)) if runner.written(gate_agent) else None
    also = ", specialist" if specialist else ""
    print(f"Running your checks, reviewer{also} and gate on {len(paths)} PRs (about a minute).", flush=True)
    system, tools, code = runner.system_prompt(runner.AGENT), runner.agent_tools(runner.AGENT), runner.code_copy()
    try:
        with ThreadPoolExecutor(max_workers=runner.WORKERS) as pool:
            reviews = dict(zip(to_review, pool.map(lambda p: review_one(p, system, tools, code, specialist), to_review)))
    finally:
        shutil.rmtree(code, ignore_errors=True)
    if reviews and all(review.verdict is None for review in reviews.values()):
        first = next(iter(reviews.values())).error
        print(f"Every review failed, so {QUEUE} is unchanged. The first error: {first}")
        return 1
    where_went: dict[str, str] = {}
    with QUEUE.open("w") as queue:
        for path in paths:
            pr = pr_data.load_pr(path)
            label = labels.get(pr.name, {})
            lead = (label.get("rules") or "R?").replace(";", ", ") if label.get("needs_changes") == "yes" else "fine"
            if path in sent_back:
                where, why, said = "claude", f"your checks blocked it ({', '.join(sent_back[path])})", "not reviewed"
            else:
                review = reviews[path]
                where, why = route(pr, review)
                if where not in ROUTES:
                    raise SystemExit(f"route() sent {pr.name} to {where!r}. It must return \"merge\", \"claude\" or \"human\".")
                said = (review.verdict or "FAILED") + (", asks a person" if review.ask_human else "") + specialist_said(review)
                if where == "human":
                    findings = "".join(f"- {f.get('rule', '')}: {f.get('why', '')}\n" for f in review.findings)
                    asked = f"The reviewer asked for a person: {review.ask_human}\n" if review.ask_human else ""
                    queue.write(f"## {pr.name}: {pr.title}\nWhy: {why}\nReviewer said: {review.verdict or 'nothing, it failed'}\n{asked}{findings}\n")
            where_went[pr.name] = where
            print(f"{pr.name:<7} lead: {lead:<7} {said:<36} -> {where}: {textwrap.shorten(why, 100)}")
    counts = Counter(where_went.values())
    problems = [name for name, label in labels.items() if label.get("needs_changes") == "yes" and name in where_went]
    merged_problems = [name for name in problems if where_went[name] == "merge"]
    unseen = [name for name in wanted if where_went.get(name) == "merge"]
    print(f"\nBack to Claude: {counts['claude']}   Merged: {counts['merge']}   To a person: {counts['human']}\n")
    print(f"Problem PRs that merged:                     {len(merged_problems)} of {len(problems)}{'  (' + ', '.join(merged_problems) + ')' if merged_problems else ''}")
    print(f"Needed a human, but merged without one:      {len(unseen)} of {len(wanted)}{'  (' + ', '.join(unseen) + ')' if unseen else ''}")
    print(f"PRs a person had to read:                    {counts['human']} of {len(paths)}")
    back = [name for name, where in where_went.items() if where == "claude"]
    if back:
        print(f"\nNext: ./lab loop {'pr-03' if 'pr-03' in back else back[0]}")
    if NOTES.exists():
        with NOTES.open("a") as out:
            out.write(f"- {time.strftime('%H:%M')} pipeline | back to Claude: {counts['claude']}; merged: {counts['merge']}; to a person: {counts['human']}; "
                      f"problems merged: {len(merged_problems)} of {len(problems)}; needed a human but merged: {len(unseen)} of {len(wanted)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
