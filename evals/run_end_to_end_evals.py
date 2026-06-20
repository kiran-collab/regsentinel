"""End-to-end evals for the full RegSentinel audit workflow.

Runs the real orchestrator (``python -m regsentinel.orchestrator``) over each
golden regulatory case, then grades the produced artifacts:

* the Markdown report exists and has the required sections (report_scorer)
* the audit trail shows the expected specialist tools ran (trace_scorer)
* the specialists ran in the canonical phase order (trace_scorer)
* at least ``expected_gap_count_min`` gaps were recorded (coverage != full)

Requires ANTHROPIC_API_KEY and network access (the researcher fetches live
regulatory text). Without a key the runner SKIPS cleanly (exit 0) so CI on
forks / no-secret contexts stays green.

Run:  python -m evals.run_end_to_end_evals
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from evals.scorers.report_scorer import score_report
from evals.scorers.trace_scorer import load_audit_trail, score_phase_order, score_trace

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = Path(__file__).parent / "datasets" / "golden_regulatory_cases.json"
RESULTS_PATH = Path(__file__).parent / "results" / "e2e_eval_results.json"
AUDIT_PATH = ROOT / "audit_trail.jsonl"

MAP_TOOL = "mcp__compliance__map_control"


def _gap_count(records: list[dict[str, Any]]) -> int:
    """Count map_control calls whose coverage != full (i.e. recorded gaps)."""
    gaps = 0
    for r in records:
        if r.get("tool") == MAP_TOOL:
            coverage = str((r.get("input") or {}).get("coverage", "")).lower()
            if coverage and coverage != "full":
                gaps += 1
    return gaps


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    working_dir = ROOT / case["working_dir"]
    report_path = working_dir / "compliance_report.md"

    # Start each case from a clean slate so stale artifacts can't pass it.
    for stale in (report_path, AUDIT_PATH):
        if stale.exists():
            stale.unlink()

    proc = subprocess.run(
        [sys.executable, "-m", "regsentinel", case["regulations"], case["working_dir"]],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )

    report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
    records = load_audit_trail(AUDIT_PATH)

    expected = case["expected"]
    report_score = score_report(report_text, expected.get("required_report_sections"))
    trace_score = score_trace(records)
    order_score = score_phase_order(records)
    gaps = _gap_count(records)

    terms = expected.get("must_include_obligation_terms", [])
    lower_report = report_text.lower()
    term_hits = {t: t.lower() in lower_report for t in terms}

    passed = bool(
        report_path.exists()
        and proc.returncode == 0
        and report_score["passed"]
        and trace_score["used_obligation_extractor"]
        and trace_score["used_control_mapper"]
        and trace_score["used_risk_scorer"]
        and trace_score["used_citation_verifier"]
        and trace_score["wrote_report"]
        and order_score["passed"]
        and gaps >= expected.get("expected_gap_count_min", 0)
    )

    return {
        "case_id": case["case_id"],
        "regulations": case["regulations"],
        "returncode": proc.returncode,
        "report_exists": report_path.exists(),
        "report_score": report_score,
        "trace_score": trace_score,
        "order_score": order_score,
        "gap_count": gaps,
        "expected_gap_count_min": expected.get("expected_gap_count_min", 0),
        "term_hits": term_hits,
        "passed": passed,
    }


def run() -> dict[str, Any]:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    results = [run_case(case) for case in dataset]
    passed = sum(1 for r in results if r["passed"])
    summary = {
        "layer": "e2e",
        "skipped": False,
        "passed": passed,
        "total": len(results),
        "all_passed": passed == len(results),
        "results": results,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("SKIP: e2e evals need ANTHROPIC_API_KEY (live orchestrator run).")
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        skipped = {"layer": "e2e", "skipped": True, "reason": "no ANTHROPIC_API_KEY"}
        RESULTS_PATH.write_text(json.dumps(skipped, indent=2), encoding="utf-8")
        return

    summary = run()
    for r in summary["results"]:
        flag = "PASS" if r["passed"] else "FAIL"
        print(f"  [{flag}] {r['case_id']} (gaps={r['gap_count']}, rc={r['returncode']})")
    print(f"\nE2E evals: {summary['passed']}/{summary['total']} passed -> {RESULTS_PATH}")
    if not summary["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
