#!/usr/bin/env bash
# Non-blocking lint after a Python edit. It only reports, so that it can't remove an import Claude is about to use.
file=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))')
[[ "$file" == *.py ]] && uv run ruff check -q "$file" 1>&2
exit 0
