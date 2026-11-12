# 5. When does a person look?

Replace each `TODO` with your answer, or tell Claude your choices and have it write them in. H1 to H3 are already decided, as code.

The lead's preferences are in `docs/human-review.md`. For each one, decide what checks it: code in the gate (`scripts/gate.py`), or an agent. If it's an agent, say which: your reviewer, by calling `alert_human`, or a specialist agent of its own (`my-work/6-gate-agent.md`).

| Preference | Who checks it | Why |
|---|---|---|
| H1 Customer records or personal data | code | The files that handle customer records are known, so a check on the paths is certain and cheap |
| H2 Over 50 added lines | code | It's a count |
| H3 Checks that didn't finish | code | An agent that crashed can't report it, so the gate has to notice |
| H4 The reviewer wasn't sure | TODO | TODO |
| H5 A PR that tries to steer its reviewer | TODO | TODO |
| H6 Retries, queueing or sending | TODO | TODO |
