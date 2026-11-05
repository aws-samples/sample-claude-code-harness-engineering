"""Your checks. Reference solution, from ./lab catch-up checks. scripts/run_checks.py runs it."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass

SDKS = {"boto3", "httpx", "requests"}
SECRET = re.compile(r"""AKIA[0-9A-Z]{16}|(?i:\b\w*(password|secret|api_?key|token|access_key)\s*(:\s*[\w\[\]| ]+)?=\s*[bf]?["'][^"']+["']|["']\w*(password|secret|api_?key|token|access_key)["']\s*:\s*["'][^"']+["'])""")
DROPS = re.compile(r"""(?i:\bDROP\s+(TABLE|DATABASE)\b|\bTRUNCATE\s+TABLE\b)|\bTRUNCATE\s+\w+""")
DELETE_ALL = re.compile(r"""(?i)\bDELETE\s+FROM\s+[\w{}.]+\s*(;|--|\\|["'])""")


@dataclass
class Finding:
    rule: str
    line: int
    message: str  # tell whoever hit it how to fix it


POLICY: dict[str, str] = {
    "R2": "block",
    "R4": "block",
    "R7": "block",
    "R10": "block",
    "R11": "warn",
}

SCOPE = "new"


def check_source(path: str, source: str) -> list[Finding]:
    """Findings for one file, given its path from the repo root, such as appointment_reminders/app/api/health.py."""
    findings: list[Finding] = []
    code_path = path.removeprefix("appointment_reminders/")
    for number, line in enumerate(source.splitlines(), 1):
        if not code_path.startswith("migrations/") and DROPS.search(line):
            findings.append(Finding("R2", number, "Destructive SQL. Move it to migrations/."))
        if SECRET.search(line):
            findings.append(Finding("R10", number, "Looks like a secret. Read it from the environment or the secrets manager."))
    if not code_path.startswith("migrations/"):
        for match in DELETE_ALL.finditer(source):  # across lines, since a WHERE can be on the next one
            findings.append(Finding("R2", source.count("\n", 0, match.start()) + 1, "DELETE with no WHERE. Add a WHERE, or move it to migrations/."))
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if code_path.startswith(("service/", "app/")) and isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            findings.extend(Finding("R4", node.lineno, f"{name} imported outside tools/. Put the call in tools/.") for name in names if name.split(".")[0] in SDKS)
        if code_path.startswith("app/api/") and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decorators = [ast.unparse(d) for d in node.decorator_list]
            if any(".route(" in d for d in decorators) and not any("rate_limit" in d for d in decorators if ".route(" not in d):
                findings.append(Finding("R7", node.lineno, f"Route {node.name} has no rate limit. Add @rate_limit()."))
    if code_path.startswith("tools/"):
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_") and "Failure modes:" not in (ast.get_docstring(node) or ""):
                findings.append(Finding("R11", node.lineno, f"{node.name} has no Failure modes: section in its docstring."))
    return findings
