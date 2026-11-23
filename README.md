# Two hands-on Claude Code modules: start here

This folder holds two modules. Each takes about an hour, and you work alone. You do not need to write any code.

| Module | Folder | What you do |
| :- | :- | :- |
| Evals by hand | `eval-by-hand` | You build a small test for an AI assistant: you label its draft replies by hand, write a rubric, let Claude grade with it, and rule on every disagreement. |
| Write a skill that drafts PRDs | `prd-skill` | You teach Claude Code how your team writes a product requirements document (PRD), by writing a skill by hand and improving it against your own rules. |

The modules do not depend on each other. Your facilitator will say which one to do, or which to do first.

## You need

- **Claude Code 2.1.218 or later**, signed in. To check, type `claude --version` in a terminal. To update, type `claude update`.
- **Python 3.9 or later.** To check, type `python3 --version` (on Windows, `python --version`). Nothing else needs installing.
- **Two terminal windows.**
- **A plain-text editor.** The editor in a code editor will do, and so will TextEdit on macOS or Notepad on Windows.

On Windows, use PowerShell or Command Prompt for the terminal you type your own commands in, not a Git Bash window.

## Set up

1. Put this folder anywhere you like. A path with spaces in it is fine.
2. Open two terminals, and in each one move into the folder of the module you are doing, for example `cd eval-by-hand`. Go into the module's own folder, not only into this one: Claude Code loads a module's settings only when you start it inside that module's folder.
3. Open the module's `GUIDE.md` and follow it from the top. It tells you what to type, and in which terminal.

Each module folder has a hidden folder inside it called `.claude`. It is part of the module, so leave it where it is.

Every company, product and person in the modules is made up.
