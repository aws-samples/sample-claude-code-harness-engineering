"""What the gate gets for each PR: the PR itself, and what the reviewer said. You don't need to change this file."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Pr:
    name: str
    title: str
    description: str
    paths: list[str]
    lines_added: int
    diff: str
    fixes: int = 0  # how many times Claude has already fixed this PR


@dataclass
class Review:
    verdict: str | None  # "approve", "request_changes", or None if the review failed
    findings: list[dict] = field(default_factory=list)
    ask_human: str = ""  # why the reviewer wants a person, if it added ask_human to its answer
    error: str = ""  # why the review failed, if it did
    specialist: dict | None = None  # the specialist's answer, if you have one: {"needs_human": True, False or None if it failed, "preference", "reason"}


def load_pr(path: Path) -> Pr:
    text = path.read_text()
    title = re.search(r"^PR #\d+: (.*)$", text, re.MULTILINE)
    description = re.search(r"^Description: (.*)$", text, re.MULTILINE)
    added = [line for line in text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    return Pr(path.stem, title.group(1) if title else "", description.group(1) if description else "",
              sorted(set(re.findall(r"^(?:\+\+\+ b|--- a)/(.*)$", text, re.MULTILINE))), len(added), text)
