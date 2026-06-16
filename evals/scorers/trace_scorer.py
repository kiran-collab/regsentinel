"""Orchestration / trace scorer.

The PostToolUse hook appends one record per tool call to ``audit_trail.jsonl``::

    {"ts": ..., "tool_use_id": ..., "tool": "<name>", "input": {...}}

That trail is a free governance artifact we turn into a regression signal: which
specialist tools ran, and did they run in the expected phase order
(research -> extract -> map -> score -> write)?
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

EXTRACT = "mcp__compliance__extract_obligations"
MAP = "mcp__compliance__map_control"
SCORE = "mcp__compliance__score_risk"
VERIFY = "mcp__compliance__verify_citation"

# Canonical phase order, by representative tool. WebSearch/WebFetch collapse to
# a single "research" phase (either satisfies it).
PHASE_ORDER = ["research", EXTRACT, MAP, SCORE, "Write"]


def load_audit_trail(path: str | Path = "audit_trail.jsonl") -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    p = Path(path)
    if not p.exists():
        return records
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def score_trace(records: list[dict[str, Any]]) -> dict[str, Any]:
    tools_used = [r.get("tool") for r in records]
    used_set = set(tools_used)
    return {
        "used_web_research": bool(used_set & {"WebSearch", "WebFetch"}),
        "used_obligation_extractor": EXTRACT in used_set,
        "used_control_mapper": MAP in used_set,
        "used_risk_scorer": SCORE in used_set,
        "used_citation_verifier": VERIFY in used_set,
        "wrote_report": "Write" in used_set,
        "tool_call_count": len(tools_used),
    }


def _phase_label(tool: str | None) -> str | None:
    if tool in {"WebSearch", "WebFetch"}:
        return "research"
    if tool in {EXTRACT, MAP, SCORE, "Write"}:
        return tool
    return None


def score_phase_order(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Check the FIRST occurrence of each phase respects PHASE_ORDER.

    Tolerant of interleaving and repeats — it only requires that the first time
    each phase's tool appears, all earlier phases already appeared. Phases that
    never run are reported but do not by themselves fail ordering (presence is
    covered by score_trace); only an out-of-order pair fails.
    """
    first_idx: dict[str, int] = {}
    for i, r in enumerate(records):
        label = _phase_label(r.get("tool"))
        if label and label not in first_idx:
            first_idx[label] = i

    present = [p for p in PHASE_ORDER if p in first_idx]
    in_order = all(
        first_idx[present[k]] < first_idx[present[k + 1]]
        for k in range(len(present) - 1)
    )
    return {
        "observed_phases": present,
        "expected_order": PHASE_ORDER,
        "passed": in_order,
    }
