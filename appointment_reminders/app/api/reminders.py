"""Routes for sending reminders."""
from __future__ import annotations

from datetime import datetime, timezone

from appointment_reminders.app.api.web import app, rate_limit
from appointment_reminders.service.scheduler import due_appointments


@app.route("/api/reminders/due")
@rate_limit()
def list_due(appointments: list) -> dict:
    due = due_appointments(appointments, datetime.now(timezone.utc))
    return {"due": [a.id for a in due]}
