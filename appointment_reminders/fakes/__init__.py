"""Stand-ins for the outside services, so the app runs on one machine with no network.

The messaging provider and the bookings API behave like real ones: they keep what you send them, and with a
trouble switch on they fail the way real services do, after the work may already have happened.
"""
from __future__ import annotations

from datetime import datetime, timezone

import httpx

from appointment_reminders.service.worker import WorkerRecycled


class FakeResponse:
    def __init__(self, body=None, status: int = 200) -> None:
        self.body = body if body is not None else {}
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(f"status {self.status_code}", request=None, response=None)

    def json(self):
        return self.body


class Trouble:
    """Trouble to simulate, from ./lab demo --trouble. When it's on, every other call to that service fails, and the worker is recycled once."""

    NAMES = {
        "slow_bookings": "the bookings API is timing out",
        "provider_blips": "the messaging provider is dropping connections",
        "worker_recycled": "the background worker restarts mid-batch",
    }

    FLAGS = {"bookings": "slow_bookings", "provider": "provider_blips", "worker": "worker_recycled"}

    def __init__(self) -> None:
        self.on: set = set()
        self.calls: dict = {}

    def recycles_now(self) -> bool:
        """The worker is recycled once, on its second send after the switch goes on."""
        if "worker_recycled" not in self.on:
            return False
        self.calls["worker_recycled"] = self.calls.get("worker_recycled", 0) + 1
        return self.calls["worker_recycled"] == 2

    def strikes(self, name: str) -> bool:
        """Whether this call fails: every other call while the switch is on."""
        if name not in self.on:
            return False
        self.calls[name] = self.calls.get(name, 0) + 1
        return self.calls[name] % 2 == 1


class FakeProvider:
    """The messaging provider. outbox is what customers really received."""

    def __init__(self, trouble: Trouble) -> None:
        self.trouble = trouble
        self.outbox: list = []
        self.keys: set = set()

    def _deliver(self, to: str, body: str, via: str) -> None:
        self.outbox.append({"to": to, "body": body, "via": via, "at": datetime.now(timezone.utc)})

    def post(self, path: str, json: dict, timeout=None) -> FakeResponse:
        if path != "/messages":
            return FakeResponse(status=404)
        self._deliver(json["to"], json["body"], "send")
        if self.trouble.strikes("provider_blips"):
            raise ConnectionError("connection dropped before the provider answered")  # it went out anyway
        return FakeResponse({"ok": True})

    def put(self, path: str, json: dict, timeout=None) -> FakeResponse:
        key = path.rsplit("/", 1)[-1]
        if key not in self.keys:  # the same key twice is one message
            self.keys.add(key)
            self._deliver(json["to"], json["body"], "send once")
        return FakeResponse({"ok": True})

    def get(self, path: str, timeout=None) -> FakeResponse:
        return FakeResponse(list(self.outbox))


class AsyncFakeProvider:
    """The same provider, for the background worker."""

    def __init__(self, provider: FakeProvider, trouble: Trouble) -> None:
        self.provider = provider
        self.trouble = trouble

    async def post(self, path: str, json: dict, timeout=None):
        if self.trouble.recycles_now():
            raise WorkerRecycled("the platform is restarting this worker")
        return self.provider.post(path, json)

    async def put(self, path: str, json: dict, timeout=None):
        return self.provider.put(path, json)

    async def get(self, path: str, timeout=None):
        return self.provider.get(path).json()


class FakeBookingsApi:
    """The bookings API. It owns appointments and emails customers itself when a time changes."""

    def __init__(self, world, trouble: Trouble) -> None:
        self.world = world
        self.trouble = trouble

    def _slow(self) -> None:
        if self.trouble.strikes("slow_bookings"):
            raise httpx.TimeoutException("the bookings API took too long to answer")

    def post(self, path: str, json: dict, timeout=None) -> FakeResponse:
        if path == "/messages":  # the bookings API tells the customer about a new time
            appointment = self.world.appointment(json["appointment"])
            customer = self.world.customers[appointment.customer_ref]
            self.world.provider._deliver(customer.email, f"Your appointment has moved to {datetime.fromisoformat(json['starts_at']):%A at %H:%M}.", "bookings API")
            return FakeResponse({"ok": True})
        return FakeResponse(status=404)

    def put(self, path: str, json: dict, timeout=None) -> FakeResponse:
        self._slow()
        parts = path.strip("/").split("/")
        if parts[0] == "appointments" and parts[2] == "time":
            self.world.appointment(parts[1]).starts_at = datetime.fromisoformat(json["starts_at"])
        elif parts[0] == "appointments" and parts[2] == "tags":
            self.world.appointment(parts[1]).tags = list(json["tags"])
        elif parts[0] == "customers" and parts[2] == "channel":
            self.world.customers[parts[1]].channel = json["channel"]
        return FakeResponse({"ok": True})

    def get(self, path: str, params=None, timeout=None) -> FakeResponse:
        self._slow()
        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[2] == "status":
            return FakeResponse({"status": self.world.appointment(parts[1]).status})
        if path == "/appointments":  # pages of two, as the real API pages them
            ids = [a.id for a in self.world.appointments]
            start = int((params or {}).get("cursor") or 0)
            following = start + 2 if start + 2 < len(ids) else None
            return FakeResponse({"items": ids[start:start + 2], "next": None if following is None else str(following)})
        return FakeResponse(status=404)


class FakeStore:
    """A key-value store: quotas, the archive and saved profiles."""

    def __init__(self, counters: dict) -> None:
        self.counters = dict(counters)
        self.archive: list = []
        self.saved: list = []

    def get(self, key: str) -> int:
        return self.counters[key]

    def decrement(self, key: str) -> int:
        self.counters[key] -= 1
        return self.counters[key]

    def put(self, items: list) -> None:
        self.archive.extend(items)

    def save(self, record) -> None:
        self.saved.append(record)


class FakeDb:
    """Branch settings and the customer table."""

    def __init__(self, settings: dict) -> None:
        self.settings = {branch: dict(values) for branch, values in settings.items()}
        self.rows: dict = {}

    def fetch_settings(self, branch: str) -> dict:
        return dict(self.settings[branch])

    def save_settings(self, branch: str, settings: dict) -> None:
        self.settings[branch] = dict(settings)

    def upsert(self, table: str, row: dict) -> dict:
        self.rows.setdefault(table, {})[row["ref"]] = row
        return row


class FakeQueue:
    """The background queue."""

    def __init__(self) -> None:
        self.items: list = []

    async def put(self, item) -> None:
        self.items.append(item)

    def take(self):
        return self.items.pop(0) if self.items else None


class FakeSendLog:
    """What the workers say they sent, beside what the provider says went out."""

    def __init__(self) -> None:
        self.entries: list = []

    async def record_sent(self, batch_id: str, size: int) -> None:
        self.entries.append(f"batch {batch_id}: {size} sent")

    async def record_totals(self, sent: list) -> None:
        self.entries.append(f"provider total today: {len(sent)}")
