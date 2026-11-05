"""The service's records."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Appointment:
    id: str
    customer_ref: str
    branch: str
    starts_at: datetime
    tags: list[str] = field(default_factory=list)


@dataclass
class Reminder:
    id: str
    customer_email: str
    body: str


@dataclass
class ReminderBatch:
    id: str
    size: int
    reminders: list[Reminder] = field(default_factory=list)

    def __str__(self) -> str:
        return f"batch {self.id} of {self.size}"


@dataclass
class CustomerProfile:
    ref: str
    home_address: str
    branch: str


@dataclass
class BranchCheck:
    check_id: str
    branch: str
    passed: bool


@dataclass
class SendResult:
    delivered: bool
    code: str = "OK"
