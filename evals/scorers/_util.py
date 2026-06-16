"""Helpers for unwrapping in-process MCP tool results.

The compliance tools (``@tool``-decorated handlers) return the MCP content
envelope::

    {"content": [{"type": "text", "text": "<json or plain string>"}],
     "is_error": <optional bool>}

Scorers want the decoded payload, so these helpers centralize the unwrapping
(and the one place that has to change if the envelope ever does).
"""

from __future__ import annotations

import json
from typing import Any


def tool_text(result: dict[str, Any]) -> str:
    """Return the first text block from an MCP tool result."""
    return result["content"][0]["text"]


def tool_json(result: dict[str, Any]) -> dict[str, Any]:
    """Decode the first text block of an MCP tool result as JSON."""
    return json.loads(tool_text(result))


def is_error(result: dict[str, Any]) -> bool:
    """True if the tool flagged the call as an error."""
    return result.get("is_error") is True
