# Part 2: Measure your reviewer and close the loop

## Introduction

In Part 1 you built deterministic checks and a reviewer agent. The checks give the same answer every time, but the reviewer makes judgment calls that can change between runs. You need to measure how good it is before you let it decide what merges.

In chunk 4 you'll build a scorer for your reviewer, and in chunk 5 you'll use it to make the reviewer better. In chunk 6 you'll put everything together, so that Claude gets feedback on a PR and fixes it until it either merges or goes to a person. Part 2 takes about 45 minutes.

## Chunk 4: Build a scorer (12 min)

In this chunk you'll decide how to score your reviewer. Claude will interview you and then write the code, and you'll use it in chunk 5.

### What is an eval?

An eval is a test suite for an agent. You run the agent on cases where you already know a good answer, compare what it says with that answer, and add up the results into a score. In Part 1 your reviewer was judging PRs. The eval is how you judge the reviewer.

![How an eval scores your reviewer](assets/eval-scoring.svg)

### What is a gold set?

A gold set is the collection of test cases and their good answers. Here each case is a past PR, and its answer is a **label** written by the team lead. The label says whether the PR needed changes, which rule it broke and why. For example:

| PR | What it does | Needs changes? | Rule | The lead's reason |
|---|---|---|---|---|
| pr-01 | Retries appointment moves on timeout | yes | R5 | `set_appointment_time` also emails the customer, so a retry can email twice |
| pr-02 | Retries channel changes on timeout | no | | `set_contact_preference` is a plain PUT, so it's safe to repeat |
| pr-13 | Logs reminders as they're queued | yes | R6 | `Reminder` is a dataclass, so `%s` prints `customer_email` |

Your score is only as useful as your gold set. We built this one so that a reviewer can't do well by guessing:

- **Half the PRs are fine.** If every PR had a problem, a reviewer that flags everything would get a perfect score.
- **Most PRs come in similar pairs.** pr-01 and pr-02 add almost the same retry loop, and only one is a problem. A reviewer has to understand the code to get both right.
- **It covers the rules that need judgment:** R1, R3, R5, R6, R8, R9, R11 and R12. No PR is labeled R13, so blocking a fine PR on R13 counts as a false alarm.
- **It's split in two.** You tune your reviewer on sixteen `dev` PRs. Another sixteen, the `holdout`, stay sealed until the end of chunk 5, so you can check it works on PRs you didn't tune it on.

On a real codebase, you'd build a gold set from past code reviews by experienced developers, and from PRs that passed review but later caused an incident or rollback.

### What does the scorer do?

You are going to work with Claude to build a scorer, which evaluates the performance of your reviewer against the test PRs. It's a short Python script. For each PR, it compares your reviewer's answer with the label and gives it a result:

| | Your reviewer asked for changes | Your reviewer approved |
|---|---|---|
| **The label says it needs changes** | Caught | **Miss** (false negative): the problem merges |
| **The label says it's fine** | **False alarm** (false positive): Claude reworks good code | Correct |

Then it adds the results up into measures. You need more than one, because a single number is easy to game. Both of these fake reviewers agree with the lead on half the PRs, and each looks perfect on one measure:

| Fake reviewer | Caught | False alarms |
|---|---|---|
| Approves every PR | 0 of 8 | 0 of 8 |
| Flags every PR | 8 of 8 | 8 of 8 |

### Your decisions

Claude will ask you these three questions in the interview. If you aren't sure, give your best guess.

1. **What counts as caught?** The lead says a PR breaks R5. Does your reviewer get credit if it asks for changes but names R9, so Claude would fix the wrong thing?
2. **What do you measure?** Caught and false alarms are the minimum. Think about what makes a review useful to whoever has to act on it. Is there anything else worth counting?
3. **What's your bar?** In chunk 6, a PR your reviewer approves could merge without a person reading it. How many misses out of eight would you accept for that, and how many false alarms? Set it now, before you've seen any scores.

**Start:** `./lab next`

**Your file:** `my-work/4-eval-design.md`, which Claude fills in with you

1. **Get interviewed.** In Claude, run `/design-eval`. It asks you the three questions, writes your answers into your file and builds the scorer in `scripts/score.py`. To look at a PR and its label first, run `/explain-pr pr-01`.
2. **Check the scorer.** At the end of the interview, Claude runs `./lab test-scorer`. This tries your scorer on the two fake reviewers above, plus a third that's harder to spot. If your scorer rates the third as perfect, decide with Claude what else to count.

**Done when** `./lab test-scorer` passes.

**Short of time?** `./lab catch-up scorer` gives you a working scorer.

## Chunk 5: Improve your reviewer (18 min)

Now you can score your reviewer and improve it: run it, read what it got wrong, change one thing and run it again. Claude can make the edits. Your job is to decide what to change and check that it helped.

The kind of error usually points to the fix:

| You see | It often means | You could try |
|---|---|---|
| False alarms | It's raising nitpicks, hypotheticals or problems that were there before the PR | Telling it how sure to be before asking for changes, and what's out of scope |
| Misses, or the same answer on similar PRs like pr-01 and pr-02 | The diff doesn't give it enough information | Letting it read the code: `tools: Read, Grep, Glob` |
| A miss on a rule you gave to your checks | The check can't detect this case, and the rule isn't in your reviewer's instructions | Adding the rule to your reviewer as well |

The score can also mislead you:

- **Noise.** The same reviewer gives different answers on different runs. A change that moves the score by one PR may have done nothing.
- **Overfitting.** Adding a line like "`set_appointment_time` sends an email" fixes pr-01, but it won't help on any other PR. Check Claude's suggestions for this.
- **Wrong labels.** Sometimes your reviewer is right and the label is wrong. If you think so, you can change it in `data/review-prs/lead-labels.csv`.

The holdout is how you catch overfitting, like a train/test split. If your score is much worse on the holdout than on the dev PRs, your reviewer learned those sixteen PRs rather than the rules. You only run it once, because tuning after you've seen the results would turn it into another dev set.

**Start:** `./lab next`

**Your file:** `my-work/3-reviewer-agent.md`

1. **Get your baseline:** `./lab eval`. It runs your reviewer on the sixteen dev PRs (about a minute) and shows its answers next to the labels, with your score at the end. Run it a second time without changing anything. Any results that differ between the two runs are noise.
2. **Change one thing.** Ask Claude: `Read my reviewer's errors and suggest one change.` Before you rerun, predict which PRs it will fix. Then run `./lab eval --note "what I changed"`. Repeat while you have time. Your scores are saved in `my-work/notes.md`.
3. **When you're happy with your reviewer, run it against the holdout:** `./lab holdout`. Check whether it clears your bar, and read any errors.

**Done when** you've run the holdout.

**Short of time?** `./lab catch-up improve` gives you a tuned reviewer. Compare it with yours, then run the holdout.

## Chunk 6: Add a human gate and close the loop (15 min)

The last piece is a gate that decides what happens to each PR after its review. It can go back to Claude to fix, go to a person, or merge. Claude will build it. Your job is to decide which PRs go to a person, and when.

![What your human gate does](assets/human-gate.svg)

Anything the gate lets through merges without a person seeing it, but if most PRs end up in the queue you haven't saved anyone time.

### What the dev team wants a human to review

The full brief is in `docs/human-review.md`. We've decided H1 to H4 for you. For H4, Claude updates your reviewer so it can add an `ask_human` field to its answer when it's unsure. You decide how to handle H5 and H6.

| | A person should see | Spotted by |
|---|---|---|
| H1 | Changes to `service/records.py` or `service/models.py`, which hold customer data | code |
| H2 | Anything over 50 added lines | code |
| H3 | Anything whose review crashed, timed out or gave no verdict | code |
| H4 | Anything the reviewer wasn't sure about | reviewer |
| H5 | A PR whose description, comments or code try to steer its reviewer (prompt injection) | ? |
| H6 | Changes to how customer messages are sent, queued or retried | ? |

### Your decisions

- **What spots H5 and H6?** You can use more than one of these for each:
  - **Code in the gate,** such as a list of files or phrases. It's fast and predictable, but it only matches what you listed.
  - **Your reviewer,** using the same `ask_human` field.
  - **A specialist agent** that only decides whether a person should look. It can work out what a change does, but costs another model call per PR.
- **Claude first, or a person first?** Say a PR changes how messages are sent, and your reviewer has also found a bug in it. Should a person see it now, or after Claude has fixed the bug? What about a PR that tried to steer the reviewer?
- **When does the loop stop?** If the reviewer keeps rejecting Claude's fixes, how many tries does Claude get before a person steps in?

**Start:** `./lab next`

**Your file:** `my-work/5-human-gate.md`, which Claude fills in with you

1. **Design and build your gate.** In Claude, run `/design-gate`. It asks you these questions, builds `scripts/gate.py` and any specialist you chose, and runs `./lab test-gate`. If your reviewer missed your bar on the holdout, it also asks whether those kinds of PR should go to a person.
2. **Run the whole system:** `./lab pipeline`. It runs your checks, reviewer and gate on the dev PRs, plus five new ones made to test your gate. It ends with three numbers: problem PRs that merged, PRs the team wanted a human to review that merged without one, and PRs a person had to read. Ideally the first two are zero and the third is small. Open `human-review-queue.md` and check whether each PR in it was worth a person's time.
3. **Close the loop:** `./lab loop pr-03`. A new Claude session gets your reviewer's findings, fixes the PR and resubmits it, until it merges or goes to a person. Then run `./lab loop pr-09` and read Claude's fix. Would you have approved it?

**Done when** `./lab test-gate` passes and you've run `./lab loop`.

**Short of time?** `./lab catch-up gate` gives you a working gate and specialist. Then run steps 2 and 3.

## Check you're done

Ask Claude: `Am I done with Part 2?`

## Extension: does a stronger model review better? (optional, about 15 min)

**Your file:** `my-work/extension-models.md`

Your reviewer has been running on Haiku. Answer the questions in your file, then try the same reviewer on a stronger model:

```bash
LAB_REVIEW_MODEL=sonnet ./lab eval --note "sonnet"
```

Compare misses, false alarms, noise between runs and cost. If your reviewer already scores well on Haiku, add `--agent data/plain-reviewer.md` to see whether a stronger model makes up for weaker instructions.

You can also compare models on R13, the interface design rule. The two `design` PRs add the same feature with different function signatures. They have no labels, so read the comments and decide which model's feedback you'd rather get:

```bash
./lab review design --out results-design-haiku.json
LAB_REVIEW_MODEL=opus ./lab review design --out results-design-opus.json
```
