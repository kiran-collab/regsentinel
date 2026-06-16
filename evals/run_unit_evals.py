"""Unit evals for the deterministic compliance MCP tools.

Exercises ``extract_obligations``, ``score_risk``, ``verify_citation`` and
``map_control`` over the dataset cases and grades each with its scorer. This is
the most defensible layer — pure Python, no model, no network, no API key — and
is the gate that runs on every push.

Run:  python -m evals.run_unit_evals
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from regsentinel.tools.compliance_tools import (
    extract_obligations,
    map_control,
    score_risk,
    verify_citation,
)

from evals.scorers.citation_scorer import score_citation_verification
from evals.scorers.control_mapping_scorer import score_control_mapping
from evals.scorers.obligation_scorer import score_obligations
from evals.scorers.risk_scorer import score_tool_result as score_risk_result

DATASETS = Path(__file__).parent / "datasets"
RESULTS_PATH = Path(__file__).parent / "results" / "unit_eval_results.json"


def _call(sdk_tool, args: dict[str, Any]) -> dict[str, Any]:
    """Invoke a @tool-decorated handler synchronously (matches tests)."""
    return asyncio.run(sdk_tool.handler(args))


def _load(name: str) -> Any:
    return json.loads((DATASETS / name).read_text(encoding="utf-8"))


def eval_risk_matrix() -> list[dict[str, Any]]:
    out = []
    for case in _load("risk_matrix_cases.json"):
        result = _call(score_risk, {
            "likelihood": case["likelihood"],
            "impact": case["impact"],
            "gap_description": "eval gap",
        })
        score = score_risk_result(
            case["likelihood"], case["impact"], result,
            expect_error=case.get("expect_error", False),
        )
        out.append({"suite": "risk_matrix", "case_id": case["case_id"], **score})
    return out


def eval_citations() -> list[dict[str, Any]]:
    out = []
    for case in _load("citation_cases.json"):
        result = _call(verify_citation, {
            "quoted_snippet": case["quoted_snippet"],
            "source_text": case["source_text"],
        })
        score = score_citation_verification(result, case["expected_verified"])
        out.append({"suite": "citation", "case_id": case["case_id"], **score})
    return out


def eval_control_mapping() -> list[dict[str, Any]]:
    out = []
    for case in _load("control_mapping_cases.json"):
        result = _call(map_control, case["args"])
        score = score_control_mapping(result, case["expected"])
        out.append({"suite": "control_mapping", "case_id": case["case_id"], **score})
    return out


def eval_obligations() -> list[dict[str, Any]]:
    out = []
    for case in _load("obligation_cases.json"):
        result = _call(extract_obligations, {
            "regulation_id": case["regulation_id"],
            "text": case["source_text"],
        })
        score = score_obligations(result, case["expected"], case["source_text"])
        out.append({"suite": "obligation", "case_id": case["case_id"], **score})
    return out


def run() -> dict[str, Any]:
    results = (
        eval_risk_matrix()
        + eval_citations()
        + eval_control_mapping()
        + eval_obligations()
    )
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    summary = {
        "layer": "unit",
        "passed": passed,
        "total": total,
        "all_passed": passed == total,
        "results": results,
    }
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    summary = run()
    for r in summary["results"]:
        flag = "PASS" if r["passed"] else "FAIL"
        print(f"  [{flag}] {r['suite']:<16} {r['case_id']}")
    print(f"\nUnit evals: {summary['passed']}/{summary['total']} passed "
          f"-> {RESULTS_PATH}")
    if not summary["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
