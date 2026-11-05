"""Your human gate: decides where each reviewed PR goes. Build it with Claude, from my-work/6-human-gate.md.

The agent can ask for a person with its alert_human tool, but a request is only a request: this code decides.
Think about what the agent can't be trusted to do for itself. ./lab test-gate tries it on tricky cases.
"""
from __future__ import annotations

from pr_data import Pr, Review


def route(pr: Pr, review: Review) -> tuple[str, str]:
    """Return where the PR goes, "merge", "author" or "human", and why. See scripts/pr_data.py for what Pr and Review hold."""
    # TODO: this is the naive version. Replace it with the gate you designed.
    if review.verdict == "request_changes":
        return "author", "the agent asked for changes"
    return "merge", "the agent approved"
