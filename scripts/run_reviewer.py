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
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)  # paths are repo-relative wherever this is run from

AGENT = Path("my-work/3-reviewer-agent.md")
GATE_AGENT = Path("my-work/7-gate-agent.md")  # the specialist gate agent, if you chose one
FROZEN = Path(".claude/frozen-agent.md")  # ./lab next copies your agent here when the held-out run opens
MODEL_ALIASES = ("haiku", "sonnet", "opus", "fable")
MODEL_ID = re.compile(r"(?:[a-z]{2,6}\.)?(?:anthropic\.)?claude-[a-z0-9][a-z0-9.-]{0,62}(?::[0-9]{1,3})?")  # claude-sonnet-5-5, or Bedrock's global.anthropic.claude-sonnet-5-5
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
    raise SystemExit(f"LAB_REVIEW_MODEL={requested!r} isn't a model name. Use one of {', '.join(MODEL_ALIASES)}, or a full id like claude-sonnet-5-5 or a Bedrock id.")


MODEL = pick_model(os.environ.get("LAB_REVIEW_MODEL", "haiku"))


def settings_env() -> dict[str, str]:
    """The `env` blocks of Claude Code's settings files, merged in its order: yours, then the project's, then local, with later ones winning.

    The reviewer runs with no settings files of its own, so this is how a setup such as Bedrock reaches it.
    Only `env` carries over: no hooks, permissions or plugins."""
    user_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    merged: dict[str, str] = {}
    for path in (user_dir / "settings.json", ROOT / ".claude/settings.json", ROOT / ".claude/settings.local.json"):
        try:
            env = json.loads(path.read_text()).get("env") or {}
        except (OSError, ValueError, AttributeError):
            continue  # missing, unreadable or not a settings file: nothing to carry over
        if isinstance(env, dict):
            merged.update({str(key): str(value) for key, value in env.items()})
    return merged


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


def last_json(text: str, key: str = "verdict") -> dict:
    """The last JSON object in the reply with this key. Quoted code in the prose can hold braces too."""
    decoder = json.JSONDecoder()
    for start in reversed([match.start() for match in re.finditer(r"\{", text)]):
        try:
            found = decoder.raw_decode(text[start:])[0]
        except ValueError:
            continue
        if isinstance(found, dict) and key in found:
            return found
    raise ValueError(f"no JSON object with {key!r}")


def pr_summary(path: Path) -> str:
    """What the PR says it does, and where to read it."""
    lines = path.read_text().splitlines()
    title = lines[0].split(": ", 1)[-1] if lines else ""
    description = lines[1].removeprefix("Description: ") if len(lines) > 1 else ""
    return f"PR: {title}. {description} ({path})"


def show(name: str, answer: dict, path: Path | None = None) -> None:
    """One review, with every field the agent reported, whatever shape you designed."""
    extras = {key: value for key, value in answer.items() if key not in ("verdict", "findings", "cost", "error")}
    print(f"{name}  {answer['verdict'] or 'FAILED: ' + answer.get('error', '')}{'  ' + json.dumps(extras) if extras else ''}")
    if path:
        print(f"    {pr_summary(path)}")
    for finding in answer["findings"]:
        more = " ".join(f"{key}={value}" for key, value in finding.items() if key not in ("rule", "why"))
        print(f"    {finding.get('rule')}{' ' + more if more else ''}: {finding.get('why', '')}")


def run_claude(diff: str, system: str, tools: str, cwd: str, alert_log: str | None = None) -> dict:
    """One headless Claude call. Returns claude's JSON reply, or {"error": ...} when the call failed.

    The claude command line is fixed text. Everything that changes goes in files instead: the system prompt, a
    settings file with the model and the tools it may use, and the MCP config. The diff goes in on stdin. So no
    PR, agent file or environment variable can add an option to the command. Each call gets its own folder:
    the agent works in code/, a copy of the code, and its config sits beside that in config/.
    """
    if shutil.which("claude") is None:
        return {"error": "can't find the claude CLI on your PATH"}
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
        (config / "settings.json").write_text(json.dumps({"model": MODEL, "env": settings_env(), "permissions": {"allow": allowed}}))
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
            return json.loads(done.stdout)
        except subprocess.CalledProcessError as exc:
            return {"error": f"claude failed: {(exc.stderr or exc.stdout or '').strip()[:200]}"}
        except subprocess.TimeoutExpired:
            return {"error": f"no answer after {TIMEOUT_SECONDS} seconds"}
        except (ValueError, OSError) as exc:
            return {"error": f"couldn't read the reply: {str(exc)[:120]}"}



def review(diff: str, system: str, tools: str, cwd: str, alert_log: str | None = None) -> dict:
    """The reviewer's verdict, or {"verdict": None, ...} when the call or its JSON failed."""
    reply = run_claude(diff, system, tools, cwd, alert_log)
    if "error" in reply:
        return {"verdict": None, "findings": [], "error": reply["error"]}
    try:
        answer = last_json(reply["result"] or "", "verdict")
        if answer["verdict"] not in ("approve", "request_changes"):
            raise ValueError(answer["verdict"])
        findings = [f if isinstance(f, dict) else {"rule": "", "why": str(f)} for f in answer.get("findings") or []]
        return {**answer, "findings": findings, "cost": reply.get("total_cost_usd", 0)}  # keeps any fields you added
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        return {"verdict": None, "findings": [], "error": f"couldn't read the reply: {str(exc)[:120]}"}


def gate_check(diff: str, system: str, tools: str, cwd: str) -> dict:
    """The specialist gate agent's answer: {"needs_human": True or False, "reason"}, or needs_human None when it failed."""
    reply = run_claude(diff, system, tools, cwd)
    if "error" in reply:
        return {"needs_human": None, "reason": "", "error": reply["error"]}
    try:
        answer = last_json(reply["result"] or "", "needs_human")
        if not isinstance(answer["needs_human"], bool):
            raise ValueError(f"needs_human is {answer['needs_human']!r}, not true or false")
        return {"needs_human": answer["needs_human"], "reason": str(answer.get("reason", "")), "cost": reply.get("total_cost_usd", 0)}
    except (ValueError, KeyError, TypeError, IndexError, AttributeError) as exc:
        return {"needs_human": None, "reason": "", "error": f"couldn't read the reply: {str(exc)[:120]}"}


def written(agent: Path) -> bool:
    return agent.exists() and STARTER not in agent.read_text()


def blocked(pr_set: str, chunk: str) -> str | None:
    """Why this set is still closed. One command opens it: these only stop you spoiling your own measurement by accident."""
    if pr_set in ("dev", "design") and chunk in ("sort", "checks", "reviewer", "label"):
        return "Hold on: running the agent on these before you've labeled them lets its answers steer yours. To go ahead anyway: ./lab goto eval"
    if pr_set == "holdout" and not Path("data/review-prs/holdout").exists():
        return "Hold on: these are your fair test, so your agent gets frozen first. When you're ready: ./lab goto holdout"
    return None


def pr_paths(pr_set: str, only: str) -> list[Path]:
    paths = sorted(Path("data/review-prs", pr_set).glob("*.diff"))
    if only:
        return [p for p in paths if p.stem in only.split(",")]
    return paths


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
    parser.add_argument("--agent", default="", help="agent file, if you want to try another one. The held-out set uses your frozen agent unless you give one")
    args = parser.parse_args()
    reason = blocked(args.set, chunk_now())
    if reason:
        raise SystemExit(reason)
    agent = Path(args.agent) if args.agent else FROZEN if args.set == "holdout" else AGENT
    if agent == FROZEN and not FROZEN.exists():
        raise SystemExit("Your agent hasn't been frozen yet. Once my-work/3-reviewer-agent.md is written: ./lab goto holdout")
    check_agent(agent)
    if agent == FROZEN:
        print(f"Using your agent as it was frozen at {time.strftime('%H:%M', time.localtime(FROZEN.stat().st_mtime))}, for a fair test.")
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
    by_name = {path.stem: path for path in paths}
    if args.runs > 1:
        results = {path.stem: [a for job, a in zip(jobs, answers) if job == path] for path in paths}
        for name, reviews in results.items():
            for number, answer in enumerate(reviews, 1):
                show(f"{name} run {number}", answer, by_name[name] if number == 1 else None)
    else:
        results = {p.stem: a for p, a in zip(paths, answers)}
        for name, answer in results.items():
            show(name, answer, by_name[name])
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
