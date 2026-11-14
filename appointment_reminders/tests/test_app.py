from __future__ import annotations

from appointment_reminders.app import actions
from appointment_reminders.app.api.web import Redirect, Request, app
from appointment_reminders.app.server import load_routes
from appointment_reminders.app.state import sample_world

load_routes()


def get(world, path: str) -> str:
    return app.handle(Request("GET", path, {}, {}, world))


def test_the_front_desk_renders():
    page = get(sample_world(), "/")
    assert "<html" in page and "Send 4 due reminders" in page


def test_sending_due_reminders_reaches_customers_once():
    world = sample_world()
    result = app.handle(Request("POST", "/send-due", {}, {}, world))
    assert isinstance(result, Redirect)
    sent = [(m["to"], m["body"]) for m in world.provider.outbox]
    assert len(sent) == len(set(sent)) == 4


def test_a_dropped_connection_still_delivers():
    world = sample_world()
    world.trouble.on.add("provider_blips")
    assert "reported a failure" in actions.send_due(world)
    assert len(world.provider.outbox) == 4


def test_moving_an_appointment_tells_the_customer():
    world = sample_world()
    app.handle(Request("POST", "/move", {}, {"id": "a-4"}, world))
    assert [m["to"] for m in world.provider.outbox] == ["dev.patel@example.com"]
