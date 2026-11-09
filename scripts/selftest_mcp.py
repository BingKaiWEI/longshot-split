"""End-to-end selftest for the MCP server: spawn it via subprocess, run
initialize -> tools/list -> tools/call, and verify the produced files.

Run directly:  python scripts/selftest_mcp.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _send(proc, payload: dict) -> None:
    proc.stdin.write(json.dumps(payload) + "\n")
    proc.stdin.flush()


def _recv(proc, msg_id: int) -> dict:
    while True:
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError(f"server closed stdout while waiting for id={msg_id}")
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if msg.get("id") == msg_id:
            return msg
        # ignore notifications


def run_selftest() -> bool:
    # 1. build a synthetic long chat image
    sys.path.insert(0, os.path.join(ROOT, "tests"))
    from synth import make_chat_image

    tmp = tempfile.mkdtemp(prefix="longshot_mcp_")
    img_path = make_chat_image(os.path.join(tmp, "chat.png"), width=1000, height=8000)

    # 2. spawn the MCP server as a subprocess
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "longshot_split.mcp_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )
    try:
        # 3. initialize handshake
        _send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "selftest", "version": "0.0.0"},
        }})
        init = _recv(proc, 1)
        assert init["result"]["serverInfo"]["name"] == "longshot-split", init
        assert init["result"]["protocolVersion"] == "2024-11-05", init
        print(f"[ok] initialize: protocol={init['result']['protocolVersion']} "
              f"server={init['result']['serverInfo']['name']} v{init['result']['serverInfo']['version']}")

        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        # 4. tools/list contains split_long_image
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = _recv(proc, 2)
        names = [t["name"] for t in tools["result"]["tools"]]
        assert "split_long_image" in names, names
        print(f"[ok] tools/list: {names}")

        # 5. tools/call actually produces segment files
        _send(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "split_long_image",
            "arguments": {"path": img_path, "max_height": 4096, "overlap": 24},
        }})
        call = _recv(proc, 3)
        result = call["result"]
        assert result.get("isError") is False, result
        summary = json.loads(result["content"][0]["text"])
        assert summary["segment_count"] >= 2, summary
        for seg in summary["segments"]:
            assert os.path.isfile(seg["file"]) and os.path.getsize(seg["file"]) > 0, seg
        assert os.path.isfile(summary["manifest_path"])
        print(f"[ok] tools/call: {summary['segment_count']} segments written, "
              f"manifest at {summary['manifest_path']}")

        print("SELFTEST PASS")
        return True
    finally:
        proc.stdin.close()
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    ok = run_selftest()
    sys.exit(0 if ok else 1)
