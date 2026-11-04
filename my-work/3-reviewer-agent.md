---
name: pr-reviewer
description: Reviews one PR against the team's judgment rules. Report only.
tools:
---
TODO: don't write this by hand. Run /interview-reviewer in Claude, and it will draft this with you.

End every reply with one JSON object:
{"verdict": "approve", "findings": [{"rule": "R5", "why": "..."}]}
`verdict` is `approve` or `request_changes`.
