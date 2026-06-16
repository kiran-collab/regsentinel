"""Tests that lock the deterministic eval layers under pytest.

The unit and guardrail eval runners are pure (no API key, no network), so we
gate them in CI by asserting they pass here. We also exercise the pure scorers
(trace ordering, report structure) with synthetic fixtures, and confirm the
model-driven runners SKIP cleanly when no API key is present.
"""

import os

import pytest

from evals import run_guardrail_evals, run_unit_evals
from evals.scorers.report_scorer import score_report
from evals.scorers.risk_scorer import score_risk_matrix_result
from evals.scorers.trace_scorer import score_phase_order, score_trace


def test_unit_evals_all_pass():
    summary = run_unit_evals.run()
    failures = [r for r in summary["results"] if not r["passed"]]
    assert summary["all_passed"], f"unit eval failures: {failures}"
    assert summary["total"] >= 20


def test_guardrail_evals_all_pass():
    summary = run_guardrail_evals.run()
    failures = [r for r in summary["results"] if not r["passed"]]
    assert summary["all_passed"], f"guardrail eval failures: {failures}"


def test_risk_oracle_rejects_wrong_band():
    # The oracle must FAIL a mis-scored cell — proving it can catch a regression.
    bad = score_risk_matrix_result("high", "high", "low")
    assert bad["passed"] is False
    good = score_risk_matrix_result("high", "high", "critical")
    assert good["passed"] is True


def test_trace_phase_order():
    ordered = [
        {"tool": "WebSearch"},
        {"tool": "mcp__compliance__extract_obligations"},
        {"tool": "mcp__compliance__map_control"},
        {"tool": "mcp__compliance__score_risk"},
        {"tool": "Write"},
    ]
    assert score_phase_order(ordered)["passed"] is True

    out_of_order = [
        {"tool": "Write"},
        {"tool": "mcp__compliance__extract_obligations"},
    ]
    assert score_phase_order(out_of_order)["passed"] is False


def test_trace_presence_flags():
    flags = score_trace([
        {"tool": "WebFetch"},
        {"tool": "mcp__compliance__extract_obligations"},
        {"tool": "Write"},
    ])
    assert flags["used_web_research"] is True
    assert flags["used_obligation_extractor"] is True
    assert flags["used_control_mapper"] is False


def test_report_scorer_requires_sections():
    incomplete = score_report("# Executive Summary\nsome text")
    assert incomplete["passed"] is False

    complete = score_report(
        "# Executive Summary\n"
        "## Risk Register\nHighest band: high. Gap found.\n"
        "## Per-Obligation Coverage\npartial\n"
        "## Citation Appendix\nsource: https://gdpr.eu\n"
    )
    assert complete["passed"] is True


@pytest.mark.skipif(
    bool(os.getenv("ANTHROPIC_API_KEY")),
    reason="skip-path test only meaningful without an API key",
)
def test_model_runners_skip_without_key():
    from evals import run_agent_evals, run_end_to_end_evals

    # main() must not raise when no key is set (it should skip, not run).
    run_agent_evals.main()
    run_end_to_end_evals.main()
