"""Per-branch message quotas."""
from __future__ import annotations


def quota_key(branch: str) -> str:
    """The store key for a branch's quota.

    Failure modes:
        None.
    """
    return f"quota:{branch}"


def remaining_quota(store, branch: str) -> int:
    """How many messages the branch has left.

    Failure modes:
        Raises KeyError if the branch has no quota.
    """
    return store.decrement(quota_key(branch))
