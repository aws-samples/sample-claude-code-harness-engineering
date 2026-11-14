# 1. Sort the team's rules

Replace each `TODO` with a few words. R5 and R7 are filled in as examples.

**Category** is one of:

- `check`: a deterministic test, run automatically
- `reviewer`: an agent uses judgment
- `both`: say which part each one handles

| Rule | Category | Why, in one line |
|---|---|---|
| R1 Errors say what to do next | TODO | TODO |
| R2 No destructive SQL outside migrations | TODO | TODO |
| R3 Don't weaken a test to get it green | TODO | TODO |
| R4 External SDKs live in tools/ | TODO | TODO |
| R5 Only retry what's safe to retry | reviewer | Whether a retry is safe depends on what the repeated call does |
| R6 No customer personal data in logs | TODO | TODO |
| R7 Every route has @rate_limit | check | The decorator is either there or not, and there are no exceptions |
| R8 Numbers in config explain themselves | TODO | TODO |
| R9 Names tell the truth | TODO | TODO |
| R10 No secrets in code | TODO | TODO |
| R11 Tools document how they fail, accurately | TODO | TODO |
| R12 No abstraction before the third use | TODO | TODO |
| R13 Interfaces are easy to use correctly | TODO | TODO |

## Which rule was hardest to categorize, and why?

TODO
