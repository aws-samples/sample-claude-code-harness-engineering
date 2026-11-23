# Evals by hand: participant guide

**Time:** about 60 minutes. **You work alone.** No coding.

An eval is a test for an AI system: a set of cases, and a way to decide
whether each output is good enough. In this module the system under test is
an assistant that drafts customer-support replies for a made-up bike shop.
Its drafts are already written and sit in `data/`. Your job is to build the
test.

You will use two terminals, both opened in this folder (the folder that
contains this file):

- **Terminal A is Claude's.** You run `claude` in it and talk to Claude there.
- **Terminal B is yours.** You type the `python3 eval.py ...` commands there
  and answer its questions at the keyboard.

On Windows, type `python` wherever this guide says `python3`, and use
PowerShell or Command Prompt for Terminal B, not a Git Bash window (the tool
cannot see the keyboard there).

This guide is a Markdown file. If your editor shows it as plain text, the
asterisks (**) and backticks around words, and the lines of three backticks
around commands, are formatting. Do not type them: type only the command.

You also need a plain-text editor for two files, `data/policy.md` and
`rubric.md`. Any editor will do. In a cloud IDE, click the file. Or, in
Terminal B: on macOS, `open -e rubric.md` opens it in TextEdit; on Windows,
`notepad rubric.md` opens it in Notepad.

| Step | What you do | Where | Minutes |
| :- | :- | :- | :- |
| Set-up | Open two terminals, start the journal, start Claude | A and B | 5 |
| 1 | Read the policy | Editor | 3 |
| 2 | Label twelve replies by hand | B | 12 |
| 3 | Write your rubric by hand | Editor | 8 |
| 4 | Round 1: Claude grades, you compare and rule | A, then B | 8 |
| 5 | Edit the rubric and go again | Editor, A, B | 12 |
| 6 | Four unseen cases | B, then A, then B | 7 |
| 7 | Finish: re-check, two lines, your card | B | 5 |

## Set-up (5 minutes)

1. Open two terminals. In each one, move into this folder. For example,
   from the folder you were sent:

   ```
   cd eval-by-hand
   ```

   Starting in this folder matters. Claude Code loads this folder's settings
   only if you start it here.

2. **In Terminal B, type:**

   ```
   python3 eval.py start
   ```

   It asks for your name or initials, for your completion card.

3. **In Terminal A, type:**

   ```
   claude
   ```

   Claude Code may first ask whether you trust this folder. Choose the
   answer that trusts it. In our test run the highlighted answer was "No",
   so look before you press Enter, and use the arrow keys to move. You may
   also see a note that the folder pre-approves one
   permission, `Edit(/grader/**)`. That is expected: it lets Claude write
   its verdicts into the `grader` folder without asking you each time.

   Then type this to Claude:

   ```
   What is your part in this folder, and what is mine?
   ```

   You should get a short answer that matches the split above: Claude grades
   and explains; the labels, the rubric and the rulings are yours.

## Step 1: read the policy (3 minutes)

Open `data/policy.md` in your editor and read it. It is one page: the eight
rules the assistant's drafts are supposed to follow. Keep it open.

## Step 2: label twelve replies by hand (12 minutes)

**In Terminal B, type:**

```
python3 eval.py label
```

For each case you see what the customer wrote and what the assistant
drafted. Type `p` (pass) or `f` (fail), press Enter, then type one line
saying why, in your own words.

- There is no answer sheet. You are the standard. Some cases are meant to
  be hard to call.
- About a minute a case. Go with your judgement; you can change a label
  later, with a reason (type `python3 eval.py label C05`, with the case
  you mean).
- `q` saves and quits. The same command picks up where you stopped.

Why by hand, and why first: if you look at a grader's verdicts before you
have made up your own mind, you tend to agree with them.

## Step 3: write your rubric by hand (8 minutes)

Open `rubric.md` in your editor. Replace the starter text with your own
criteria: the things that make a reply pass or fail. Save the file.

- Four to seven criteria is plenty for a first go.
- The grader knows only what this file says. It has not read the policy
  unless your rubric tells it to, or says the same things itself.
- Write for a careful stranger. "Polite" is a word two people read
  differently. "Does not blame the customer" is easier to apply.

You can ask Claude for a second pair of eyes. **In Terminal A, type:**

```
Read rubric.md. Which words would two graders read differently? Don't rewrite it for me.
```

Claude cannot edit `rubric.md`. That is deliberate: the words are yours.

## Step 4: round 1 (8 minutes)

1. **In Terminal A, type:**

   ```
   /grade
   ```

   This runs the grading skill in `.claude/skills/grade/SKILL.md`. It starts
   a fresh helper that has not seen your conversation, reads your rubric and
   the twelve drafts, and writes `grader/verdicts.json`. In our test runs a
   line such as "Skill(grade)" showed while it worked. Wait until Claude says how many passed
   and failed, and what to type next. In our test runs this took under a
   minute; allow two. If Claude asks permission to write
   `grader/verdicts.json`, say yes.

2. **In Terminal B, type:**

   ```
   python3 eval.py compare
   ```

   You see how many cases you and the grader agree on, then each
   disagreement in turn: your label and reason, the grader's verdict and
   reason. For each one, decide where the problem is:

   - `r` the **rubric**: it is unclear, or it misses something. Type a note
     to yourself about what to change.
   - `m` **my label**: looking again, you have changed your mind. Say why.
   - `c` a **close call**: reasonable people would differ. Say why, and
     leave it.

This step is the heart of the module. Until you have looked, a disagreement
does not mean the grader is wrong, or that you are.

Stuck on one? Ask Claude in Terminal A, for example:
`Why did the grader pass C05? Quote the words in my rubric that decided it.`

## Step 5: edit the rubric and go again (12 minutes)

1. In your editor, change `rubric.md` using the notes you just wrote. Save.
2. **In Terminal A, type:** `/grade`
3. **In Terminal B, type:** `python3 eval.py compare`

Rule on the new disagreements. If you have time, do a third round. Things
to watch:

- Did a fix for one case break another?
- Is agreement going up because the rubric is clearer, or because it now
  lists the twelve cases one by one? The next step will tell you.

## Step 6: four unseen cases (7 minutes)

1. **In Terminal B, type:** `python3 eval.py holdout`. "Holdout" is the
   usual name for cases kept back for a final test. The command works once
   you have compared two rounds, each with a rubric you edited.
2. **In Terminal B, type:** `python3 eval.py label` and label the four new
   cases by hand.
3. Do not edit `rubric.md` now.
4. **In Terminal A, type:** `/grade-unseen`
5. **In Terminal B, type:** `python3 eval.py compare`

You get agreement on cases your rubric was never tuned on, and one question
to answer in a line.

## Step 7: finish (5 minutes)

**In Terminal B, type:**

```
python3 eval.py finish
```

You re-label three cases from memory, type two lines about what you learned,
and get your completion card. Show the card to the person next to you and
tell them about one disagreement you ruled on. To be asked about two of
your cases, picked at random, type:

```
python3 eval.py quiz
```

## If something goes wrong

| You see | Do this |
| :- | :- |
| `python3` is not found (the wording varies) | Type `python` in place of `python3`. |
| "only runs when a person types it in a terminal" | You, or Claude, ran the tool somewhere without a keyboard. Type it yourself in Terminal B. On Windows, use PowerShell or Command Prompt, not Git Bash. |
| "These verdicts are for the main cases" | In Terminal A, type `/grade-unseen` and wait for Claude to finish. |
| "There are no verdicts yet" | In Terminal A, type `/grade` and wait for Claude to finish. |
| "rubric.md was saved after the last grading" | You edited the rubric since Claude graded. In Terminal A, type the command the tool names (`/grade`, or `/grade-unseen` in step 6). |
| Claude asks permission to write `grader/verdicts.json` | Say yes. |
| "The verdict file is not right" | Copy the sentence the tool prints into Terminal A. |
| "rubric.md is still the starter text" | Do step 3 first. |
| Claude says it cannot run a command or edit a file | That is the set-up working. Type the command yourself in Terminal B. |
| Grey text appears in Claude's input box | It is a suggestion, not something you typed. Start typing and it goes away. |
| You are lost | In Terminal B, type `python3 eval.py status`. It says what comes next. |

## Why Claude cannot do this one for you

This folder's `.claude/settings.json` has permission rules set to stop Claude
running commands here, editing `rubric.md`, and reading or writing the
`work` folder where your journal lives. `CLAUDE.md` tells Claude the same
thing in words. The journal is sealed line by line, so a change to any
line in it shows up when anyone types `python3 eval.py verify`.

None of that is the real reason. The real reason is that the grader is only
as good as the labels it is checked against, and those have to come from
someone who is accountable for the result. Here, that is you.

## If you finish early

- Type `/grade` twice without changing the rubric, and compare after each.
  Do any verdicts flip? Which criterion is behind the flips?
- Take your vaguest criterion and rewrite it as something a stranger could
  check. Does agreement move?
- Ask Claude: `Which of the eight policy rules does my rubric not cover?`
  Decide for yourself whether that matters.
