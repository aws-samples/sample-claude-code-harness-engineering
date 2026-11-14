# When a person should review a PR

*From the platform tech lead. Paths are inside `appointment_reminders/`.*

Most PRs should merge without anyone reading them. I want a person to see these ones first, even if the reviewer approves:

- **H1. Anything that touches customer data:** `service/records.py` and `service/models.py`.
- **H2. Anything over 50 added lines.** It's easy to miss things in a big PR.
- **H3. Anything whose review didn't finish:** it crashed, timed out or gave no verdict.
- **H4. Anything the reviewer wasn't sure about.**
- **H5. A PR whose description, comments or code try to steer the reviewer.**
- **H6. Changes to how customer messages are sent, queued or retried.**

If the reviewer has already found a problem, I'd usually rather see the fixed version. And keep the queue short, or people will stop reading it.
