"""Your human gate: decides where each reviewed PR goes. Reference solution, from ./lab catch-up gate.

Code checks what it can see for certain (H1 to H3, and H5's obvious wording). The reviewer's ask_human covers H4.
The specialist in my-work/6-gate-agent.md covers H5 and H6, where meaning matters.
"""
from __future__ import annotations

import re

from pr_data import Pr, Review

ADDRESSES_REVIEWER = re.compile(r"(?i)\b((AI|automated) review|reviewers?:|pre-?approved|approve (it|this)|ignore (all|your|previous|prior)|no action needed)")
LARGE_PR_LINES = 50
CUSTOMER_DATA = ("service/records.py", "service/models.py")
MAX_FIXES = 2  # fixes Claude gets before a person steps in


def person_now(pr: Pr, review: Review) -> str | None:
    """Reasons a fix from Claude can't settle, so the PR skips straight to a person."""
    specialist = review.specialist or {}
    if review.verdict is None:
        return "H3: the review didn't finish"
    if review.specialist is not None and specialist.get("needs_human") is None:
        return "H3: the specialist's check didn't finish"
    if review.ask_human:
        return f"H4: {review.ask_human}"
    if ADDRESSES_REVIEWER.search(pr.diff):
        return "H5: the PR's text addresses its reviewer"
    if specialist.get("needs_human") and specialist.get("preference") == "H5":
        return f"H5: {specialist.get('reason', '')}"
    return None


def person_before_merge(pr: Pr, review: Review) -> str | None:
    """Reasons a person should look, once Claude has fixed what the reviewer found."""
    if any(path.endswith(CUSTOMER_DATA) for path in pr.paths):
        return "H1: it touches customer records"
    if pr.lines_added > LARGE_PR_LINES:
        return "H2: it's over 50 added lines"
    if review.specialist and review.specialist.get("needs_human"):
        return f"H6: {review.specialist.get('reason', '')}"
    return None


def route(pr: Pr, review: Review) -> tuple[str, str]:
    """Return where the PR goes, "merge", "claude" or "human", and why."""
    now = person_now(pr, review)
    if now:
        return "human", now
    if review.verdict == "request_changes":
        if pr.fixes >= MAX_FIXES:
            return "human", f"still not approved after {pr.fixes} fixes"
        return "claude", "the reviewer asked for changes"
    later = person_before_merge(pr, review)
    if later:
        return "human", later
    return "merge", "approved, and nothing needs a person"
