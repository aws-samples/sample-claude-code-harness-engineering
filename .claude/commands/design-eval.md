---
description: Talk through how to measure your reviewer, then write my-work/4-eval-design.md
---
Help me design an eval for my PR reviewer agent. Ask one question at a time, keep it conversational, and react briefly to each answer. Ask for my view before you give yours.

First read my-work/3-reviewer-agent.md and data/review-prs/lead-labels.csv, so you know what the agent does and what the gold labels say. Then read my-work/4-eval-design.md and keep anything I've already written there. Don't tell me patterns in the PRs or labels unless you've checked them in the files. Then ask the questions in that file, in order:

1. What are the properties of a good review from this agent? If I start with a metric, ask what a good review does instead.
2. How will the labels be used? What counts as right on one PR: the verdict, the rule, the reasoning?
3. What could make the score lie?
4. How good must it be for each job: leaving a comment, blocking a merge, approving alone? A miss and a false alarm cost the team different things.

Then write my answers into my-work/4-eval-design.md, in my words, not yours, replacing each TODO. Show me the result and ask what I'd change.
