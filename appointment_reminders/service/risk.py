"""Late-cancellation risk."""
from __future__ import annotations


def late_cancel_score(distance_risk: float, history_risk: float) -> float:
    return round(distance_risk + history_risk, 6)


REGIONS = {"US": "United States", "CA": "Canada", "MX": "Mexico"}


def get_region(code: str) -> str:
    return REGIONS[code]


def reminder_text(branch: str) -> str:
    """The reminder for a branch such as US-1."""
    return f"You have an appointment at your {branch} branch in {get_region(branch.split('-')[0])}."
