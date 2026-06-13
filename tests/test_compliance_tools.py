"""
Unit tests for the deterministic compliance tools.

These prove the auditable core is reproducible — the part a regulator cares
about most. Run with: pytest -q

The @tool decorator wraps each function in an SdkMcpTool; the original async
handler is preserved at `.handler`, which is what we exercise here.
"""

import asyncio
import json

from regsentinel.tools.compliance_tools import (
    extract_obligations,
    map_control,
    score_risk,
    verify_citation,
)


def _call(sdk_tool, args):
    return asyncio.run(sdk_tool.handler(args))


def _text(result):
    return result["content"][0]["text"]


def test_score_risk_matrix():
    res = _call(score_risk, {"likelihood": "high", "impact": "high", "gap_description": "x"})
    assert json.loads(_text(res))["risk_band"] == "critical"
    res = _call(score_risk, {"likelihood": "low", "impact": "low", "gap_description": "x"})
    assert json.loads(_text(res))["risk_band"] == "informational"


def test_score_risk_rejects_bad_input():
    res = _call(score_risk, {"likelihood": "extreme", "impact": "low", "gap_description": "x"})
    assert res.get("is_error") is True


def test_verify_citation_normalizes_whitespace():
    res = _call(verify_citation, {
        "quoted_snippet": "shall   maintain a   record",
        "source_text": "The controller shall maintain a record of activities.",
    })
    assert json.loads(_text(res))["citation_verified"] is True


def test_verify_citation_detects_fabrication():
    res = _call(verify_citation, {
        "quoted_snippet": "must publish results within 24 hours",
        "source_text": "The controller shall maintain a record of activities.",
    })
    assert json.loads(_text(res))["citation_verified"] is False


def test_extract_obligations_flags_mandatory():
    text = (
        "Article 9 Risk management. (a) The provider shall establish a risk "
        "management system covering the lifecycle of the high-risk AI system. "
        "(b) Providers may consider additional mitigations where appropriate."
    )
    res = _call(extract_obligations, {"regulation_id": "EUAIA", "text": text})
    obligations = json.loads(_text(res))["obligations"]
    assert len(obligations) >= 1
    assert any(o["is_mandatory"] for o in obligations)


def test_map_control_marks_gap():
    res = _call(map_control, {
        "obligation_id": "EUAIA:abc",
        "control_id": "CTRL-014",
        "coverage": "partial",
        "rationale": "no residual-risk acceptance step",
    })
    assert json.loads(_text(res))["is_gap"] is True
