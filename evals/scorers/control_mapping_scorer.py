"""Control-mapping scorer.

``map_control`` records an obligation -> internal-control mapping with a coverage
judgement (full/partial/none) and derives ``is_gap`` (coverage != full). This
scorer validates the coverage vocabulary, the gap derivation, and — when the
case supplies them — the expected coverage/control id.
"""

from __future__ import annotations

from typing import Any

from ._util import is_error, tool_json

VALID_COVERAGE = {"full", "partial", "none"}


def score_control_mapping(result: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """Score a raw ``map_control`` tool result against the case's expectations.

    If ``expected`` sets ``error: true`` the tool is expected to reject the input
    (invalid coverage value).
    """
    if expected.get("error"):
        return {
            "expected": "error",
            "predicted": "error" if is_error(result) else "no-error",
            "passed": is_error(result),
        }

    if is_error(result):
        return {"expected": expected, "predicted": "error", "passed": False}

    payload = tool_json(result)
    coverage = str(payload.get("coverage", "")).lower()
    expected_gap = expected.get("coverage", "") != "full"

    valid_coverage = coverage in VALID_COVERAGE
    coverage_match = coverage == expected.get("coverage")
    control_id_match = payload.get("control_id") == expected.get("control_id")
    gap_match = payload.get("is_gap") is expected_gap
    has_rationale = bool(payload.get("rationale"))

    return {
        "valid_coverage": valid_coverage,
        "coverage_match": coverage_match,
        "control_id_match": control_id_match,
        "gap_match": gap_match,
        "has_rationale": has_rationale,
        "passed": all([valid_coverage, coverage_match, control_id_match, gap_match, has_rationale]),
    }
