"""Pytest wrapper for the MCP server end-to-end selftest."""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from selftest_mcp import run_selftest  # noqa: E402


def test_mcp_server_end_to_end():
    assert run_selftest() is True
