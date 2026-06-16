"""Citation-integrity scorer.

``verify_citation`` is the system's structural defense against fabricated
findings: it confirms a quoted snippet actually appears (whitespace-normalized)
in the cited source. This scorer checks the tool's verdict against the case's
ground truth and confirms a fingerprint is always emitted.
"""

from __future__ import annotations

from typing import Any

from ._util import tool_json


def score_citation_verification(result: dict[str, Any], expected_verified: bool) -> dict[str, Any]:
    """Score a raw ``verify_citation`` tool result against expected truth."""
    payload = tool_json(result)
    verified = payload.get("citation_verified")
    has_fingerprint = bool(payload.get("fingerprint"))
    return {
        "citation_verified": verified,
        "expected_verified": expected_verified,
        "has_fingerprint": has_fingerprint,
        "passed": verified is expected_verified and has_fingerprint,
    }
