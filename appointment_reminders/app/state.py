"""What the app shows: branches, customers and appointments, with stand-ins for the outside services.

Everything lives in memory and starts again from the same sample data when the app restarts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from appointment_reminders.fakes import AsyncFakeProvider, FakeBookingsApi, FakeProvider, FakeQueue, FakeStore, Trouble
from appointment_reminders.service.models import Appointment
from appointment_reminders.tools.quota import quota_key

BRANCHES = ["US-1", "US-2", "CA-1"]


@dataclass
class Customer:
    ref: str
    name: str
    email: str
    channel: str = "email"


@dataclass
class Booking(Appointment):
    """An appointment as the app shows it, with what the bookings API knows about it."""
    status: str = "confirmed"
    distance_risk: float = 0.1
    history_risk: float = 0.2


@dataclass
class World:
    appointments: list
    customers: dict
    trouble: Trouble = field(default_factory=Trouble)

    def __post_init__(self) -> None:
        self.provider = FakeProvider(self.trouble)
        self.worker_provider = AsyncFakeProvider(self.provider, self.trouble)
        self.bookings = FakeBookingsApi(self, self.trouble)
        self.store = FakeStore({quota_key(branch): 500 for branch in BRANCHES})
        self.queue = FakeQueue()

    def appointment(self, appointment_id: str) -> Booking:
        return next(a for a in self.appointments if a.id == appointment_id)


def sample_world() -> World:
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    customers = {c.ref: c for c in [
        Customer("c-101", "Ana Ruiz", "ana.ruiz@example.com"),
        Customer("c-102", "Ben Okafor", "ben.okafor@example.com", "sms"),
        Customer("c-103", "Chloe Martin", "chloe.martin@example.com"),
        Customer("c-104", "Dev Patel", "dev.patel@example.com"),
        Customer("c-105", "Emma Lindqvist", "emma.lindqvist@example.com"),
        Customer("c-106", "Felix Tremblay", "felix.tremblay@example.com"),
    ]}
    appointments = [
        Booking("a-1", "c-101", "US-1", now + timedelta(minutes=25), ["first-visit"], distance_risk=0.1, history_risk=0.2),
        Booking("a-2", "c-102", "US-1", now + timedelta(minutes=50), ["follow-up", "parking"], distance_risk=0.3, history_risk=0.1),
        Booking("a-3", "c-103", "US-2", now + timedelta(minutes=40), ["follow-up"], distance_risk=0.05, history_risk=0.15),
        Booking("a-4", "c-104", "US-2", now + timedelta(hours=3), [], distance_risk=0.2, history_risk=0.4),
        Booking("a-5", "c-105", "CA-1", now + timedelta(minutes=35), ["translator"], distance_risk=0.15, history_risk=0.05),
        Booking("a-6", "c-106", "CA-1", now + timedelta(days=1), ["first-visit"], distance_risk=0.25, history_risk=0.25),
        Booking("a-7", "c-101", "US-1", now - timedelta(days=2), ["follow-up"], status="attended"),
        Booking("a-8", "c-103", "US-2", now - timedelta(days=5), [], status="attended"),
    ]
    return World(appointments, customers)
