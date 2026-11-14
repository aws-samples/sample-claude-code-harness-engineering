---
name: gate-agent
description: Answers one question about a PR: does a person need to see it?
tools:
---
TODO: don't write this by hand. /design-gate drafts it if you choose a specialist. Otherwise leave it as it is and it won't run.

End every reply with one JSON object:
{"needs_human": false, "preference": "", "reason": "..."}
`needs_human` is true or false. When it's true, `preference` is the H number, such as "H6".
