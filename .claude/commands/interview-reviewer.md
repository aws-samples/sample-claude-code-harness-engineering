---
description: Interview me, then draft my reviewer agent in my-work/3-reviewer-agent.md
---
Interview me to design my PR reviewer agent. Ask one question at a time, keep it conversational, and react briefly to each answer.

First read my-work/1-rule-sort.md, so you know which rules I gave the reviewer. Then ask:

1. These are the rules you gave it (list them). Is anything missing? Should it comment on what your checks already enforce?
2. When it's unsure, should it flag, or stay quiet? What does that cost either way?
3. R13 is the lead's preferences on interface design, and it's less clear-cut than the other rules. Is a yes-or-no finding enough here, or does the agent need to report something else, like a score? If they choose a score, what does each level mean? Ask for their view, and don't suggest a design first.
4. What should each result do: block, comment or stay quiet? And what should the agent do when two of the preferences pull against each other?

Then draft the file in my words, not yours. The agent can't read docs/team-rules.md when it runs, so the rules it needs must be in the file. Leave the `tools:` line as it is. Keep what's already at the end of the file about the JSON reply. If I chose to report anything extra, such as a score, add it as a field on that rule's finding, and show that in the JSON example, so that ./lab review prints it. Remove the TODO line. Show me the result and ask what I'd change.
