---
description: Explain what a PR does, and the lead's label for it if there is one
argument-hint: pr-01
---
Help me understand the PR $ARGUMENTS, from its .diff file in data/review-prs/.

Tell me in a few lines what it changes and why it says it does. Show me the code it touches or calls in appointment_reminders, and what that code does. Mention that `./lab demo $ARGUMENTS` runs the app with the PR applied. If its bug only shows when something fails, give the `--trouble` flag too: `bookings` for `tools/bookings_client.py` or `tools/rebooking.py`, and `provider` for `tools/messaging.py`, as in `./lab demo $ARGUMENTS --trouble bookings`.

If data/review-prs/lead-labels.csv, or the labels.csv in the PR's own folder, has a label for it, show me the label and explain why the lead decided that: what in the code makes it need changes, or makes it fine. Say whether the diff alone shows it, or you need to read the code it calls. If you think the label is arguable, say why, and leave the decision to me.

If it has no label, end with one or two neutral questions worth checking, and don't give a verdict unless I ask.
