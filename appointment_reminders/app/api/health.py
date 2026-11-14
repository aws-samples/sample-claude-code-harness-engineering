"""Health check. It has no rate limit, which breaks R7. It's been like this for a while."""
from __future__ import annotations

from appointment_reminders.app.api.web import app


@app.route("/api/health")
def health() -> dict:
    return {"status": "ok"}
