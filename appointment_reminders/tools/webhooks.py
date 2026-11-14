"""Outgoing webhooks to branch systems."""
from __future__ import annotations

import httpx

from appointment_reminders.service.settings import REQUEST_TIMEOUT_SECONDS


def deliver(url: str, event: dict) -> None:
    """Post one event to a branch's webhook.

    Failure modes:
        Raises httpx.HTTPError if the branch rejects the event or can't be reached.
    """
    httpx.post(url, json=event, timeout=REQUEST_TIMEOUT_SECONDS).raise_for_status()
