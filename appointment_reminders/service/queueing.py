"""Background queue."""
from __future__ import annotations

import logging

from appointment_reminders.service.models import Reminder, ReminderBatch

logger = logging.getLogger(__name__)


async def queue_reminder(queue, reminder: Reminder) -> None:
    await queue.put(reminder)


async def queue_batch(queue, batch: ReminderBatch) -> None:
    await queue.put(batch)
