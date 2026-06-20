"""Aggregate per-layer result JSON into a single Markdown summary.

Reads whatever ``results/*_eval_results.json`` files exist and writes
``results/eval_summary.md``. Safe to run after any subset of layers.

Run:  python -m evals.summarize
"""

from __future__ import annotations

import json
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
SUMMARY_PATH = RESULTS / "eval_summary.md"

LAYER_FILES = {
    "unit": "unit_eval_results.json",
    "guardrail": "guardrail_eval_results.json",
    "agent": "agent_eval_results.json",
    "e2e": "e2e_eval_results.json",
}


def main() -> None:
    lines = ["# RegSentinel Eval Summary", ""]
    lines.append("| Layer | Status | Passed | Total |")
    lines.append("|---|---|---|---|")

    for layer, fname in LAYER_FILES.items():
        path = RESULTS / fname
        if not path.exists():
            lines.append(f"| {layer} | not run | – | – |")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("skipped"):
            lines.append(f"| {layer} | skipped ({data.get('reason', '')}) | – | – |")
            continue
        status = "✅ pass" if data.get("all_passed") else "❌ fail"
        passed, total = data.get("passed", "?"), data.get("total", "?")
        lines.append(f"| {layer} | {status} | {passed} | {total} |")

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
