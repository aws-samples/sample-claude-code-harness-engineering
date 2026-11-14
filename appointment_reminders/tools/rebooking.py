"""Rebooking flows."""
from __future__ import annotations

import httpx

from appointment_reminders.tools.bookings_client import set_appointment_time, set_contact_preference


def move_appointment(client: httpx.Client, appointment_id: str, starts_at: str) -> None:
    """Move an appointment.

    Failure modes:
        Raises httpx.HTTPError as set_appointment_time does.
    """
    set_appointment_time(client, appointment_id, starts_at)


def change_channel(client: httpx.Client, customer_ref: str, channel: str) -> None:
    """Change how a customer is contacted.

    Failure modes:
        Raises httpx.HTTPError as set_contact_preference does.
    """
    set_contact_preference(client, customer_ref, channel)
