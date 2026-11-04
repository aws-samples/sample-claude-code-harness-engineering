#!/usr/bin/env python3
"""Run your reviewer agent over a set of PRs and write what it said.

  ./lab review dev   is the usual way in. Directly:
  python3 scripts/run_reviewer.py --set dev [--only pr-01,pr-05] [--out results.json] [--agent FILE] [--runs 3]

Every call is a fresh headless Claude Code session with only the agent file as its system prompt, so nothing
in this session can leak into the answer. The agent's `tools:` line decides what else it can use: with none
it sees only the PR, and with Read, Grep, Glob it can also look through a copy of the code.
The agent must end its reply with one JSON object:
  {"verdict": "approve" | "request_changes", "findings": [{"rule": "R5", "why": "..."}]}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # paths are repo-relative wherever this is run from

AGENT = Path("my-work/3-reviewer-agent.md")
MODEL_ALIASES = ("haiku", "sonnet", "opus", "fable")
MODEL_ID = re.compile(r"claude-[a-z0-9][a-z0-9.-]{0,62}")  # e.g. claude-sonnet-5-5
READ_TOOLS = ("Read", "Grep", "Glob")  # the lab's two modes: no tools, or these
ALERT_TOOL = "mcp__gate__alert_human"
TIMEOUT_SECONDS = 180
STARTER = "TODO: don't write this by hand"


def pick_model(requested: str) -> str:
    """LAB_REVIEW_MODEL, checked against model names. It reaches claude through a settings file, never the command line."""
    for alias in MODEL_ALIASES:
        if requested == alias:
            return alias
    if MODEL_ID.fullmatch(requested):
        return requested
    raise SystemExit(f"LAB_REVIEW_MODEL={requested!r} isn't a model name. Use one of {', '.join(MODEL_ALIASES)}, or a full id like claude-sonnet-5-5.")


MODEL = pick_model(os.environ.get("LAB_REVIEW_MODEL", "haiku"))


def system_prompt(agent: Path) -> str:
    text = agent.read_text()
    return text.split("---", 2)[2].strip() if text.startswith("---") else text


def agent_tools(agent: Path) -> str:
    """The `tools:` line of the agent's frontmatter: blank means it sees the PR and nothing else,
    and "Read, Grep, Glob" lets it look through a copy of the code. Those are the only two the lab runs."""
    text = agent.read_text()
    found = re.search(r"^tools:[ \t]*(.*)$", text.split("---")[1] if text.startswith("---") else "", re.MULTILINE)
    names = {name.strip() for name in (found.group(1) if found else "").split(",") if name.strip()}
    if not names:
        return ""
    if names == set(READ_TOOLS):
        return ",".join(READ_TOOLS)
    raise SystemExit(f"The tools: line in {agent} should be blank, or Read, Grep, Glob. It has: {', '.join(sorted(names))}")


def code_copy() -> str:
    """A copy of the code alone, so an agent with tools can't read the labels or other PRs."""
    copy = tempfile.mkdtemp(prefix="review-code-")
    shutil.copytree("appointment_reminders", f"{copy}/appointment_reminders", ignore=shutil.ignore_patterns("__pycache__"))
    return copy


def last_verdict(text: str) -> dict:
    """The last JSON object in the reply with a verdict. Quoted code in the prose can hold braces too."""
    decoder = json.JSONDecoder()
    for start in reversed([match.start() for match in re.finditer(r"\{", text)]):
        try:
            found = decoder.raw_decode(text[start:])[0]
        except ValueError:
            continue
        if isinstance(found, dict) and "verdict" in found:
            return found
    raise ValueError("no JSON object with a verdict")


def show(name: str, answer: dict) -> None:
    """One review, with every field the agent reported, whatever shape you designed."""
    extras = {key: value for key, value in answer.items() if key not in ("verdict", "findings", "cost", "error")}
    print(f"{name}  {answer['verdict'] or 'FAILED: ' + answer.get('error', '')}{'  ' + json.dumps(extras) if extras else ''}")
    for finding in answer["findings"]:
        more = " ".join(f"{key}={value}" for key, value in finding.items() if key not in ("rule", "why"))
        print(f"    {finding.get('rule')}{' ' + more if more else ''}: {finding.get('why', '')}")


def review(diff: str, system: str, tools: str, cwd: str, alert_log: str | None = None) -> dict:
    """Return the agent's verdict, or {"verdict": None, ...} when the call or its JSON failed.

    The claude command line is fixed text. Everything that changes goes in files instead: the system prompt, a
    settings file with the model and the tools it may use, and the MCP config. The diff goes in on stdin. So no
    PR, agent file or environment variable can add an option to the command. Each call gets its own folder:
    the agent works in code/, a copy of the code, and its config sits beside that in config/.
    """
    if shutil.which("claude") is None:
        return {"verdict": None, "findings": [], "error": "can't find the claude CLI on your PATH"}
    allowed = [*tools.split(",")] if tools else []
    servers: dict = {}
    if alert_log:  # the human gate's tool: the agent can ask for a person, and the request lands in alert_log
        servers["gate"] = {"command": sys.executable, "args": [str(ROOT / "scripts/alert_human_server.py")], "env": {"ALERT_LOG": alert_log}}
        allowed.append(ALERT_TOOL)
    with tempfile.TemporaryDirectory(prefix="review-call-") as call:
        work, config = Path(call, "code"), Path(call, "config")
        shutil.copytree(cwd, work)
        config.mkdir()
        (config / "system.md").write_text(system)
        (config / "settings.json").write_text(json.dumps({"model": MODEL, "permissions": {"allow": allowed}}))
        (config / "mcp.json").write_text(json.dumps({"mcpServers": servers}))
        try:
            if tools:
                done = subprocess.run(
                    ["claude", "-p", "--tools=Read,Grep,Glob", "--output-format=json", "--system-prompt-file=../config/system.md",
                     "--settings=../config/settings.json", "--mcp-config=../config/mcp.json", "--strict-mcp-config",
                     "--setting-sources=", "--no-session-persistence"],
                    input=diff, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=True, cwd=work)
            else:
                done = subprocess.run(
                    ["claude", "-p", "--tools=", "--output-format=json", "--system-prompt-file=../config/system.md",
                     "--settings=../config/settings.json", "--mcp-config=../config/mcp.json", "--strict-mcp-config",
                     "--setting-sources=", "--no-session-persistence"],
                    input=diff, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=True, cwd=work)
            reply = json.loads(done.stdout)
            answer = last_verdict(reply["result"] or "")
            if answer["verdict"] not in ("approve", "request_changes"):
                raise ValueError(answer["verdict"])
            findings = [f if isinstance(f, dict) else {"rule": "", "why": str(f)} for f in answer.get("findings") or []]
            return {**answer, "findings": findings, "cost": reply.get("total_cost_usd", 0)}  # keeps any fields you added
        except subprocess.CalledProcessError as exc:
            return {"verdict": None, "findings": [], "error": f"claude failed: {(exc.stderr or exc.stdout or '').strip()[:200]}"}
        except subprocess.TimeoutExpired:
            return {"verdict": None, "findings": [], "error": f"no answer after {TIMEOUT_SECONDS} seconds"}
        except (ValueError, KeyError, TypeError, IndexError, AttributeError, OSError) as exc:
            return {"verdict": None, "findings": [], "error": f"couldn't read the reply: {str(exc)[:120]}"}


def blocked(pr_set: str, chunk: str) -> str | None:
    """Why this set is still closed. One command opens it: these only stop you spoiling your own measurement by accident."""
    if pr_set in ("dev", "design") and chunk in ("sort", "checks", "reviewer", "label"):
        return "Hold on: running the agent on these before you've labeled them lets its answers steer yours. To go ahead anyway: ./lab goto eval"
    if pr_set == "holdout" and chunk and chunk not in ("holdout", "gate"):
        return "Hold on: these are your fair test, so the agent gets frozen first. When you're ready: ./lab goto holdout"
    return None


def pr_paths(pr_set: str, only: str) -> list[Path]:
    paths = sorted(Path("data/review-prs", pr_set).glob("*.diff"))
    if only:
        return [p for p in paths if p.stem in only.split(",")]
    return [p for p in paths if p.stem != "debate"]


def check_agent(agent: Path) -> None:
    if not agent.exists() or STARTER in agent.read_text():
        raise SystemExit(f"{agent} isn't written yet. In Claude, run /interview-reviewer, or take ours with ./lab catch-up reviewer.")


def chunk_now() -> str:
    stage = Path(".claude/lab-stage")
    return stage.read_text().strip() if stage.exists() else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=["try", "dev", "design", "holdout"], default="dev")
    parser.add_argument("--runs", type=int, default=1, help="review each PR this many times, to see how much answers vary")
    parser.add_argument("--only", default="", help="comma-separated PR names")
    parser.add_argument("--out", default="results.json")
    parser.add_argument("--agent", default=str(AGENT), help="agent file, if you want to try another one")
    args = parser.parse_args()
    reason = blocked(args.set, chunk_now())
    if reason:
        raise SystemExit(reason)
    agent = Path(args.agent)
    check_agent(agent)
    paths = pr_paths(args.set, args.only)
    if not paths:
        raise SystemExit(f"No PRs here for {args.set} {args.only}. If this set isn't open yet: ./lab goto {'holdout' if args.set == 'holdout' else 'eval'}")
    runs = f", {args.runs} times each" if args.runs > 1 else ""
    print(f"Reviewing {len(paths)} PR{'s' if len(paths) != 1 else ''}{runs}. Each is a fresh Claude call, so this can take a minute.", flush=True)
    system, tools, code = system_prompt(agent), agent_tools(agent), code_copy()
    jobs = [path for path in paths for _ in range(args.runs)]
    with ThreadPoolExecutor(max_workers=5) as pool:
        answers = list(pool.map(lambda p: review(p.read_text(), system, tools, code), jobs))
    shutil.rmtree(code, ignore_errors=True)
    if all(a["verdict"] is None for a in answers):
        print(f"Every call failed, so {args.out} is unchanged. The first error: {answers[0].get('error', '') if answers else ''}")
        return 1
    if args.runs > 1:
        results = {path.stem: [a for job, a in zip(jobs, answers) if job == path] for path in paths}
        for name, reviews in results.items():
            for number, answer in enumerate(reviews, 1):
                show(f"{name} run {number}", answer)
    else:
        results = {p.stem: a for p, a in zip(paths, answers)}
        for name, answer in results.items():
            show(name, answer)
    out = Path(args.out)
    merged = {**(json.loads(out.read_text()) if args.only and out.exists() else {}), **results}  # --only updates, it doesn't wipe
    out.write_text(json.dumps(merged, indent=2))
    failed = sum(1 for a in answers if a["verdict"] is None)
    if failed:
        print(f"WARNING: {failed} calls failed. If it says it couldn't read the reply, check that your agent still ends with the JSON object. Otherwise rerun, and tell your facilitator if it keeps happening.")
    print(f"cost ${sum(a.get('cost', 0) for a in answers):.3f} for {len(answers)} reviews, tools: {tools or 'none'}")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
