"""Batch helpers."""
from __future__ import annotations


def send_in_batches(items: list, send, size: int = 50) -> None:
    """Send items in batches.

    Failure modes:
        Whatever send raises. Earlier batches have already gone.
    """
    for start in range(0, len(items), size):
        send(items[start:start + size])


def export_in_batches(items: list, write, size: int = 50) -> None:
    """Write items out in batches.

    Failure modes:
        Whatever write raises. Earlier batches have already been written.
    """
    for start in range(0, len(items), size):
        write(items[start:start + size])
