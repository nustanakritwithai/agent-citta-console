"""Minimal local stdio JSON tool skeleton.

This is a local MCP-style foundation, not a complete MCP server yet. It reads
one JSON object per line from stdin:

{"tool":"citta.list_adapters","input":{}}
"""

from __future__ import annotations

import json
import sys
from typing import TextIO

from .tools.dispatcher import dispatch_tool


def serve_stdio(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    for line in stdin:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            request = json.loads(stripped)
            if not isinstance(request, dict):
                raise ValueError("request must be a JSON object")
            tool = request.get("tool")
            if not isinstance(tool, str) or not tool:
                raise ValueError("tool is required")
            payload = request.get("input") or {}
            result = dispatch_tool(tool, payload)
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
        stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(serve_stdio())
