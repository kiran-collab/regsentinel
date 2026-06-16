"""Guardrail evals for the governance hooks.

Drives ``guard_egress`` (the PreToolUse egress allowlist) over the adversarial
URL dataset and confirms each fetch is allowed or denied as expected. Pure and
deterministic — no API key, no network — so it gates every push alongside the
unit evals.

Run:  python -m evals.run_guardrail_evals
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from regsentinel.hooks import guard_egress

DATASETS = Path(__file__).parent / "datasets"
RESULTS_PATH = Path(__file__).parent / "results" / "guardrail_eval_results.json"


async def _decision_for(url: str) -> str:
    """Return 'deny' or 'allow' for a WebFetch to ``url``."""
    result = await guard_egress(
        input_data={"tool_name": "WebFetch", "tool_input": {"url": url}},
        tool_use_id="eval",
        context=None,
    )
    decision = (
        result.get("hookSpecificOutput", {}).get("permissionDecision")
        if result
        else None
    )
    # Hook returns {} (allow) or a deny decision dict.
    return "deny" if decision == "deny" else "allow"


def run() -> dict[str, Any]:
    cases = json.loads((DATASETS / "adversarial_cases.json").read_text(encoding="utf-8"))
    results = []
    for case in cases:
        observed = asyncio.run(_decision_for(case["url"]))
        results.append({
            "case_id": case["case_id"],
            "url": case["url"],
            "expected": case["expected_decision"],
            "observed": observed,
            "passed": observed == case["expected_decision"],
        })

    # Sanity: a non-WebFetch tool must never be blocked by the egress guard.
    passthrough = asyncio.run(guard_egress(
        input_data={"tool_name": "Read", "tool_input": {"file_path": "x"}},
        tool_use_id="eval", context=None,
    ))
    results.append({
        "case_id": "non_webfetch_passthrough",
        "url": "(Read tool)",
        "expected": "allow",
        "observed": "allow" if passthrough == {} else "deny",
        "passed": passthrough == {},
    })

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    summary = {
        "layer": "guardrail",
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
        print(f"  [{flag}] {r['case_id']:<28} expected={r['expected']:<5} "
              f"observed={r['observed']}")
    print(f"\nGuardrail evals: {summary['passed']}/{summary['total']} passed "
          f"-> {RESULTS_PATH}")
    if not summary["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
