# appointment-reminders

A small web app for reminding customers about appointments across several branches. Run it with `./lab demo` and click **Open in Browser**, or open port 8000 from the **Ports** tab.

The page shows today's appointments, buttons to remind, move and edit them, and the messages customers received. Logs print in the terminal. `./lab demo --trouble provider` (or `bookings`, or `worker`) makes one of the fake services fail.

| Where | What's there |
|---|---|
| `service/` | Scheduling, reminder wording, records, settings, the queue and the worker |
| `tools/` | All calls to outside services: the bookings API, messaging, webhooks |
| `app/` | Routes in `app/api/`, HTML in `app/views.py`, button handlers in `app/actions.py`, and the server |
| `fakes/` | Fake outside services, so the app runs with no network |
| `tests/` | `uv run pytest appointment_reminders/tests` |

Some existing code already breaks the team's rules.
