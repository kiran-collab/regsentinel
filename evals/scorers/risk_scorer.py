"""Risk-matrix scorer.

The whole point of RegSentinel's ``score_risk`` tool is that the band comes from
a FIXED likelihood x impact matrix, not the model's judgement. This scorer keeps
an independent copy of the expected matrix so a regression in the tool's matrix
is detected rather than mirrored.
"""

from __future__ import annotations

from typing import Any

from ._util import is_error, tool_json

# Independent oracle. Must match compliance_tools._RISK_MATRIX by VALUE, but is
# deliberately a separate definition so drift is caught.
RISK_MATRIX_EXPECTED: dict[tuple[str, str], str] = {
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


def score_risk_matrix_result(likelihood: str, impact: str, predicted_band: str) -> dict[str, Any]:
    """Pure comparison: does ``predicted_band`` match the oracle for this cell?"""
    key = (likelihood.strip().lower(), impact.strip().lower())
    expected_band = RISK_MATRIX_EXPECTED.get(key)
    return {
        "likelihood": key[0],
        "impact": key[1],
        "expected": expected_band,
        "predicted": predicted_band,
        "passed": expected_band is not None and expected_band == predicted_band,
    }


def score_tool_result(likelihood: str, impact: str, result: dict[str, Any],
                      expect_error: bool = False) -> dict[str, Any]:
    """Score a raw ``score_risk`` tool result.

    For valid cells, checks the returned ``risk_band`` against the oracle. For
    cells expected to be rejected (bad input), checks the tool flagged an error.
    """
    if expect_error:
        return {
            "likelihood": likelihood,
            "impact": impact,
            "expected": "error",
            "predicted": "error" if is_error(result) else "no-error",
            "passed": is_error(result),
        }

    if is_error(result):
        return {
            "likelihood": likelihood,
            "impact": impact,
            "expected": RISK_MATRIX_EXPECTED.get((likelihood.lower(), impact.lower())),
            "predicted": "error",
            "passed": False,
        }

    predicted = tool_json(result).get("risk_band")
    return score_risk_matrix_result(likelihood, impact, predicted)
