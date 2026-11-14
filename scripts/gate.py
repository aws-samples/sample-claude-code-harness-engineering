"""Your human gate: decides where each reviewed PR goes. Build it with /design-gate."""
from __future__ import annotations

from pr_data import Pr, Review


def route(pr: Pr, review: Review) -> tuple[str, str]:
    """Return where the PR goes, "merge", "claude" or "human", and why. See scripts/pr_data.py for what Pr and Review hold."""
    # TODO: this is the naive version. Replace it with the gate you designed.
    if review.verdict == "request_changes":
        return "claude", "the reviewer asked for changes"
    return "merge", "the reviewer approved"
