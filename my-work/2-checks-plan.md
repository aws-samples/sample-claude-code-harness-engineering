# 2. Plan the checks

Replace each `TODO` with your answer, then ask Claude to build it. The checks run on commit, in a git pre-commit hook.

## Which rules get a check, and does each one block or warn?

Ask Claude to copy in the rules you sorted as `check` or `both` in `my-work/1-rule-sort.md`. Then decide: a block stops the commit, and a warning lets it through and prints the finding.

| Rule | Block or warn | Why |
|---|---|---|
| TODO | TODO | TODO |

## New code only, or all of it?

`app/api/health.py` already breaks R7. Should a typo fix there be stopped?

TODO

## Three tests for your plan

There's no single right answer, but a good plan passes these:

1. A secret is caught before it reaches git history.
2. A block tells whoever hit it how to fix it.
3. Old debt doesn't block an unrelated edit, unless you chose that on purpose.
