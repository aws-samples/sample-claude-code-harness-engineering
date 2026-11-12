---
description: Talk through my deterministic checks with me, then build them and the pre-commit hook
---
Help me plan and build my deterministic checks. Ask one question at a time, keep it conversational, and react briefly to each answer. For each question, ask what I think before you give the trade-offs. If I'm not sure, help me reach a best guess: that's fine here.

First read my-work/1-rule-sort.md, and list the rules I sorted as `check` or `both`. For a `both` rule, say which part the check would handle. Then ask:

1. Should each of these block Claude's commit when it fires, or only warn? A block means Claude has to fix it before it can commit. A warning lets the commit through, and Claude sees the message. The question to ask of each rule is how often the check could be wrong: a check that is never wrong can block, and one that only finds suspects is better as a warning, with the reviewer deciding.
2. Should the checks look only at the code a commit adds, or at every file it touches, old code included? `appointment_reminders/app/api/health.py` already breaks R7. With "all of it", fixing a typo in that file is blocked until someone fixes the old problem too.
3. How might you stop Claude from "cheating", by editing or skipping the checks rather than fixing its code? Ideas, if I'm stuck: deny `git commit --no-verify` and edits to the checks in Claude Code's permissions; run the same checks again in CI, from the main branch, so a PR can't change what checks it; or have a person review any PR that changes the checks, which Part 2's human gate could do. None is perfect, so ask which I'd want.

Then:

- Write my answers into my-work/2-checks-plan.md, in my words, replacing every TODO.
- Build the checks in scripts/checks.py: `POLICY` with "block" or "warn" for each rule, `SCOPE` as "new" or "all", and `check_source()`. Each finding's message tells whoever hit it how to fix it. Run `./lab test-checks` and make it pass, including the table of check PRs at the end. A rule marked "for your reviewer" there is fine.
- Add the git pre-commit hook: `.githooks/pre-commit` running `python3 scripts/run_checks.py --staged`, made executable, with `git config core.hooksPath .githooks`.
- If I chose a guard that can be set up here, such as permission rules, set it up in `.claude/settings.local.json`, which isn't committed. Don't change `.claude/settings.json`.

Show me what you built in a few lines, and what the PR table says.
