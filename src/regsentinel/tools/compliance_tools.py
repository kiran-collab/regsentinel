"""
In-process MCP tools for RegSentinel.

These are *custom tools* exposed to Claude via the Agent SDK's in-process MCP
server (`create_sdk_mcp_server`). They encapsulate deterministic, auditable
domain logic that we never want the model to "hallucinate": clause hashing,
control-mapping math, risk scoring, and citation integrity checks.

Keeping this logic in real Python (not in the prompt) is what makes the
system's findings reproducible and defensible to an auditor.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


# --------------------------------------------------------------------------- #
# Deterministic helpers (pure functions, unit-tested)
# --------------------------------------------------------------------------- #
def _clause_fingerprint(text: str) -> str:
    """Stable fingerprint of a normalized clause, for dedup + audit trail."""
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


# Likelihood x impact -> qualitative band. Auditors expect a fixed matrix,
# not a model's vibe. This matrix is the single source of truth.
_RISK_MATRIX = {
    ("low", "low"): "informational",
    ("low", "medium"): "low",
    ("low", "high"): "medium",
    ("medium", "low"): "low",
    ("medium", "medium"): "medium",
    ("medium", "high"): "high",
    ("high", "low"): "medium",
    ("high", "medium"): "high",
    ("high", "high"): "critical",
}


# --------------------------------------------------------------------------- #
# Tools
# --------------------------------------------------------------------------- #
@tool(
    "extract_obligations",
    "Extract individual regulatory obligations from a block of regulation "
    "text. Splits on enumerated clauses and returns each as a fingerprinted "
    "obligation object so downstream agents can map controls to it.",
    {"regulation_id": str, "text": str},
)
async def extract_obligations(args: dict[str, Any]) -> dict[str, Any]:
    text = args["text"]
    reg_id = args["regulation_id"]

    # Split on enumerated markers like "(a)", "1.", "Article 5", "§ 12".
    raw_clauses = re.split(
        r"(?=\b(?:Article|Section|§)\s+\d+|\(\w+\)|\n\s*\d+\.\s)",
        text,
    )
    obligations = []
    for clause in raw_clauses:
        clause = clause.strip()
        if len(clause) < 25:  # skip headers / fragments
            continue
        obligations.append(
            {
                "obligation_id": f"{reg_id}:{_clause_fingerprint(clause)}",
                "text": clause,
                "is_mandatory": bool(
                    re.search(r"\b(shall|must|required to|may not)\b", clause, re.I)
                ),
            }
        )

    return {
        "content": [
            {"type": "text", "text": json.dumps({"obligations": obligations}, indent=2)}
        ]
    }


@tool(
    "score_risk",
    "Score a single compliance gap using the fixed enterprise risk matrix. "
    "Returns a qualitative band (informational/low/medium/high/critical). "
    "Likelihood and impact must each be one of: low, medium, high.",
    {"likelihood": str, "impact": str, "gap_description": str},
)
async def score_risk(args: dict[str, Any]) -> dict[str, Any]:
    likelihood = args["likelihood"].strip().lower()
    impact = args["impact"].strip().lower()
    key = (likelihood, impact)

    if key not in _RISK_MATRIX:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "ERROR: likelihood and impact must each be "
                        "'low', 'medium', or 'high'."
                    ),
                }
            ],
            "is_error": True,
        }

    band = _RISK_MATRIX[key]
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "risk_band": band,
                        "likelihood": likelihood,
                        "impact": impact,
                        "gap": args["gap_description"],
                        "scored_at": datetime.now(timezone.utc).isoformat(),
                    }
                ),
            }
        ]
    }


@tool(
    "verify_citation",
    "Integrity check for a claimed citation. Confirms the quoted snippet "
    "actually appears (normalized) in the cited source text. Use this before "
    "asserting any finding so the audit trail cannot be fabricated.",
    {"quoted_snippet": str, "source_text": str},
)
async def verify_citation(args: dict[str, Any]) -> dict[str, Any]:
    def norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())

    found = norm(args["quoted_snippet"]) in norm(args["source_text"])
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "citation_verified": found,
                        "fingerprint": _clause_fingerprint(args["quoted_snippet"]),
                    }
                ),
            }
        ]
    }


@tool(
    "map_control",
    "Record a mapping between a regulatory obligation and an internal control, "
    "with a coverage judgement. coverage must be one of: full, partial, none.",
    {
        "obligation_id": str,
        "control_id": str,
        "coverage": str,
        "rationale": str,
    },
)
async def map_control(args: dict[str, Any]) -> dict[str, Any]:
    coverage = args["coverage"].strip().lower()
    if coverage not in {"full", "partial", "none"}:
        return {
            "content": [
                {"type": "text", "text": "ERROR: coverage must be full/partial/none."}
            ],
            "is_error": True,
        }
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(
                    {
                        "obligation_id": args["obligation_id"],
                        "control_id": args["control_id"],
                        "coverage": coverage,
                        "rationale": args["rationale"],
                        "is_gap": coverage != "full",
                    }
                ),
            }
        ]
    }


# --------------------------------------------------------------------------- #
# Server factory
# --------------------------------------------------------------------------- #
def build_compliance_server():
    """Create the in-process MCP server exposing the compliance tools."""
    return create_sdk_mcp_server(
        name="compliance",
        version="1.0.0",
        tools=[extract_obligations, score_risk, verify_citation, map_control],
    )


# Pre-approved tool names for ClaudeAgentOptions.allowed_tools
COMPLIANCE_TOOL_NAMES = [
    "mcp__compliance__extract_obligations",
    "mcp__compliance__score_risk",
    "mcp__compliance__verify_citation",
    "mcp__compliance__map_control",
]
