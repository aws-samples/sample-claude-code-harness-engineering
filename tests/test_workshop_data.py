"""Every PR that's open must really apply to the service."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PRS = sorted((ROOT / "data/review-prs").glob("*/*.diff"))


@pytest.mark.parametrize("pr", PRS, ids=lambda p: p.stem)
def test_pr_applies(pr: Path, tmp_path: Path):
    diff = pr.read_text().partition("\n\n")[2]
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["cp", "-r", str(ROOT / "appointment_reminders"), str(tmp_path)], check=True)
    done = subprocess.run(["git", "apply", "--check", "-"], cwd=tmp_path, input=diff, text=True, capture_output=True)
    assert done.returncode == 0, done.stderr
