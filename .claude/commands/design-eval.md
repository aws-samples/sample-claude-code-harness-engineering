---
description: Talk through how to score my reviewer, then build and test the scorer
---
Help me design and build the scorer for my PR reviewer. Ask one question at a time, keep it short, and ask for my view before you give yours.

First read my-work/4-eval-design.md and data/review-prs/lead-labels.csv. Don't run my reviewer: that's the next chunk. Use labeled PRs as the examples. Then ask:

1. What counts as caught? If the verdict is right but the rule is wrong? If a PR breaks two rules and it names one?
2. What should we measure? Caught and false alarms are the minimum. Is there anything else worth counting? Don't suggest anything: if I say no, move on.
3. What's my bar for letting an approved PR merge with no person: how many misses out of eight, and how many false alarms? Get two numbers.

Write my answers into questions 1 to 3 of my-work/4-eval-design.md, in my words. Build `result()` and `score()` in scripts/score.py from those answers and nothing more: don't read scripts/test_scorer.py first, and don't add measures I haven't asked for. Then run `./lab test-scorer`.

If a fake reviewer gets past, show me what it did and ask what my scorer should count. Write my answer into question 4, update the scorer and run the test again. If none gets past, ask me why the third one failed, and write that in. Finish by telling me to run `./lab next`.
