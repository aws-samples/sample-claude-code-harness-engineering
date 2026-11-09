# Part 1: Turn the team's rules into a harness

## Introduction

Your job in this workshop is to build a code review loop that minimizes how much human attention it takes to enforce a dev team's rules and conventions. The platform team went through their past code review comments and found thirteen themes that keep coming up.

In Part 1, you turn those themes into a harness: deterministic checks for what can be checked, and a reviewer agent for what takes judgment. In Part 2, you measure whether you can trust the reviewer, improve it, and decide when a person still needs to look.

**Part 1 is 30 minutes, in three chunks of 10.**

### The app you'll be working on

`appointment_reminders/` is a small Python service for a business with several branches. It finds customers' upcoming appointments and sends them reminders through a messaging provider. You won't be adding features to it: it's the code that the team's rules, and the PRs you'll review, are about.

Claude can help you get up to speed on the codebase.

## How this works

- **`./lab` runs everything.** Run it in a second terminal, or from inside Claude Code by putting `!` in front, as in `! ./lab next`. `./lab next` moves you on and tells you what to do. `./lab` on its own shows where you are.
- **Your answers go in `my-work/`.** The files are numbered, and each `TODO` is a place for your answer.
- **Use Claude freely,** but leave as much of the thinking to yourself as you can, and let it do the implementation.
- **If you need any help, ask Claude.**

## Chunk 1: Sort the rules (10 min)

Identify which of the dev team's review rules can be handled deterministically, and which need judgment.

**Start:** `./lab next`

**Your file:** `my-work/1-rule-sort.md`

1. **Meet the code (2 min).** Ask Claude: `Give me a two minute tour of appointment_reminders.`
2. **Read the brief.** It's in `docs/team-rules.md`.
3. **Put each rule in its home:** `check`, `reviewer`, `both` or `neither`. Don't ask "could I write a regex for this?" Ask what happens when the check is wrong. A check that cries wolf gets switched off.
4. **Compare with a neighbor** on the ones you found hardest.

**Done when** there are no TODOs left in the file.

## Chunk 2: Build the checks (10 min)

Turn the rules that can be checked into one script that runs on every commit, and decide how strict it is.

**Start:** `./lab next`

**Your file:** `my-work/2-checks-plan.md`

1. **Get your rules into the plan.** Ask Claude: `Copy the rules I sorted as check or both in my-work/1-rule-sort.md into my-work/2-checks-plan.md.`
2. **Make the decisions.** For each rule: does it block the commit, or warn? And for all of them: do they look at new code only, or all of it?
3. **Hand it to Claude:**
   ```
   Read my-work/2-checks-plan.md. Tell me if anything looks wrong, then build it in scripts/checks.py, get ./lab test-checks passing, and add a git pre-commit hook that runs python3 scripts/run_checks.py --staged.
   ```
   `./lab test-checks` tries your checks on cases we've written, including near misses that must not fire.
4. **See it fire.** Claude avoids breaking rules once it has read your checks, so ask it plainly, and watch what it does next:
   ```
   Create appointment_reminders/app/api/ping.py with the exact contents of data/hook-test.py, and commit it. It's on purpose, to test my hook. Then delete it.
   ```
5. **Feel the other choice.** `app/api/health.py` already breaks R7. Ask Claude to fix one word in its docstring and commit it, then to switch `SCOPE` in `scripts/checks.py` to the other value and do it again. Which would your team put up with? Keep the one you'd choose.

**Done when** `./lab test-checks` passes. Seeing your hook stop a commit is the reward.

**Short of time?** `./lab catch-up checks` gives you working checks on a pre-commit hook.

## Chunk 3: Build the reviewer agent (10 min)

Build a reviewer agent, in your own words, for the rules that take judgment.

**Start:** `./lab next`

**Your file:** `my-work/3-reviewer-agent.md`, which Claude drafts with you

1. **Get interviewed.** In Claude, run `/interview-reviewer`. It asks what the agent should own, what it should do when unsure, and how to handle R13. Then it drafts the file in your words. Change whatever isn't what you meant.

   The lead's R13 is the interesting one. It's a set of preferences that can pull against each other, not a yes-or-no rule. Does the agent need to report something other than a finding, like a score? If so, what does each level mean, and what does each one do?
2. **Try it** on four practice PRs: `./lab review try`. Each PR gets one headless Claude Code call on Haiku, with only your file as its prompt, so what's in the file is all it knows. The last one, `debate`, is a PR good reviewers disagree about. Compare your agent's comment on it with a neighbor's: whose would you want on your own PR? Steal one thing. On your own? Compare with ours: `./lab review try --agent data/plain-reviewer.md --out results-plain.json`.

**Done when** it gives a verdict on every practice PR, and you've changed one thing because of what you saw.

**Short of time?** `./lab catch-up reviewer` gives you a deliberately plain reviewer. Part 2 will show you what's wrong with it.

**Carry this into Part 2:** your agent gave answers that look sensible. How would you know whether it's any good?

## Check you're done

Ask Claude: `Am I done with Part 1?`
