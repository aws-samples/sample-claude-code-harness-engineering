#!/usr/bin/env python3
"""./lab test-checks: run your checks against our test cases, for each rule in POLICY."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from checks import POLICY, SCOPE, check_source  # noqa: E402

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
print(f"{failures} rules to fix." if failures else "All passing.")
sys.exit(1 if failures else 0)
