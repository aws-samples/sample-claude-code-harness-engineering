from __future__ import annotations

from datetime import datetime, timedelta, timezone

from appointment_reminders.service.models import Appointment
from appointment_reminders.service.scheduler import due_appointments, tags_changed

NOW = datetime(2030, 3, 4, 9, tzinfo=timezone.utc)


def appointment(id_: str, minutes: int) -> Appointment:
    return Appointment(id_, "c1", "US-1", NOW + timedelta(minutes=minutes))


def test_only_appointments_in_the_window_are_due():
    due = due_appointments([appointment("later", 90), appointment("soon", 30), appointment("past", -5)], NOW)
    assert [a.id for a in due] == ["soon"]


def test_tags_changed():
    assert tags_changed(["a"], ["b"])
    assert not tags_changed(["a"], ["a"])
