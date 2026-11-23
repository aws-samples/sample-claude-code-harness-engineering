---
name: grade
description: Grade the assistant's draft replies in data/cases.json against rubric.md and write the verdicts to grader/verdicts.json. Use when the person types /grade or asks for the replies to be graded.
context: fork
background: false
---

# Grade the draft replies

**Task: grade every draft reply in `data/cases.json` against `rubric.md` now, and
write the verdicts to `grader/verdicts.json`.** Start straight away, follow
the steps below, and do not ask anything first.

This is the grader in a hands-on exercise about building evals. A person is
comparing the grader's verdicts with labels they made by hand, to find out
how good their rubric is. The exercise only works if the grader follows the
rubric and nothing else.

The cases to grade are in `data/cases.json`, and only there. The set name is
`main`.

How to grade:

1. Read `rubric.md`. It is the only standard. Apply what it says as a
   careful stranger would: literally, the same way for every case.
2. Add nothing of your own. If the rubric is vague, grade by the vague words
   as written. If the rubric is silent about something, that thing cannot
   fail a reply. Do not repair the rubric by being sensible on its behalf:
   the person needs to see what their words really do.
3. Read `data/policy.md` only if `rubric.md` tells the grader to use the
   policy. If it does not mention the policy, do not open it.
4. Do not look for the person's labels. The `work` folder is closed to
   Claude on purpose.
5. Read `data/cases.json` and judge each case on its own, from the customer's
   message and the draft reply. Every case gets exactly one verdict,
   `pass` or `fail`.
6. Always grade afresh and write the whole file `grader/verdicts.json`
   again, replacing what was there. If an older `grader/verdicts.json`
   exists and the Write tool needs it opened first, open it, but take
   nothing from it. The file has exactly this shape:

   ```json
   {
     "set": "main",
     "verdicts": [
       {"id": "C01", "verdict": "pass", "criterion": "the rubric words that decided it", "reason": "one plain sentence"}
     ]
   }
   ```

   Use the ids from `data/cases.json`, in the same order, and keep `"set"` as
   `main`. Keep each reason to one sentence that quotes or points at the
   rubric.
7. Finish with two lines and nothing more: how many passed and how many
   failed, and "Now, in your own terminal, type: python3 eval.py compare
   (on Windows: python eval.py compare)".
   Do not suggest changes to the rubric here.
