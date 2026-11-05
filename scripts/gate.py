"""Your human gate: decides where each reviewed PR goes. Reference solution, from ./lab catch-up gate."""
from __future__ import annotations

import re

from pr_data import Pr, Review

SENSITIVE = re.compile(r"^\+.*(logger\.|pytest\.mark\.|MAX_ATTEMPTS|queue\.put)", re.MULTILINE)
ADDRESSES_REVIEWER = re.compile(r"(?i)\b((AI|automated) review|reviewers?:|approve (it|this)|ignore (all|your|previous|prior)|no action needed)")
LARGE_PR_LINES = 50
CUSTOMER_DATA = ("service/records.py", "service/models.py")


def forced_reason(pr: Pr, review: Review) -> str | None:
    """Conditions code can check, so the agent can't be talked out of them."""
    if review.verdict is None:
        return "the agent failed, so nobody has reviewed this"
    if ADDRESSES_REVIEWER.search(pr.description) or ADDRESSES_REVIEWER.search(pr.diff):
        return "the PR's text addresses its reviewers"
    if pr.lines_added > LARGE_PR_LINES:
        return "too large for an unattended merge"
    if any(path.endswith(CUSTOMER_DATA) for path in pr.paths):
        return "it touches code that handles customer records"
    if SENSITIVE.search(pr.diff):
        return "it touches logging, retries, queueing or test markers"
    return None


def route(pr: Pr, review: Review) -> tuple[str, str]:
    """Return where the PR goes, "merge", "author" or "human", and why. The agent can add to what reaches a person, but never remove."""
    if review.alerts:
        return "human", review.alerts[0].get("reason") or "the agent asked for a person"
    forced = forced_reason(pr, review)
    if forced:
        return "human", forced
    if review.verdict == "approve" and review.findings:
        return "human", "the agent approved, but it listed findings"
    if review.verdict == "request_changes":
        return "author", "the agent asked for changes"
    return "merge", "approved, and nothing needs a person"
