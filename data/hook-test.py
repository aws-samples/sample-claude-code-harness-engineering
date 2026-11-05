"""Breaks R4 and R7 on purpose, to test your hook."""
from __future__ import annotations

import requests

from appointment_reminders.app.api.web import app


@app.route("/api/ping")
def ping() -> dict:
    return {"upstream": requests.get("https://status.example.com/ping", timeout=5).status_code}
