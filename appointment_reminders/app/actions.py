"""What each button on the pages does. Every action calls the service's own code, so a change there shows here."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from appointment_reminders.service.queueing import queue_reminder
from appointment_reminders.service.risk import late_cancel_score
from appointment_reminders.service.scheduler import due_appointments, reminder_for, send_all, tags_changed
from appointment_reminders.service.worker import WorkerRecycled
from appointment_reminders.tools.bookings_client import set_tags
from appointment_reminders.tools.messaging import DirectGateway, Gateway
from appointment_reminders.tools.rebooking import change_channel, move_appointment


def now() -> datetime:
    return datetime.now(timezone.utc)


def due_reminders(world) -> list:
    return [reminder_for(a, world.customers[a.customer_ref].email) for a in due_appointments(world.appointments, now())]


def send_due(world) -> str:
    reminders = due_reminders(world)
    results = send_all(reminders, DirectGateway(world.provider))
    failed = sum(1 for r in results if not r.delivered)
    return f"Sent {len(results) - failed} of {len(results)} due reminders." + (f" {failed} reported a failure." if failed else "")


def _run_worker(world) -> None:
    """Send what's on the background queue, as the worker would."""
    async def drain() -> None:
        gateway = Gateway(world.worker_provider)
        while (reminder := world.queue.take()) is not None:
            try:
                await gateway.send_message(reminder)
            except WorkerRecycled:
                pass
    asyncio.run(drain())


def remind_one(world, appointment_id: str) -> str:
    appointment = world.appointment(appointment_id)
    reminder = reminder_for(appointment, world.customers[appointment.customer_ref].email)
    asyncio.run(queue_reminder(world.queue, reminder))
    _run_worker(world)
    return f"Sent {world.customers[appointment.customer_ref].name} a reminder."


def move(world, appointment_id: str, starts_at: str) -> str:
    try:
        move_appointment(world.bookings, appointment_id, datetime.fromisoformat(starts_at).replace(tzinfo=timezone.utc).isoformat())
    except Exception as exc:  # the page shows what went wrong
        return f"Couldn't move {appointment_id}: {exc}"
    appointment = world.appointment(appointment_id)
    return f"Moved {world.customers[appointment.customer_ref].name}'s appointment to {appointment.starts_at:%A at %H:%M}."


def channel(world, customer_ref: str, new_channel: str) -> str:
    try:
        change_channel(world.bookings, customer_ref, new_channel)
    except Exception as exc:
        return f"Couldn't change the channel: {exc}"
    return f"{world.customers[customer_ref].name} now hears from us by {new_channel}."


def tags(world, appointment_id: str, text: str) -> str:
    appointment = world.appointment(appointment_id)
    new = [tag.strip() for tag in text.split(",") if tag.strip()]
    if not tags_changed(appointment.tags, new):
        return "No change to the tags."
    try:
        set_tags(world.bookings, appointment_id, new)
    except Exception as exc:
        return f"Couldn't save the tags: {exc}"
    return f"Saved tags for {appointment_id}."








def risk_of(appointment) -> float:
    return late_cancel_score(appointment.distance_risk, appointment.history_risk)
