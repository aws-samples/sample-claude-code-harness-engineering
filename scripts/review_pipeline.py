#!/usr/bin/env python3
"""The whole system: run the reviewer with its alert_human tool, then let your gate route each PR.

  ./lab pipeline [dev]

Anything routed to a person lands in human-review-queue.md. Nobody is really alerted.
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

QUEUE = Path("human-review-queue.md")


def review_one(path: Path, system: str, tools: str, code: str, logs: str) -> pr_data.Review:
    alert_log = Path(logs) / f"{path.stem}.jsonl"
    answer = runner.review(path.read_text(), system, tools, code, str(alert_log))
    alerts = [json.loads(line) for line in alert_log.read_text().splitlines()] if alert_log.exists() else []
    return pr_data.Review(answer["verdict"], answer["findings"], alerts, answer.get("error", ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=["dev", "holdout"], default="holdout")
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
    print(f"Reviewing {len(paths)} PRs, then routing them. This can take a minute.", flush=True)
    try:
        with tempfile.TemporaryDirectory() as logs, ThreadPoolExecutor(max_workers=5) as pool:
            reviews = list(pool.map(lambda p: review_one(p, system, tools, code, logs), paths))
    finally:
        shutil.rmtree(code, ignore_errors=True)
    if all(review.verdict is None for review in reviews):
        print(f"Every call failed, so {QUEUE} is unchanged. The first error: {reviews[0].error if reviews else ''}")
        return 1
    counts: Counter[str] = Counter()
    with QUEUE.open("w") as queue:
        for path, review in zip(paths, reviews):
            pr = pr_data.load_pr(path)
            where, why = route(pr, review)
            counts[where] += 1
            asked = "asked for a person" if review.alerts else "no alert"
            print(f"{pr.name}  agent: {review.verdict or 'FAILED: ' + review.error}, {asked}  ->  {where}: {why}")
            if where == "human":
                summary = review.alerts[0].get("summary", "") if review.alerts else ""
                findings = "".join(f"- {f.get('rule', '')}: {f.get('why', '')}\n" for f in review.findings)
                queue.write(f"## {pr.name}: {pr.title}\nWhy: {why}\nAgent said: {review.verdict or 'nothing, it failed'}\n{summary}\n{findings}\n")
    print(f"\n{dict(counts)}. People would see {counts['human']} of {len(paths)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
