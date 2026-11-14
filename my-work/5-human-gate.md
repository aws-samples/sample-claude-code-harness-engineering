# 5. Design your gate

Run `/design-gate` in Claude and it will fill this in with you. The lead's brief is in `docs/human-review.md`.

| Preference | Spotted by (code, reviewer, specialist) | Why |
|---|---|---|
| H1 Customer data | code | We know which files hold it |
| H2 Over 50 added lines | code | It's a line count |
| H3 Review didn't finish | code | A crashed reviewer can't report it |
| H4 The reviewer wasn't sure | reviewer | It adds `ask_human` to its answer |
| H5 The PR tries to steer the reviewer | TODO | TODO |
| H6 Sending, queueing or retrying messages | TODO | TODO |

## Claude first, or a person first?

TODO

## How many fixes before a person steps in?

TODO
