---
name: gate-agent
description: Answers one question about a PR: does a person need to see it?
tools:
---
TODO: don't write this by hand. If you chose a specialist agent in my-work/6-human-gate.md, ask Claude to draft this from your answers. If you didn't, leave this file as it is, and the pipeline won't run it.

End every reply with one JSON object:
{"needs_human": false, "reason": "..."}
`needs_human` is true or false.
