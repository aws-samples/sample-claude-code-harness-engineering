"""Runs queued reminder batches."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def nightly_totals(gateway, send_log) -> None:
    """Record what the provider says went out today, whatever the workers thought they sent."""
    await send_log.record_totals(await gateway.sent_today())


class WorkerRecycled(Exception):
    """The platform is restarting this worker."""


async def run_batch(batch, gateway, send_log, queue) -> None:
    try:
        for reminder in batch.reminders:
            await gateway.send_message(reminder)
        await send_log.record_sent(batch.id, batch.size)
    except WorkerRecycled:
        logger.info("worker recycled during batch %s", batch.id)
