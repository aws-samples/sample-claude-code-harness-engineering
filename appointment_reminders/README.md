# appointment-reminders

A small service that reminds customers about appointments at its branches. It's the code the workshop's PRs change. Read it in five minutes, or ask Claude for a tour.

| Where | What's there |
|---|---|
| `service/scheduler.py` | The core: picks reminders that are due and sends them |
| `service/models.py` | The records. Some hold customer personal data, some don't |
| `service/queueing.py`, `service/worker.py` | Background queue and worker |
| `service/records.py` | Finding records, profiles and branch checks |
| `service/startup.py`, `service/settings.py` | Start-up and tunable numbers |
| `service/risk.py` | Late-cancellation risk score |
| `tools/` | The only place that talks to outside services: bookings API, messaging, webhooks |
| `app/api/` | HTTP routes |
| `tests/` | `uv run pytest appointment_reminders/tests` |

A few things already break the team's rules. Real code does.
