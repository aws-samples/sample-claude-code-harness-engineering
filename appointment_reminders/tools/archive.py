"""Archive old appointments."""
from __future__ import annotations


def archive_all(items: list, store) -> None:
    """Move items to the archive store.

    Failure modes:
        Whatever store.put raises. Earlier items stay archived.
    """
    for start in range(0, len(items), 50):
        store.put(items[start:start + 50])
