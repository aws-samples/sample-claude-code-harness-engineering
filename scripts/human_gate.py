#!/usr/bin/env python3
"""Decides where a reviewed PR goes. Build this with Claude, from my-work/6-human-gate.md.

The agent can ask for a person with its alert_human tool, but a request is only a request: this code decides.
Think about what the agent can't be trusted to do for itself.
"""
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


@dataclass
class Review:
    verdict: str | None  # "approve", "request_changes", or None if the agent failed
    findings: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)  # what the agent sent to alert_human: {"reason", "summary"}
    error: str = ""  # why the agent failed, if it did


def load_pr(path: Path) -> Pr:
    text = path.read_text()
    title = re.search(r"^PR #\d+: (.*)$", text, re.MULTILINE)
    description = re.search(r"^Description: (.*)$", text, re.MULTILINE)
    added = [line for line in text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    return Pr(path.stem, title.group(1) if title else "", description.group(1) if description else "",
              sorted(set(re.findall(r"^(?:\+\+\+ b|--- a)/(.*)$", text, re.MULTILINE))), len(added), text)


def route(pr: Pr, review: Review) -> tuple[str, str]:
    """Return where the PR goes, "merge", "author" or "human", and why."""
    # TODO: this is the naive version. Replace it with the gate you designed.
    if review.verdict == "request_changes":
        return "author", "the agent asked for changes"
    return "merge", "the agent approved"
