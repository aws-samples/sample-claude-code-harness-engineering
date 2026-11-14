"""Activity log."""
from __future__ import annotations


def audit_key(branch: str) -> str:
    """The store key for a branch's activity log.

    Failure modes:
        None.
    """
    return f"audit:{branch}"
