"""The messaging provider."""
from __future__ import annotations


class DirectGateway:
    """Sends straight away, for the scheduler."""

    def __init__(self, client) -> None:
        self.client = client

    def send(self, reminder) -> None:
        """Send one reminder.

        Failure modes:
            Raises ConnectionError if the provider can't be reached.
        """
        self.client.post("/messages", json={"to": reminder.customer_email, "body": reminder.body})


class Gateway:
    """Sends from background workers."""

    def __init__(self, client) -> None:
        self.client = client

    async def send_message(self, reminder) -> None:
        """Send one reminder. Every call sends, and the provider bills for it.

        Failure modes:
            Raises ConnectionError if the provider can't be reached.
        """
        await self.client.post("/messages", json={"to": reminder.customer_email, "body": reminder.body})

    async def sent_today(self) -> list[dict]:
        """What the provider says went out today.

        Failure modes:
            Raises ConnectionError if the provider can't be reached.
        """
        return await self.client.get("/messages/today")

    async def send_once(self, reminder, key: str) -> None:
        """Send one reminder once. A repeat with the same key does nothing, and isn't billed.

        Failure modes:
            Raises ConnectionError if the provider can't be reached.
        """
        await self.client.put(f"/messages/{key}", json={"to": reminder.customer_email, "body": reminder.body})
