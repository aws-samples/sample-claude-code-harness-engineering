#!/usr/bin/env python3
"""./lab test-checks: run your checks against our test cases, for each rule in POLICY."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from checks import POLICY, SCOPE, check_source  # noqa: E402
from run_checks import check_pr  # noqa: E402

if not POLICY:
    sys.exit("POLICY in scripts/checks.py is empty. Ask Claude to build your plan from my-work/2-checks-plan.md, or take ours with ./lab catch-up checks.")
fixtures = json.loads((ROOT / "data/check-fixtures.json").read_text())
failures = 0
for rule, level in POLICY.items():
    if str(level).strip().lower() not in ("block", "warn"):
        print(f"FAIL {rule}  POLICY says {level!r}. Use \"block\" or \"warn\".")
        failures += 1
if str(SCOPE).strip().lower() not in ("new", "all"):
    print(f"FAIL SCOPE is {SCOPE!r}. Use \"new\" or \"all\".")
    failures += 1
for rule in POLICY:
    cases = [c for c in fixtures if c["rule"] == rule]
    if not cases:
        print(f"     {rule}  we have no test cases for this one. Ask Claude to add one that fires and one near miss to data/check-fixtures.json")
        continue
    bad = [c for c in cases if any(f.rule == rule for f in check_source(c["path"], c["source"])) != c["fires"]]
    fires = [c for c in cases if c["fires"]]
    near = [c for c in cases if not c["fires"]]
    print(f"{'ok  ' if not bad else 'FAIL'} {rule}  must fire {sum(c not in bad for c in fires)}/{len(fires)}, near misses {sum(c not in bad for c in near)}/{len(near)}")
    for case in bad:
        print(f"       {'missed' if case['fires'] else 'false alarm'}: {case['path']}: {case['source'].strip()!r}")
    failures += bool(bad)

print("\nYour checks on the check PRs in data/review-prs/checks/, as your hook would check their commits.")
print('"for your reviewer" means you have no check for that rule.')
for row in csv.DictReader((ROOT / "data/review-prs/checks/expected.csv").open()):
    found = check_pr((ROOT / f"data/review-prs/checks/{row['pr']}.diff").read_text())
    fired = {finding.rule: level for _, level, finding in found}
    rule = row["rules"]
    if not rule:
        result = "passed" if not fired else f"FALSE ALARM: {', '.join(sorted(fired))}"
        failures += bool(fired)
    elif rule in fired:
        result = f"{'blocked' if fired[rule] == 'block' else 'warned'}"
    elif rule in POLICY:
        result = "MISSED"
        failures += 1
    else:
        result = "for your reviewer"
    extra = sorted(set(fired) - {rule}) if rule else []
    print(f"  {row['pr']}  {rule or '-':<4} {result + ('  also ' + ', '.join(extra) if extra else ''):<18} {row['reason']}")
print(f"\n{failures} to fix." if failures else "\nAll passing.")
sys.exit(1 if failures else 0)
