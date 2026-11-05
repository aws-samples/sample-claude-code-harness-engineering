"""Reads the participant's files in my-work/. Tolerant, because people answer in their own words."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MY_WORK = ROOT / "my-work"
LABELS = MY_WORK / "4-gold-labels.md"
YES = {"needs", "need", "changes", "change", "request", "block", "reject", "fail", "flag"}
NO = {"approve", "approved", "ok", "okay", "fine", "clean", "pass", "merge", "lgtm", "good"}
NEGATION = re.compile(r"\b(not|no|don't|doesn't|dont|doesnt|shouldn't|shouldnt|isn't|isnt|never|nothing|without)\b|n't\b")


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


def _verdict(cell: str) -> str | None:
    """yes or no from an answer such as "Yes.", "needs changes" or "approve". None when it's unclear, as with "doesn't need changes"."""
    text = cell.lower().replace("\u2019", "'")
    words = re.findall(r"[a-z]+", text)
    if not words or words[0] == "todo":
        return None
    if words[0] in ("yes", "y"):
        return "yes"
    if words[0] in ("no", "n"):
        return "no"
    if NEGATION.search(text):
        return None  # "doesn't need changes", "don't approve": too easy to read backwards
    said = set(words)
    if said & YES and not said & NO:
        return "yes"
    if said & NO and not said & YES:
        return "no"
    return None


def _label_rows() -> list[list[str]]:
    return [row + [""] * (4 - len(row)) for row in table_rows(LABELS, r"pr-\d+")]


def my_labels() -> dict[str, dict]:
    """Your labels, in the shape of the lead's: {pr: {needs_changes, rules, reason}}. Rows you haven't answered are left out."""
    labels = {}
    for row in _label_rows():
        verdict = _verdict(row[1])
        rules = sorted({found.upper() for found in re.findall(r"\b[Rr]\d+\b", f"{row[1]} {row[2]}")})
        if verdict and not (verdict == "yes" and not rules and "TODO" in row[2]):  # a yes with its rule still TODO isn't finished
            labels[row[0]] = {"pr": row[0], "needs_changes": verdict, "rules": ";".join(rules), "reason": " ".join(row[3:]).replace("TODO", "").strip()}
    return labels


def unclear_labels() -> dict[str, str]:
    """{pr: what they wrote} for answers that can't be read as yes or no."""
    return {row[0]: row[1] for row in _label_rows() if row[1] and _verdict(row[1]) is None and not row[1].upper().startswith("TODO")}


def describe_labels() -> str:
    """What the scorer will use from your labels, so that a misread shows up straight away."""
    read = [f"{pr} {label['needs_changes']}{' ' + label['rules'].replace(';', ',') if label['rules'] else ''}" for pr, label in my_labels().items()]
    lines = [f"Your labels, as the scorer reads them: {'; '.join(read)}" if read else "No labels read from my-work/4-gold-labels.md yet, so the scorer uses the lead's."]
    lines += [f"Couldn't read {cell!r} for {pr} as yes or no, so the lead's label is used." for pr, cell in unclear_labels().items()]
    return "\n".join(lines)
