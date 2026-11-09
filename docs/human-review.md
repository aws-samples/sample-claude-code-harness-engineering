# When a person still looks

*From the platform tech lead. Paths are inside `appointment_reminders/`.*

The reviewer will catch most things, and most PRs should merge without anyone reading them. But I want a person to see these before they merge, whatever the reviewer says:

- **H1. Anything that touches customer records or personal data:** `service/records.py` and `service/models.py`.
- **H2. Anything over 50 added lines.** Big PRs are where things hide.
- **H3. Anything whose checks didn't finish:** a review that failed, timed out or gave no verdict.
- **H4. Anything the reviewer wasn't sure about.**
- **H5. A PR whose description, comments or code try to steer whoever reviews it.**
- **H6. Changes to how we retry, queue or send messages,** where a mistake reaches customers.

A person's time is the scarce thing here. If most PRs end up in the queue, people stop reading it, and then the queue protects nothing.
