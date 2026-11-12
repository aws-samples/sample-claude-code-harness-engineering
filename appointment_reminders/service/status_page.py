"""Text for the branch status page."""
from __future__ import annotations

from appointment_reminders.service.risk import reminder_text


def status_line(branch: str) -> str:
    """The line shown on the branch status page."""
    return reminder_text(branch)
