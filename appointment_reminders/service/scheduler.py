"""Pick the reminders that are due, and send them."""
from __future__ import annotations

from datetime import datetime, timedelta

from appointment_reminders.service.models import Appointment, Reminder, SendResult
from appointment_reminders.service.risk import reminder_text
from appointment_reminders.service.settings import REMINDER_WINDOW_SECONDS, SWEEP_LIMIT


def due_appointments(appointments: list[Appointment], now: datetime) -> list[Appointment]:
    """Appointments starting within the reminder window, soonest first."""
    window_end = now + timedelta(seconds=REMINDER_WINDOW_SECONDS)
    due = [a for a in appointments if now <= a.starts_at <= window_end]
    return sorted(due, key=lambda a: a.starts_at)[:SWEEP_LIMIT]


def reminder_for(appointment: Appointment, customer_email: str) -> Reminder:
    """The reminder to send for one appointment."""
    return Reminder(appointment.id, customer_email, reminder_text(appointment.branch))


def send_all(reminders: list[Reminder], gateway) -> list[SendResult]:
    """Send each reminder once and report what happened to it."""
    results = []
    for reminder in reminders:
        try:
            gateway.send(reminder)
            results.append(SendResult(delivered=True))
        except ConnectionError:
            results.append(SendResult(delivered=False, code="GATEWAY_DOWN"))
    return results


def tags_changed(old: list[str], new: list[str]) -> bool:
    """Whether an appointment's tags differ."""
    return old != new
