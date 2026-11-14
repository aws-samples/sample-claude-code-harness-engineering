from __future__ import annotations

from appointment_reminders.service.risk import late_cancel_score


def test_late_cancel_score():
    score = late_cancel_score(0.1, 0.2)
    assert score == 0.3
