from __future__ import annotations

import pytest

from appointment_reminders.service.models import Reminder
from appointment_reminders.service.scheduler import send_all


class FakeGateway:
    def __init__(self, fail_every: int = 0) -> None:
        self.fail_every = fail_every
        self.calls = 0

    def send(self, reminder: Reminder) -> None:
        self.calls += 1
        if self.fail_every and self.calls % self.fail_every == 0:
            raise ConnectionError


@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway(fail_every=3)


def test_reminder_reports_gateway_failure(gateway):
    reminders = [Reminder(str(n), "someone@example.com", "See you soon") for n in range(3)]
    results = send_all(reminders, gateway)
    assert results[2].code == "GATEWAY_DOWN"
