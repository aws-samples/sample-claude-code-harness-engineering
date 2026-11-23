# Write a skill that drafts PRDs: participant guide

About 60 minutes. You work alone, at your own pace. The times in each heading are a guide, not a test.

## What you will do

You will teach Claude Code how **your** team writes a product requirements document (PRD). A *skill* is a file of instructions called `SKILL.md`. Claude Code uses a skill when it is relevant, or when you type its name as a command.

You will:

1. get a first PRD draft from Claude with no help, and see what it gets wrong for your team;
2. write down your team's house rules;
3. write a skill by hand that carries those rules;
4. review each new draft against your rules, and change the skill until the drafts follow them.

## Why Claude cannot do this for you

The rules are your team's, and you are the reviewer. Nobody else in the room has your answers.

This folder is also set up so that Claude **cannot** edit your skill file, see your rules or your reviews, or run commands. If you ask it to finish the exercise for you, it should tell you it can't, and tell you what to type next. That is deliberate.

## Before you start

You need Claude Code, Python 3.9 or later, and a text editor.

You will type in three places. The guide marks each line with where it goes:

| Mark | Where | What it is for |
| :- | :- | :- |
| **A>** | Terminal A, running Claude Code | Asking Claude for drafts |
| **B>** | Terminal B, a plain terminal in this folder | Your own commands: rules and reviews |
| **Editor** | Your text editor | Reading briefs and drafts, writing the skill |

If your editor shows this guide as plain text, the asterisks (**) and backticks around words are formatting. Do not type them: after **B>** `python3 prd.py start`, you type only python3 prd.py start.

On Windows, type `python` wherever this guide says `python3`, and use PowerShell or Command Prompt for Terminal B, not a Git Bash window. In Git Bash the `prd.py` commands cannot tell that a person is typing, and refuse to run.

---

## Step 0: set up (5 minutes, 0:00 to 0:05)

1. Open two terminals. In each one, go to this folder, the one that holds `GUIDE.md`, for example with `cd prd-skill`.

2. In Terminal B, start your journal and type your name when asked:

   **B>** `python3 prd.py start`

3. In Terminal A, start Claude Code:

   **A>** `claude`

   Start it in this folder, not in a folder above it. The settings for this exercise only load when Claude Code starts here. If Claude Code asks whether you trust this folder, choose the answer that trusts it. In a test run of a folder like this one the highlighted answer was "No", so look before you press Enter, and use the arrow keys to move. A note that the folder pre-approves a permission is expected. It lets Claude save drafts without asking you each time.

## Step 1: a draft with no help (8 minutes, 0:05 to 0:13)

4. **Editor:** open `briefs/brief-1.md` and read it. It is a page of messy notes about a made-up product. Notice what the notes do *not* say.

5. Ask Claude for a PRD. Type this in Terminal A, exactly:

   **A>** `Draft a PRD from briefs/brief-1.md and save it as drafts/baseline.md`

6. **Editor:** when Claude has finished, open `drafts/baseline.md` and read it. Would the person who reads PRDs on your team accept it? Do not fix anything. Just notice what you would send back.

## Step 2: your house rules (10 minutes, 0:13 to 0:23)

7. Write down how your team wants a PRD written. Type:

   **B>** `python3 prd.py rules`

   It asks who reads your PRDs, then asks for 4 to 8 rules. Type each rule as one sentence that a reviewer could check by looking at a PRD and answering yes or no.

   The difference, shown on meeting notes rather than PRDs so the example does not write your rules for you:

   - Hard to check: *Notes should be short and useful.*
   - Easy to check: *Notes fit on one screen and begin with the decisions that were made.*

   Think of your own team. If you have no team rules to hand, think of the last document you sent back to someone, and why.

## Step 3: review the first draft (5 minutes, 0:23 to 0:28)

8. Check the first draft against your rules. Keep `drafts/baseline.md` open in your editor, and type:

   **B>** `python3 prd.py review drafts/baseline.md`

   It first asks which brief the draft came from (type `1` here). Then, for each rule, answer `y` (yes), `n` (no) or `p` (partly). When the answer is not yes, say in a few words what is wrong. At the end it asks whether anything else is wrong with the draft: press Enter for nothing, or say what, and you can then add it as a rule. You end with a score. That score is Claude knowing nothing about your team.

   If the draft already follows nearly all your rules, they are probably things any careful writer does. Add one or two that are peculiar to your team, such as a length, the names and order of sections, or who must be named. Type `python3 prd.py rules` again to add them, then the review command again: it asks about the added rules only, so that your first score counts every rule.

## Step 4: write your skill by hand (10 minutes, 0:28 to 0:38)

9. Create your skill file from the starter:

   **B>** `python3 prd.py skill`

10. **Editor:** open `.claude/skills/prd-draft/SKILL.md`. The `.claude` folder starts with a dot, so some file browsers hide it. If yours does, open it from Terminal B: on macOS `open -e .claude/skills/prd-draft/SKILL.md`, on Windows `notepad .claude\skills\prd-draft\SKILL.md`. In a code editor, use its "open file" box and type the path.

    Delete the comment line near the top, and replace every line marked `REPLACE` with your own words:

    - the **description** at the top, which tells Claude what the skill is for and when to use it;
    - who reads your PRDs;
    - your house rules, written as instructions to Claude;
    - what Claude should do when a brief leaves something out.

    Write as if you were briefing a new colleague. Save the file.

11. Check the file is well formed, and fix what it reports:

    **B>** `python3 prd.py check`

12. Optional, if you have a minute. Ask Claude to read the skill as a newcomer would. It can read the file, but it cannot change it:

    **A>** `Read .claude/skills/prd-draft/SKILL.md and tell me what a newcomer could read two ways. Questions only.`

    If its questions show you a gap, fix it yourself in the editor.

## Step 5: round 1, the same brief with your skill (8 minutes, 0:38 to 0:46)

13. Start a new conversation, so the first draft does not colour this one, and load your skill:

    **A>** `/clear`

    **A>** `/reload-skills`

14. Ask for the same PRD again, this time through your skill. The skill's folder name is the command:

    **A>** `/prd-draft briefs/brief-1.md and save it as drafts/round-1.md`

    If Claude Code does not know `/prd-draft`, type `/reload-skills` and try again.

15. **Editor:** open `drafts/round-1.md`. Then review it:

    **B>** `python3 prd.py review drafts/round-1.md`

    This time, for every rule the draft misses, you also say *why*: the skill did not say it, the skill said it unclearly, Claude missed a clear instruction, or the brief made it impossible. Compare the score with your baseline.

## Step 6: round 2, change the skill and try a new brief (9 minutes, 0:46 to 0:55)

16. **Editor:** open your skill file again. For each miss in round 1, change the skill so that the next draft will not make it. Add a sentence, sharpen one, or cut one that is causing trouble. Save, then:

    **B>** `python3 prd.py check`

17. Reload the changed skill and try it on a brief it has not seen. Always reload after you edit the skill, or Claude may draft from the old version:

    **A>** `/clear`

    **A>** `/reload-skills`

    **A>** `/prd-draft briefs/brief-2.md and save it as drafts/round-2.md`

18. **Editor:** read `briefs/brief-2.md` and `drafts/round-2.md`. Then review:

    **B>** `python3 prd.py review drafts/round-2.md`

    Did your changes carry over to a new brief, or did they only fix brief 1?

## Step 7: finish (5 minutes, 0:55 to 1:00)

19. If you want a third round (see "If you have time left"), do it before this step: after `finish`, the tool records no more reviews. Then close the exercise. It asks two short questions about what you learned, then prints your completion card:

    **B>** `python3 prd.py finish`

20. Show your card to a neighbour or the facilitator. Tell them about one rule that Claude only followed after you changed the skill. They can ask you about two of your own answers with:

    **B>** `python3 prd.py quiz`

---

## If you have time left

Do the third round before `finish` in step 19. The second item can be done at any time.

- **A third round.** Change the skill again, type `/reload-skills` in Terminal A, and try `briefs/brief-3.md`, which is about an internal tool. Save the draft as `drafts/round-3.md` and review it. Does a skill written for customer features still fit?
- **Does Claude pick the skill up by itself?** Claude decides whether to use a skill from its description. Type `/clear`, then ask without the command: `I need a PRD for briefs/brief-3.md, saved as drafts/auto.md`. If the draft ignores your rules, the description is the place to look.

## If something goes wrong

| What you see | What to do |
| :- | :- |
| `python3` is not found (the wording varies) | Try `python` instead, or `py -3` on Windows. |
| "…only runs when a person types it in a terminal…", with "This shell was started by Claude Code" or "This window is not a terminal…" | You ran a `prd.py` command through Claude, or in a window that is not a plain terminal. Type it yourself in Terminal B. On Windows, use PowerShell or Command Prompt, not Git Bash. |
| Claude says it is blocked, or cannot edit your skill | That is the exercise working. The step is yours. |
| Claude Code asks permission to save a draft | Say yes. Drafts go in the `drafts` folder. |
| `/prd-draft` is not recognised | Type `/reload-skills`. Check the file is at `.claude/skills/prd-draft/SKILL.md`. If it still fails, leave Claude Code with `/exit` and start it again in this folder. |
| "This draft is older than your last edit to the skill" | You changed the skill after the draft was written. Type `/reload-skills` in Terminal A, then ask Claude for a fresh draft under a new name, for example `drafts/round-1b.md`, then review that. |
| Grey text appears in Claude Code's input box after an answer | It is a suggestion. Start typing and it goes away. |
| "Your skill is word for word the same as in your last review" | A new round needs your own change to the skill first. |
| "The journal … does not check out" | Something other than `prd.py` changed the files in `work`. Delete the `work` folder and begin again with `python3 prd.py start`. |
| You want to see your rules again | **B>** `python3 prd.py rules list` |
| You are not sure where you are | **B>** `python3 prd.py status` |

## What to take away

- A skill is your team's knowledge, written down once so that you do not retype it in every conversation.
- You cannot tell whether a skill is good by reading it. You tell by reading what it produces, against rules you can check.
- When a draft misses a rule, ask which of four things happened: the skill did not say it, said it unclearly, was ignored, or the brief made it impossible. Each one has a different fix.
