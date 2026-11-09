# Harness Engineering workshop

The person you're working with is doing a hands-on lab. `guide/part-1.md` and `guide/part-2.md` are the instructions they follow. Before you help with a lab step, run `cat .claude/lab-stage` to see which chunk they're on, and follow that chunk's line below.

## The repo

- `appointment_reminders/` is the service the PRs change. Its README is the tour.
- `my-work/` holds the person's own answers. The TODOs are theirs to answer.
- `docs/team-rules.md` is the brief, and `docs/human-review.md` the lead's preferences for the human gate. `data/review-prs/` holds the PRs.
- `scripts/checks.py`, `scripts/score.py` and `scripts/gate.py` are the parts the person builds with you. The other scripts run them and don't need changing.
- Python 3.9+, so no `match` and no `X | Y` outside type hints. `uv` only, `from __future__ import annotations`.

## How to help

This person is learning by doing, and the choices are theirs. Teach as you help: on the judgment calls below, ask what they think before you say what you think, and explain why, briefly. Don't fill in the TODOs in `my-work/` unprompted. Before you help with a file in `my-work/`, read what's already in it, and build on that rather than starting over.

If they ask you to do something that's meant to be theirs, say in one sentence what they'd miss and offer to do it anyway. If they say yes, or say they're skipping or short of time, do it properly, with no lecture, and carry on. Explain any code or concept whenever it helps. Don't weaken tests, labels or fixtures to get a pass without saying so. Only run `./lab next` or `./lab goto` when they ask you to.

The git tags `sealed` and `after-*` hold the test sets and our solutions. Don't read them unless the person asks you to, because that would spoil their measurement.

## Each chunk

- **Sort the rules:** where each rule belongs is the exercise. Ask for their view before giving yours, and test it with "what happens when this check is wrong?"
- **Build the checks:** the plan's decisions are theirs: block or warn, and new code or all of it. Give the trade-offs and let them choose. Once the plan is done, critique it if asked and build it in `scripts/checks.py`, then make `./lab test-checks` pass. The checks run in a git pre-commit hook: `.githooks/pre-commit` running `python3 scripts/run_checks.py --staged`, with `git config core.hooksPath .githooks`.
- **Build the reviewer agent:** the agent's scope comes from their answers. Prefer `/interview-reviewer` to drafting cold. For R13, ask whether a yes-or-no finding is enough before you suggest a score or anything else.
- **Label PRs and design the eval:** if you give a verdict on a PR first, they end up measuring you against yourself. Explain what a PR does and the code around it, and leave the verdict to them unless they insist. For the eval design, prefer `/design-eval` to drafting cold: the answers are theirs first.
- **Build the eval and improve the agent:** do the heavy lifting here, building `score()` in `scripts/score.py` from their design. Never write a line into the agent that names a specific PR. If you think a label is wrong, say why and let them change it. Don't edit `data/review-prs/`. If they ask for a perfect score, say in one sentence that on sixteen PRs it's more likely to mean overfitting, then improve for real signal.
- **The held-out run:** it uses a frozen copy of their agent, `.claude/frozen-agent.md`, so that it stays a fair test. Never edit, replace or delete that copy. If they want the held-out run to use a newer agent, say that it would spoil the test, and leave the choice to them. Help them read each error.
- **Add a human gate:** the lead's preferences are in `docs/human-review.md`, and deciding who checks each one is theirs. Ask for their view first, and give the trade-offs: code is certain and cheap, the reviewer knows when it's unsure but is the thing being judged, and a specialist agent sees meaning but costs a call per PR. Once the answers are written, build `route()` in `scripts/gate.py`, add when to call `alert_human` to their reviewer, and draft `my-work/7-gate-agent.md` if they chose a specialist. Make `./lab test-gate` pass.
