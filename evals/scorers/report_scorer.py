"""Final-report quality scorer.

Structural + evidence checks on the report-writer's Markdown deliverable. This
is intentionally a deterministic floor (sections present, risk band named,
citation + gap language present); qualitative grading lives in the optional
LLM-as-judge layer (see evals/run_agent_evals.py docstring).
"""

from __future__ import annotations

from typing import Any

REQUIRED_REPORT_SECTIONS = [
    "executive summary",
    "risk register",
    "per-obligation coverage",
    "citation appendix",
]

RISK_BANDS = ["critical", "high", "medium", "low", "informational"]


def score_report(report_text: str, required_sections: list[str] | None = None) -> dict[str, Any]:
    lower = report_text.lower()
    sections = required_sections or REQUIRED_REPORT_SECTIONS

    section_scores = {section: section.lower() in lower for section in sections}
    has_risk_band = any(band in lower for band in RISK_BANDS)
    has_citation_language = "citation" in lower or "source" in lower
    has_gap_language = any(w in lower for w in ("gap", "partial", "none"))

    return {
        "sections": section_scores,
        "has_risk_band": has_risk_band,
        "has_citation_language": has_citation_language,
        "has_gap_language": has_gap_language,
        "passed": bool(
            all(section_scores.values())
            and has_risk_band
            and has_citation_language
            and has_gap_language
        ),
    }
