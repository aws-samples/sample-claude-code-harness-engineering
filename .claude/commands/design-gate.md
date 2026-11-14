---
description: Talk through my human gate, then build and test it
---
Help me design and build my human gate. Ask one question at a time, keep it short, and ask for my view before you give the trade-offs.

First read docs/human-review.md, my-work/5-human-gate.md and my-work/notes.md. If my holdout didn't clear my bar, say what it got wrong in one line, and ask whether that kind of PR should go to a person too. Then ask:

1. For each of H5 and H6: code, my reviewer, a specialist, or more than one? Test each answer with "how would this miss one?"
2. When a PR needs a person and my reviewer has also asked for changes, who gets it first? Is it the same for every preference?
3. How many fixes does Claude get before a person steps in?

Write my answers into my-work/5-human-gate.md, in my words. Build `route()` in scripts/gate.py, with H1 to H3 as code. For H4, always add this to my reviewer, before its JSON instructions: "If you've read the code and still can't tell whether a rule is broken, add `"ask_human": "why, in one sentence"` to your JSON. Leave it out when you're sure, either way." If I chose my reviewer for H5 or H6, extend that line. If I chose a specialist, write my-work/6-gate-agent.md. Don't read data/review-prs/gate/ to tune rules to those PRs. Run `./lab test-gate`. If a case fails because of a choice I made, show me and ask what I want to change, rather than changing the design yourself.
