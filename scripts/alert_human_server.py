#!/usr/bin/env python3
"""The reviewer agent's alert_human tool, as a tiny MCP server over stdio.

It alerts nobody. It records the request in $ALERT_LOG, and scripts/review_pipeline.py decides what happens to it.
"""
from __future__ import annotations

import json
import os
import sys

TOOL = {
    "name": "alert_human",
    "description": "Ask for a person to review this PR before it merges. Say why, and summarize the PR for someone who hasn't seen it.",
    "inputSchema": {
        "type": "object",
        "properties": {"reason": {"type": "string"}, "summary": {"type": "string"}},
        "required": ["reason", "summary"],
    },
}


def handle(message: dict) -> dict | None:
    method = message.get("method")
    if "id" not in message:
        return None  # a notification needs no reply
    if method == "initialize":
        result = {"protocolVersion": message["params"].get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {}}, "serverInfo": {"name": "gate", "version": "1"}}
    elif method == "tools/list":
        result = {"tools": [TOOL]}
    elif method == "tools/call":
        with open(os.environ["ALERT_LOG"], "a") as log:
            log.write(json.dumps(message.get("params", {}).get("arguments", {})) + "\n")
        result = {"content": [{"type": "text", "text": "Request recorded. Now finish your review and give your verdict."}]}
    elif method == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": message["id"], "error": {"code": -32601, "message": f"unknown method {method}"}}
    return {"jsonrpc": "2.0", "id": message["id"], "result": result}


for line in sys.stdin:
    try:
        reply = handle(json.loads(line))
    except (ValueError, KeyError, AttributeError, OSError):
        continue
    if reply is not None:
        print(json.dumps(reply), flush=True)
