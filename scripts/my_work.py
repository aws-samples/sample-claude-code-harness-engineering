"""Reads the participant's files in my-work/. Tolerant, because people type answers like "Yes." and "both: the check finds them"."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MY_WORK = ROOT / "my-work"
HOMES = {"check", "reviewer", "both", "neither"}


def todos_left(path: Path) -> int:
    """How many TODOs are left to answer. A `TODO` in backticks is the instructions talking about them."""
    return len(re.findall(r"(?<!`)\bTODO\b(?!`)", path.read_text())) if path.exists() else 0


def table_rows(path: Path, first_cell: str) -> list[list[str]]:
    """Cells of each table row whose first cell starts with the first_cell pattern."""
    rows = []
    for line in path.read_text().splitlines() if path.exists() else []:
        if line.startswith("|") and re.match(rf"\|\s*{first_cell}", line):
            rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    return rows


def first_word(cell: str) -> str:
    found = re.search(r"[a-z]+", cell.lower())
    return found.group(0) if found else ""


def sort_rows() -> list[tuple[str, str, str]]:
    """(rule, home, why) for each rule, whatever was typed."""
    rows = table_rows(MY_WORK / "1-rule-sort.md", r"R\d+")
    return [(row[0].split()[0], first_word(row[1]) if len(row) > 1 else "", " ".join(row[2:])) for row in rows]


def sorted_rules(*homes: str) -> dict[str, str]:
    """{rule: why} for the rules sorted into these homes."""
    return {rule: why for rule, home, why in sort_rows() if home in homes}


def unclear_homes() -> list[str]:
    """Rules whose home has been answered, but isn't one of the four."""
    return [rule for rule, home, _ in sort_rows() if home not in HOMES and home != "todo"]


def sort_finished() -> bool:
    rows = sort_rows()
    return bool(rows) and all(home != "todo" for _, home, _ in rows)


def unclear_labels() -> list[str]:
    """PRs with an answer that isn't readable as yes or no."""
    rows = table_rows(MY_WORK / "4-gold-labels.md", r"pr-\d+")
    return [row[0] for row in rows if row[0] not in my_labels() and len(row) > 1 and first_word(row[1]) not in {"todo", ""}]


def my_labels() -> dict[str, dict]:
    """Your labels, in the shape of the lead's: {pr: {needs_changes, rules, reason}}. Unfinished rows are left out."""
    labels = {}
    for row in table_rows(MY_WORK / "4-gold-labels.md", r"pr-\d+"):
        row = row + [""] * (4 - len(row))
        verdict = {"y": "yes", "n": "no"}.get(first_word(row[1]), first_word(row[1]))
        if verdict in {"yes", "no"} and not any("TODO" in cell for cell in row[2:]):
            rules = sorted({found.upper() for found in re.findall(r"\b[Rr]\d+\b", row[2])})
            labels[row[0]] = {"pr": row[0], "needs_changes": verdict, "rules": ";".join(rules), "reason": " ".join(row[3:])}
    return labels
