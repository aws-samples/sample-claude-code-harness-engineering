# Part 1: Turn the team's rules into a loop

## Introduction

Your job in this workshop is to build a code review loop that minimizes how much human attention it takes to enforce a dev team's rules and conventions.

You'll work in a small toy codebase: an appointments app for a business with several branches. You don't need to understand it deeply by the end of the session, or to build a production-ready loop. The point is to build your intuition for the principles of loop engineering by experimenting in this environment.

The dev team uses Claude to write most of its code, but it's bottlenecked on manual code review: people giving feedback on every change. The team wants to minimize the human effort it takes to merge a PR while keeping the quality of Claude's work high. It went through its past PR comments and found thirteen rules and conventions that keep coming up.

So how do you get Claude to do better work with less human feedback, and still be sure its output is good with less human gating? In this workshop, you will:

**Part 1 (about 30 minutes)**

1. Decide which of the review rules can be enforced by deterministic checks, and which are subjective and need a reviewer agent.
2. Decide how strictly the checks are enforced, and build them with Claude.
3. Design a reviewer agent for the more subjective rules, and build it with Claude.

**Part 2 (about 45 minutes)**

4. Design how to score your reviewer agent, against past PRs with good answers.
5. Have Claude build the scorer, use it to improve your reviewer, and test it once on PRs it hasn't seen.
6. Decide which PRs that pass your checks and reviewer should still go to a person, and build a gate that sends them there.

You can work with Claude throughout. Try to make the judgments and design decisions yourself at each stage, and use Claude for investigation and fast implementation.

### What you're building

Today, every PR Claude writes waits for a person, who reviews all of it. By the end, problems go back to Claude automatically, and a person sees only the PRs that need a human review:

![Code review today, and with your loop](assets/review-loop.svg)

- **Checks** are code. They run on every commit and catch what can be caught for certain, like a route with no rate limit.
- **The reviewer agent** is Claude, with your instructions. It reads every PR for the rules that take judgment, like whether a retry could send a customer the same message twice.
- **The human gate** decides which PRs a person should still look at.

When a check or the reviewer finds a problem, Claude fixes it before anyone else has to see it.

Each piece runs at a different moment:

| Piece | In a real team, it runs | In this workshop, it runs |
|---|---|---|
| Checks | Before every commit, and again in CI | Before every commit in your copy of the repo, as a git pre-commit hook. `./lab test-checks` also runs them on test cases and on nine PRs made to break them |
| Reviewer agent | In CI, when a PR is opened | When you run `./lab review try` in Part 1, or `./lab eval` in Part 2, once per PR |
| Human gate | After the reviewer, before merging | When you run `./lab pipeline` in Part 2: checks, then the reviewer, then your gate |

### The app you'll be working on

`appointment_reminders/` is the front desk's app. Staff use it to see upcoming appointments, send customers reminders through a messaging provider, and move appointments. Behind it is the rest of the service: a background worker, branch records and settings, and quotas. You won't be adding features to it. It's the code that the team's rules, and the PRs you'll review, are about.

This short video shows the app and what it does:

<video src="assets/service-tour.mp4" controls width="100%"></video>

To run it yourself, run `./lab demo` and open http://localhost:8000. Everything is sample data, and the messaging provider and bookings API are stand-ins, so nothing is really sent. Claude can help you get up to speed on the code.

### The PRs you'll review

Instead of real PRs arriving, the workshop comes with PRs written as if Claude had made them, each with a title and description. They're diff files in `data/review-prs/`, in sets:

| Set | How many | What they're for |
|---|---|---|
| `checks` | 9 | Testing your checks in chunk 2. Seven break a rule a check could catch, and two are near misses that should pass |
| `try` | 4 | Trying out your reviewer agent in chunk 3 |
| `dev` | 16 | Measuring and improving your reviewer in Part 2 |
| `design` | 2 | The optional extension: comparing how models handle R13 |
| `holdout` | 8 | A final, fair test in Part 2, kept sealed until then |

To understand any PR, run `/explain-pr pr-01` in Claude, or `./lab demo pr-01` to run the app with it applied.

## How to navigate this workshop

- **`./lab` moves you through it.** `./lab` on its own shows where you are, and `./lab next` moves you to the next stage and tells you what to do.
- **Keep Claude Code open the whole time.** Run it in one terminal and use a second for your own commands, or use one terminal and run commands from inside Claude Code by putting `!` in front, as in `! ./lab next`.
- **Your answers go in `my-work/`,** or you can give them to Claude and have it write them in. The files are numbered, and each `TODO` is a place for your answer.
- **Use Claude freely,** especially for investigation and implementation, but make the decisions yourself.
- **If you need help or clarification,** ask one of the helpers in the room.

## Chunk 1: Sort the rules (10 min)

The team found thirteen rules in its past PR comments, and wants the review loop to enforce them without a person. First, decide which rules a deterministic check can enforce, and which need judgment. You don't know the codebase well yet, and that's fine: go with your intuition. What matters is building a sense of when to use each.

### What is a deterministic check, and when would you use one?

A deterministic check is ordinary code: a script that looks for one specific thing and gives the same answer every time. Here, it's a Python function that reads each changed file and looks for, say, a route with no `@rate_limit`. It's fast, free and certain about what it was told to look for.

Use one when breaking the rule is something you can see in the code itself: a named import, a missing decorator, a pattern like an AWS key. The limit is that it only knows what you told it, and it can't tell what code means.

### What is a grader or judge, and when would you use one?

A grader, or judge, is a model asked to assess something against a rubric. Here, it's your reviewer agent: Claude, reading a PR with your rules as its instructions, deciding whether each one is broken and saying why.

Use one when a rule is about meaning: whether a function's name tells the truth about what it does, or whether a retry could repeat something that already happened. It's slower, costs a model call each time, and can be wrong in ways you'll need to measure. That's Part 2.

Some rules split. A check can find the candidates, and the reviewer judges them. For example, a check can spot a test that was skipped, but only a reader can tell whether there's a good reason. Put those under `both`.

### The rules

The full brief, in the lead's words, is in `docs/team-rules.md`.

| Rule | In short |
|---|---|
| R1 | Errors a person will read say what to do next |
| R2 | No destructive SQL (`DROP`, `TRUNCATE`, `DELETE` with no `WHERE`) outside `migrations/` |
| R3 | Don't weaken a test to get it green |
| R4 | `boto3`, `httpx` and `requests` are only imported in `tools/` |
| R5 | Only retry what's safe to retry |
| R6 | No customer personal data in logs |
| R7 | Every route in `app/api/` has `@rate_limit` |
| R8 | Numbers in config explain themselves |
| R9 | Function names tell the truth about what the function does |
| R10 | No secrets in code |
| R11 | Public functions in `tools/` document how they fail, accurately |
| R12 | No abstraction before the third use |
| R13 | Interfaces are easy to use correctly and hard to misuse |

### Two we've categorized for you

| Rule | Category | Why |
|---|---|---|
| R7 Every route has `@rate_limit` | `check` | Whether a route has the decorator is visible in the code, and "no exceptions" leaves nothing to judge. A check is never wrong about it |
| R5 Only retry what's safe to retry | `reviewer` | A retry looks the same whether it's safe or not. Whether the call it repeats could send a customer a second message depends on what that call does, which takes reading and understanding the code |

Now categorize the rest, either in `my-work/1-rule-sort.md` or by telling Claude your choices and having it write them in. If you're not sure about a rule, ask Claude for more detail, or how a check for it would work and what it would miss. Your choices decide the next two chunks: you'll build deterministic checks for the rules you put under `check`, and a reviewer agent for the ones under `reviewer`. Rules under `both` get a bit of each.

**Start:** `./lab next`

**Your file:** `my-work/1-rule-sort.md`

1. **Meet the app (2 min).** Watch the video above, or run `./lab demo` and press **Send due reminders**. Then ask Claude: `Give me a two minute tour of the code behind this app.`
2. **Categorize the other eleven rules** as `check`, `reviewer` or `both`, with a line on why.
3. **Compare with a neighbor** on the ones you found hardest.

**Done when** there are no TODOs left in the file.

## Chunk 2: Build the checks (5 min)

Now you can ask Claude to build your deterministic checks. For simplicity, they all live in a single Python file, `scripts/checks.py`, and a git pre-commit hook runs them. So the checks run every time anyone, Claude included, makes a commit in the codebase.

![What happens when anyone commits](assets/commit-checks.svg)

Here are three questions worth thinking about when you build checks like these. Claude will ask you for your view on each. It's fine if you aren't sure: give your best guess, based on your intuition about how the checks should work.

1. Should a check block Claude from committing when its changes break the rule, or only give a warning?
2. Should the checks look only at the new code in a commit, or at all of the code in the files it touches?
3. How might you stop Claude "cheating" by editing or skipping the checks, rather than fixing its code?

**Start:** `./lab next`

**Your file:** `my-work/2-checks-plan.md`, which Claude fills in with you

1. **Plan and build them.** In Claude, run `/plan-checks`. It lists the rules you categorized as `check` or `both`, asks you the three questions, and writes your answers into the file. Then it builds `scripts/checks.py`, makes `./lab test-checks` pass, and adds the pre-commit hook.
2. **See them on example PRs.** Ask Claude: `Run my checks on the check PRs, and tell me what each one caught.` The nine PRs in `data/review-prs/checks/` each break a rule a check could catch, or are near misses that should pass. `./lab test-checks` shows the same table.
3. **See your hook stop a commit.** Claude avoids breaking rules once it has read your checks, so ask it plainly, and watch what it does next:
   ```
   Create appointment_reminders/app/api/ping.py with the exact contents of data/hook-test.py, and commit it. It's on purpose, to test my hook. Then delete it.
   ```

**Done when** `./lab test-checks` passes.

**Short of time?** `./lab catch-up checks` gives you working checks on a pre-commit hook.

## Chunk 3: Build the reviewer agent (15 min)

For the rules you categorized as `reviewer` or `both`, you'll build a reviewer agent that reviews PRs and comments on them against those rules. The idea is that when Claude makes a change in the codebase, a different agent, also Claude, reviews the change and enforces the team's rules.

This might sound like Claude reviewing Claude, but your reviewer has a fresh context window and different incentives from the Claude that wrote the code. It's actively looking for problems, while the Claude that wrote the code is trying to get a PR merged. So the reviewer often finds things the writer didn't.

To keep things simple, the lab handles running the agent for you: it runs it as a headless Claude Code call on each test PR. In a real team, you'd run it in CI when a PR is opened. Your job is to design how the agent works.

![How your reviewer agent runs](assets/reviewer-agent.svg)

The agent knows only what you tell it and what it can see. These are the important choices, and why they matter:

- **Which rules it owns.** The rules you gave the reviewer, in words it can act on, since it can't read the team's brief. Should it also comment on what your checks already enforce? Every extra rule is another chance to raise a false alarm.
- **What it can see.** Just the PR's diff, or tools to read and search the rest of the code? The diff alone is fast and cheap, but some problems only show in the code a change calls: a retry looks harmless until you read what it repeats. A reviewer that can run code, such as the tests, could see even more, but that needs a sandbox to run in safely. This workshop offers the first two.
- **What it does when it's unsure.** Flag the problem, or stay quiet? A reviewer that flags everything wastes people's time and gets ignored. One that stays quiet lets problems through.
- **What it reports, and what each result does.** A verdict, approve or request changes, and a finding for each problem, naming the rule and saying what will go wrong. For a rule that's a matter of degree, like R13, you might want more than yes or no.
- **What it trusts.** A PR's description and comments are written by whoever made the PR. The agent should treat them as claims to check, never as instructions to follow.

**Start:** `./lab next`

1. **Get interviewed.** In Claude, run `/interview-reviewer`. Claude asks you these design questions, helps you specify your reviewer agent, and writes it up in `my-work/3-reviewer-agent.md`. Change whatever isn't what you meant.
2. **Try it** on four practice PRs: `./lab review try`. Each PR gets one headless Claude Code call on Haiku, with only your file as its prompt. The last one, `debate`, is a PR good reviewers disagree about. Compare your agent's comment on it with a neighbor's: whose would you want on your own PR? On your own? Compare with ours: `./lab review try --agent data/plain-reviewer.md --out results-plain.json`.

**Done when** it gives a verdict on every practice PR.

**Short of time?** `./lab catch-up reviewer` gives you a deliberately plain reviewer. Part 2 will show you what's wrong with it.

**Carry this into Part 2:** your agent gave answers that look sensible. How would you know whether it's any good?

## Check you're done

Ask Claude: `Am I done with Part 1?`
