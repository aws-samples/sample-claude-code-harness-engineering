"""Your checks. Build this with Claude, from my-work/2-checks-plan.md. scripts/run_checks.py runs it."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Finding:
    rule: str
    line: int
    message: str  # tell whoever hit it how to fix it


# TODO: from your plan. "block" stops the commit, "warn" lets it through and prints the finding.
POLICY: dict[str, str] = {}

# TODO: from your plan. "new" ignores problems that were already there at the last commit. "all" doesn't.
SCOPE = "new"


def check_source(path: str, source: str) -> list[Finding]:
    """Findings for one file, given its path from the repo root, such as appointment_reminders/app/api/health.py."""
    # TODO: one check for each rule in POLICY.
    return []
