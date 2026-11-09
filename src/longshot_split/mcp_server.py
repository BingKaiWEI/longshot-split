"""MCP server (stdio, JSON-RPC 2.0) for longshot-split.

Hand-written protocol layer — zero dependencies beyond Pillow/numpy.
Frames are newline-delimited JSON as per the MCP stdio transport
(protocol version 2024-11-05, falling back to whatever the client offers).
"""

from __future__ import annotations

import json
import os
import sys

from . import __version__
from .core import split_image

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "split_long_image",
        "description": (
            "Adaptively split a long screenshot (chat log / web capture) into "
            "segments, cutting only on safe blank rows so text is never sliced. "
            "Returns segment file paths and a manifest summary."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the long image (PNG/JPEG/WebP)"},
                "max_height": {"type": "integer", "description": "Target segment height in px", "default": 4096},
                "overlap": {"type": "integer", "description": "Overlap between segments in px", "default": 24},
            },
            "required": ["path"],
        },
    }
]


def _reply(msg_id, result=None, error=None):
    resp = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        resp["error"] = error
    else:
        resp["result"] = result
    sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle(msg: dict) -> None:
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        client_version = params.get("protocolVersion", PROTOCOL_VERSION)
        _reply(
            msg_id,
            {
                "protocolVersion": client_version,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "longshot-split", "version": __version__},
            },
        )
    elif method == "notifications/initialized":
        pass  # notification, no reply
    elif method == "tools/list":
        _reply(msg_id, {"tools": TOOLS})
    elif method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name != "split_long_image":
            _reply(msg_id, error={"code": -32602, "message": f"unknown tool: {name}"})
            return
        path = arguments.get("path")
        if not path or not os.path.isfile(path):
            _reply(
                msg_id,
                {"content": [{"type": "text", "text": f"file not found: {path}"}], "isError": True},
            )
            return
        try:
            manifest = split_image(
                path,
                max_height=int(arguments.get("max_height", 4096)),
                overlap=int(arguments.get("overlap", 24)),
            )
        except Exception as exc:  # surface errors inside the tool result
            _reply(
                msg_id,
                {"content": [{"type": "text", "text": f"split failed: {exc}"}], "isError": True},
            )
            return
        summary = {
            "segment_count": manifest["segment_count"],
            "width": manifest["width"],
            "height": manifest["height"],
            "manifest_path": manifest["manifest_path"],
            "segments": [
                {"index": s["index"], "y_start": s["y_start"], "y_end": s["y_end"], "file": s["file"]}
                for s in manifest["segments"]
            ],
        }
        _reply(
            msg_id,
            {"content": [{"type": "text", "text": json.dumps(summary, ensure_ascii=False, indent=2)}], "isError": False},
        )
    elif msg_id is not None:
        _reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


def serve() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            _reply(None, error={"code": -32700, "message": "parse error"})
            continue
        _handle(msg)
    return 0


if __name__ == "__main__":
    sys.exit(serve())
