"""The front desk's page, and its buttons."""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from html import escape

from appointment_reminders.app import actions
from appointment_reminders.app.api.web import Redirect, app, rate_limit
from appointment_reminders.app.state import BRANCHES
from appointment_reminders.app.views import button, page, select
from appointment_reminders.service import settings
from appointment_reminders.service.scheduler import due_appointments


def _slot(world, a, due: bool) -> str:
    customer = world.customers[a.customer_ref]
    minutes = int((a.starts_at - actions.now()).total_seconds() // 60)
    soon = f"in {minutes} min" if minutes < 120 else f"in {minutes // 60} h" if a.starts_at.date() == actions.now().date() else ""
    tags = "".join(f"<span class='tag'>{escape(t)}</span>" for t in a.tags)
    edit = (f"<details><summary>Edit</summary>"
            f"<form method='post' action='/tags'><input type='hidden' name='id' value='{a.id}'>"
            f"<input name='tags' size='16' value='{escape(', '.join(a.tags))}' aria-label='Tags'><button class='quiet'>Save tags</button></form>"
            f"<form method='post' action='/channel'><input type='hidden' name='ref' value='{customer.ref}'>"
            f"{select('channel', ['email', 'sms'], customer.channel)}<button class='quiet'>Save contact</button></form></details>")
    return (f"<li class='slot{' due' if due else ''}'><div class='time'>{a.starts_at:%H:%M}<small>{soon}</small></div><div class='dot'></div>"
            f"<div class='card'><div><span class='who'>{escape(customer.name)}</span>{tags}"
            f"<div class='sub'>{a.branch} branch, contact by {customer.channel}</div></div>"
            f"<div class='risk'>No-show risk<br>{actions.risk_of(a)}</div>"
            f"<div class='acts'>{button('/remind', 'Remind', {'id': a.id}, 'quiet')}{button('/move', 'Move a day', {'id': a.id}, 'quiet')}{edit}</div></div></li>")


def _day(moment) -> str:
    return f"{moment:%A} {moment.day} {moment:%B}"


def _sent(world) -> str:
    outbox = world.provider.outbox
    if not outbox:
        return "<p class='empty'>Nothing sent yet today. Reminders you send appear here, as the customer sees them.</p>"
    counts = Counter((m["to"], m["body"]) for m in outbox)
    items = []
    for m in reversed(outbox):
        twice = counts[(m["to"], m["body"])] > 1
        kind = "twice" if twice else "notice" if m["via"] == "bookings API" else ""
        flag = "<div class='flag'>Sent more than once</div>" if twice else ""
        items.append(f"<li class='{kind}'><div class='to'>To {escape(m['to'])}, {m['at']:%H:%M}</div>"
                     f"<div class='bubble'>{escape(m['body'])}</div>{flag}</li>")
    return f"<ul class='msgs'>{''.join(items)}</ul>"


@app.route("/")
@rate_limit()
def front_desk(request) -> str:
    world, now = request.world, actions.now()
    due = {a.id for a in due_appointments(world.appointments, now)}
    upcoming = sorted((a for a in world.appointments if a.starts_at >= now), key=lambda a: a.starts_at)
    past = sorted((a for a in world.appointments if a.starts_at < now), key=lambda a: a.starts_at, reverse=True)
    rows = [f"<li class='now'><div class='time'>{now:%H:%M}</div><div class='dot'></div><hr></li>"]
    if due:
        rows.append(f"<li class='band'>Reminders go out for these: they start in the next {settings.REMINDER_WINDOW_SECONDS // 60} minutes</li>")
    label = ""
    for a in upcoming:
        if a.id not in due:
            heading = "Later today" if a.starts_at.date() == now.date() else _day(a.starts_at)
            if heading != label:
                rows.append(f"<li class='band later'>{heading}</li>")
                label = heading
        rows.append(_slot(world, a, a.id in due))
    earlier = "".join(f"<p>{_day(a.starts_at)}, {a.starts_at:%H:%M}: {escape(world.customers[a.customer_ref].name)}, {a.branch}</p>" for a in past)
    message = request.query.get("msg", "")
    body = (f"<main><section><div class='top'><div><h1>{_day(now)}</h1>"
            f"<p class='lede'>Appointments across the {len(BRANCHES)} branches. The data is made up, and nothing really gets sent.</p></div>"
            f"{button('/send-due', f'Send {len(due)} due reminders') if due else ''}</div>"
            f"{f'<div class=note>{escape(message)}</div>' if message else ''}"
            f"<ol>{''.join(rows)}</ol>"
            f"{f'<details class=earlier><summary>Earlier ({len(past)})</summary>{earlier}</details>' if past else ''}</section>"
            f"<aside><h2>Sent to customers</h2>{_sent(world)}</aside></main>")
    trouble = [world.trouble.NAMES[name] for name in sorted(world.trouble.on)]
    return page("Front desk", f"Branches {', '.join(BRANCHES[:-1])} and {BRANCHES[-1]}", trouble, body)


@app.route("/send-due", methods=("POST",))
@rate_limit()
def send_due(request) -> Redirect:
    return Redirect("/", actions.send_due(request.world))


@app.route("/remind", methods=("POST",))
@rate_limit()
def remind(request) -> Redirect:
    return Redirect("/", actions.remind_one(request.world, request.form["id"]))


@app.route("/move", methods=("POST",))
@rate_limit()
def move(request) -> Redirect:
    appointment = request.world.appointment(request.form["id"])
    return Redirect("/", actions.move(request.world, appointment.id, f"{appointment.starts_at + timedelta(days=1):%Y-%m-%dT%H:%M}"))


@app.route("/tags", methods=("POST",))
@rate_limit()
def tags(request) -> Redirect:
    return Redirect("/", actions.tags(request.world, request.form["id"], request.form.get("tags", "")))


@app.route("/channel", methods=("POST",))
@rate_limit()
def channel(request) -> Redirect:
    return Redirect("/", actions.channel(request.world, request.form["ref"], request.form["channel"]))
