"""Reads the participant's files in my-work/."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MY_WORK = ROOT / "my-work"


def todos_left(path: Path) -> int:
    """How many TODOs are left to answer. A `TODO` in backticks is the instructions talking about them."""
    return len(re.findall(r"(?<!`)\bTODO\b(?!`)", path.read_text())) if path.exists() else 0
