# Part 2: Can you trust your reviewer?

Deterministic checks either work or they don't. Your reviewer agent makes judgments on subjective criteria, so you should think about how to measure its quality with an eval.

**45 minutes, three chunks of 15.** This carries straight on from Part 1, with the agent you built there. If you need any help, ask Claude.

## Chunk 4: Label five PRs and design the eval (15 min)

Decide the right answer for a few PRs, and design how you'll measure your reviewer against answers like these.

**Start:** `./lab next`

**Your files:** `my-work/4-gold-labels.md` and `my-work/5-eval-design.md`

1. **Label five PRs (6 min).** Decide the right answer before the agent runs. Five is far too few to prove anything, and that's fine: this is to feel what you're asking of the agent. The team lead has labeled the other eleven, and the eval uses those automatically, so it still has sixteen. You can use Claude to help with this, since you aren't familiar with the codebase: in Claude, `/explain-pr pr-01` shows you what a PR changes and the code around it, without a verdict.
2. **Judge two design PRs (2 min).** `design-1` and `design-2` are about R13, so that's the question here. Judge them your own way, and compare with a neighbor.
3. **Design the eval (7 min).** Answer the questions in `5-eval-design.md` to help guide a good design.

**Done when** there are no TODOs left in either file.

**Worth a thought:** Claude helped you read those PRs. Does that matter for what your gold labels can prove?

## Chunk 5: Build the eval and improve the agent (15 min)

Build the eval, use it to improve your reviewer, and finish with one fair test on PRs it hasn't seen.

**Start:** `./lab next`

**Your file:** `my-work/3-reviewer-agent.md`, and Claude builds `scripts/eval_reviewer.py`

1. **Run the agent on all sixteen labeled PRs,** your five and the lead's eleven: `./lab review dev`. It takes about a minute.
2. **Build the scorer with Claude.** The file already loads the labels and shows where you and the lead differ:
   ```
   Read my-work/5-eval-design.md and build score() in scripts/eval_reviewer.py. Then run ./lab score --results data/eval-fixtures/always-approves.json, and the same with flags-everything.json, and show me that neither looks good.
   ```
3. **Get your baseline:** `./lab score`. Write it in `my-work/notes.md`. A perfect score first time is a reason to check your scorer and your labels.
4. **Improve the agent.** Let Claude read the misses, change the agent and rerun. Your job is to stay honest:
   - **Read every change.** A line naming a specific PR is a cheat sheet, not a fix.
   - **Run it twice.** Answers vary. Is that change signal or noise?
   - **Ask what the agent can't see.** If it missed what you caught, how did you catch it?
   - **Is the label wrong?** Sometimes the agent is right, and you get to change your mind.
5. **Try it on R13 (3 min).** `./lab review design` runs your agent three times on each design PR. There's no answer key, so ask: is it consistent? Does it treat the two PRs differently? Did your way of reporting R13 help? Change it and rerun if not.
6. **Final 3 minutes, the fair test.** Eight PRs have been hidden from everyone. Did it learn the rules, or just these sixteen? `./lab next` comes first, because it freezes your agent. Changing the agent after you've seen these PRs would spoil the test.
   ```bash
   ./lab next
   ./lab review holdout
   ./lab score holdout
   ```
   Eight is too few for a percentage, so read each error rather than the number. A clean run on eight small PRs isn't proof.

**Done when** you can name the change that moved the score most, and you've read any held-out errors. If there are none, ask what these eight have in common that real PRs don't.

**Short of time?** `./lab catch-up eval` gives you a scorer. Spend the time on the agent.

## Chunk 6: Add a human gate (15 min)

Decide when a person still needs to look at a PR, and build that into the pipeline.

**Start:** `./lab next`

**Your file:** `my-work/6-human-gate.md`

1. **Read `data/review-prs/holdout/pr-45.diff`, and what your agent said about it.** Suppose a PR did talk your agent out of raising an alarm. What does that mean for who should decide?
2. **Answer the questions in your file.** When should a person look? How would you assess that? Who gets it?
3. **Build it with Claude.** There are two pieces. `alert_human(reason, summary)` is a tool your agent can call. It alerts nobody, since we aren't live. `scripts/human_gate.py` then decides where each PR goes: `merge`, `author` or `human`.
   ```
   Read my-work/6-human-gate.md. Build it: tell my agent when to call alert_human, and replace route() in scripts/human_gate.py. Get ./lab test-gate passing.
   ```
4. **Run the whole system:** `./lab pipeline`. Anything routed to a person lands in `human-review-queue.md`. Would you know what to do from what's in there? Is the number of PRs right?

**Done when** `./lab test-gate` passes and you've read the queue.

**Short of time?** `./lab catch-up gate` gives you a gate that passes. Read it, and argue with one of its conditions.

## Check you're done

`./lab verify 2`, then `./lab off`.

## Extension: does a stronger model review better? (optional, about 15 min)

**Your file:** `my-work/extension-models.md`

Your reviewer has been running on Haiku. Answer the questions in your file, then ask Claude to help you run and compare the models, with the same agent on the same PRs. Any model runs like this:

```bash
LAB_REVIEW_MODEL=sonnet ./lab review dev --out results-sonnet.json
./lab score --results results-sonnet.json
LAB_REVIEW_MODEL=opus ./lab review design --out results-design-opus.json
```

**Things you could look at:**

- What it catches, and its false alarms
- How much its answers change between runs
- How it handles R13, on the design PRs
- Whether you'd want its comments on your own PR
- What it costs and how long it takes: each review prints a cost estimate

