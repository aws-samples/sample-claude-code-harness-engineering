#!/usr/bin/env python3
"""The whole system: your checks, then the reviewer with its alert_human tool, then your gate routes each PR.

  ./lab pipeline [dev]

A PR your checks block goes back to Claude without a review. Anything routed to a person lands in human-review-queue.md.
Nobody is really alerted.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr_data  # noqa: E402
from gate import route  # noqa: E402
import run_reviewer as runner  # noqa: E402
from run_checks import check_pr  # noqa: E402

QUEUE = Path("human-review-queue.md")


def review_one(path: Path, system: str, tools: str, code: str, logs: str, specialist: tuple[str, str] | None) -> pr_data.Review:
    alert_log = Path(logs) / f"{path.stem}.jsonl"
    answer = runner.review(path.read_text(), system, tools, code, str(alert_log))
    alerts = [json.loads(line) for line in alert_log.read_text().splitlines()] if alert_log.exists() else []
    checked = runner.gate_check(path.read_text(), *specialist, code) if specialist else None
    return pr_data.Review(answer["verdict"], answer["findings"], alerts, answer.get("error", ""), checked)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=["dev", "holdout"], default="dev")
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    reason = runner.blocked(args.set, runner.chunk_now()) if args.set != "holdout" else None
    if reason:
        raise SystemExit(reason)
    runner.check_agent(runner.AGENT)
    system, tools, code = runner.system_prompt(runner.AGENT), runner.agent_tools(runner.AGENT), runner.code_copy()
    paths = runner.pr_paths(args.set, args.only)
    if not paths:
        raise SystemExit("No PRs here. If this set isn't open yet: ./lab goto gate")
    sent_back = {}
    for path in paths:
        blocks = [finding.rule for _, level, finding in check_pr(path.read_text()) if level == "block"]
        if blocks:
            sent_back[path] = blocks
            print(f"{path.stem}  your checks blocked it ({', '.join(sorted(set(blocks)))})  ->  back to Claude, with no review")
    paths = [path for path in paths if path not in sent_back]
    gate_agent = runner.GATE_AGENT
    specialist = (runner.system_prompt(gate_agent), runner.agent_tools(gate_agent)) if runner.written(gate_agent) else None
    also = ", with your specialist gate agent" if specialist else ""
    print(f"Reviewing {len(paths)} PRs{also}, then routing them. This can take a minute.", flush=True)
    if not paths:
        shutil.rmtree(code, ignore_errors=True)
        print(f"Your checks sent back all {len(sent_back)}, so there's nothing to review.")
        return 0
    try:
        with tempfile.TemporaryDirectory() as logs, ThreadPoolExecutor(max_workers=5) as pool:
            reviews = list(pool.map(lambda p: review_one(p, system, tools, code, logs, specialist), paths))
    finally:
        shutil.rmtree(code, ignore_errors=True)
    if all(review.verdict is None for review in reviews):
        print(f"Every call failed, so {QUEUE} is unchanged. The first error: {reviews[0].error if reviews else ''}")
        return 1
    counts: Counter[str] = Counter({"back to Claude": len(sent_back)} if sent_back else {})
    with QUEUE.open("w") as queue:
        for path, review in zip(paths, reviews):
            pr = pr_data.load_pr(path)
            where, why = route(pr, review)
            counts[where] += 1
            asked = "asked for a person" if review.alerts else "no alert"
            if review.specialist:
                said = review.specialist["needs_human"]
                asked += f", specialist: {'FAILED' if said is None else 'a person should look' if said else 'no person needed'}"
            print(f"{pr.name}  agent: {review.verdict or 'FAILED: ' + review.error}, {asked}  ->  {where}: {why}")
            if where == "human":
                summary = review.alerts[0].get("summary", "") if review.alerts else ""
                findings = "".join(f"- {f.get('rule', '')}: {f.get('why', '')}\n" for f in review.findings)
                specialist_said = f"Specialist said: {review.specialist.get('reason') or review.specialist.get('error', '')}\n" if review.specialist else ""
                queue.write(f"## {pr.name}: {pr.title}\nWhy: {why}\nAgent said: {review.verdict or 'nothing, it failed'}\n{summary}\n{specialist_said}{findings}\n")
    print(f"\n{dict(counts)}. People would see {counts['human']} of {len(paths) + len(sent_back)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
