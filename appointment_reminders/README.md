# appointment-reminders

A small web app that a business with several branches uses to remind customers about appointments. It's the code the workshop's PRs change. Run it with `./lab demo` and open http://localhost:8000, or ask Claude for a tour.

The page is the front desk's: today's appointments, which are due a reminder, buttons to remind, move and edit, and every message customers received. The code behind it is mostly `service/scheduler.py`, `tools/messaging.py`, `tools/rebooking.py` and `tools/bookings_client.py`. The rest of the service (the background worker, branch records, settings and quotas) runs out of sight, as it would for real. Its logs print in the terminal, and `./lab demo --trouble provider` (or `bookings`, or `worker`) makes a stand-in service misbehave.

| Where | What's there |
|---|---|
| `service/` | The core: what's due, the reminder wording, records, settings, the queue and the worker |
| `tools/` | The only place that talks to outside services: the bookings API, messaging, webhooks |
| `app/` | The web app: routes in `app/api/`, the page's HTML in `app/views.py`, what each button does in `app/actions.py`, and the server |
| `fakes/` | Stand-ins for the outside services, so the app runs with no network. `--trouble` switches their failures on |
| `tests/` | `uv run pytest appointment_reminders/tests` |

A few things already break the team's rules. Real code does.
