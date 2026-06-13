"""
Lifecycle hooks for RegSentinel governance.

Hooks are where agentic systems earn trust in regulated settings. They run
deterministic Python at fixed points in the agent loop, independent of anything
the model decides. We use them for two things big-tech reviewers will look for:

1. A tamper-evident **audit log** of every tool invocation (PostToolUse).
2. **Egress guarding** — a PreToolUse hook that can block a web fetch to a
   domain not on the allowlist, containing exfiltration / injection risk.

Hooks return {} to allow, or a decision dict to block.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

AUDIT_LOG = Path("audit_trail.jsonl")

# Domains the researcher subagent is permitted to fetch. In production this
# would come from config / a policy service.
ALLOWED_FETCH_DOMAINS = {
    "eur-lex.europa.eu",
    "gdpr.eu",
    "www.iso.org",
    "csrc.nist.gov",
    "www.federalregister.gov",
    "aicpa.org",
    "www.aicpa.org",
}


async def audit_tool_use(
    input_data: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    """PostToolUse: append a structured record of every tool call."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool_use_id": tool_use_id,
        "tool": input_data.get("tool_name"),
        "input": input_data.get("tool_input"),
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {}


async def guard_egress(
    input_data: dict[str, Any], tool_use_id: str | None, context: Any
) -> dict[str, Any]:
    """PreToolUse: block WebFetch to any domain outside the allowlist."""
    if input_data.get("tool_name") != "WebFetch":
        return {}

    url = input_data.get("tool_input", {}).get("url", "")
    host = urlparse(url).netloc.lower()

    if host and host not in ALLOWED_FETCH_DOMAINS:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Egress to '{host}' blocked: not on the regulator allowlist. "
                    f"Add it to ALLOWED_FETCH_DOMAINS to permit."
                ),
            }
        }
    return {}
