#!/usr/bin/env python3
"""./lab test-checks: run your checks against the fixtures, for the rules in your plan."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_checks  # noqa: E402
from my_work import first_word, table_rows  # noqa: E402

plan_path = ROOT / "my-work/2-checks-plan.md"
if not plan_path.exists():
    sys.exit("No plan yet: run ./lab goto checks.")
all_rows = table_rows(plan_path, r"R\d+")
rows = [(row[0], row[2], row[3], row[4]) for row in all_rows if len(row) == 5]
for row in all_rows:
    if len(row) != 5:
        print(f"FAIL {row[0]}: this row in your plan should have five cells, and has {len(row)}.")
fixtures = json.loads((ROOT / "data/check-fixtures.json").read_text())
failures = sum(len(row) != 5 for row in all_rows)
for rule, _severity, level, scope in rows:
    cases = [c for c in fixtures if c["rule"] == rule]
    bad = [c for c in cases if any(f.rule == rule for f in run_checks.check_source(c["path"], c["source"])) != c["fires"]]
    fires = [c for c in cases if c["fires"]]
    near = [c for c in cases if not c["fires"]]
    if not cases:
        print(f"{rule}  no fixtures here: ask Claude to write one that fires and one near miss, as tests in tests/")
    else:
        print(f"{'ok  ' if not bad else 'FAIL'} {rule}  must fire {sum(c not in bad for c in fires)}/{len(fires)}, near misses {sum(c not in bad for c in near)}/{len(near)}")
    for case in bad:
        print(f"       {'missed' if case['fires'] else 'false alarm'}: {case['path']}: {case['source'].strip()!r}")
    want = (first_word(level), "new" if "new" in scope.lower().split() else "all")
    if want[0] == "todo" or first_word(scope) == "todo":
        print("       your plan's decisions for this rule are still TODO")
        bad = bad or ["plan"]
    elif run_checks.POLICY.get(rule) != want:
        print(f"       POLICY says {run_checks.POLICY.get(rule)}, your plan says {want}. Your plan decides: change POLICY in scripts/run_checks.py to match it.")
        bad = bad or ["policy"]
    failures += bool(bad)
if not rows:
    print("Your plan has no checks yet. Put some rules under check or both in my-work/1-rule-sort.md, then run ./lab goto checks.")
elif failures:
    print(f"{failures} rules to fix.")
else:
    print("All passing. Now go and see the hook fire.")
sys.exit(1 if failures or not rows else 0)
