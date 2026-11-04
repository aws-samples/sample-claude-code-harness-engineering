"""Bookings API client."""
from __future__ import annotations

import httpx

from appointment_reminders.service.settings import REQUEST_TIMEOUT_SECONDS


def set_contact_preference(client: httpx.Client, customer_ref: str, channel: str) -> None:
    """Replace the customer's preferred contact channel.

    Failure modes:
        Raises httpx.HTTPError if the bookings API rejects the call or can't be reached.
    """
    client.put(f"/customers/{customer_ref}/channel", json={"channel": channel}, timeout=REQUEST_TIMEOUT_SECONDS).raise_for_status()


def set_appointment_time(client: httpx.Client, appointment_id: str, starts_at: str) -> None:
    """Email the customer the new time and move the appointment.

    Failure modes:
        Raises httpx.HTTPError if either call fails. The email may already have gone out.
    """
    client.post("/messages", json={"appointment": appointment_id, "starts_at": starts_at}, timeout=REQUEST_TIMEOUT_SECONDS).raise_for_status()
    client.put(f"/appointments/{appointment_id}/time", json={"starts_at": starts_at}, timeout=REQUEST_TIMEOUT_SECONDS).raise_for_status()


def set_tags(client: httpx.Client, appointment_id: str, tags: list[str]) -> None:
    """Replace the appointment's tags.

    Failure modes:
        Raises httpx.HTTPError if the bookings API rejects the call or can't be reached.
    """
    client.put(f"/appointments/{appointment_id}/tags", json={"tags": tags}, timeout=REQUEST_TIMEOUT_SECONDS).raise_for_status()


def fetch_status(client: httpx.Client, appointment_id: str) -> str | None:
    """Fetch an appointment's status."""
    try:
        response = client.get(f"/appointments/{appointment_id}/status", timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.TimeoutException:
        return None
    return response.json()["status"]


def next_page(client: httpx.Client, cursor: str | None) -> dict:
    """Fetch one page of appointments.

    Failure modes:
        Raises httpx.HTTPError if the bookings API rejects the call or can't be reached.
    """
    response = client.get("/appointments", params={"cursor": cursor}, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def all_items(client: httpx.Client):
    """Yield every appointment, page by page.

    Failure modes:
        Raises httpx.HTTPError as next_page does.
    """
    cursor = None
    while True:
        body = next_page(client, cursor)
        yield from body["items"]
        cursor = body["next"]
        if cursor is None:
            return
