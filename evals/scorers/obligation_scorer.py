"""Obligation-extraction scorer.

``extract_obligations`` splits regulatory text into atomic, fingerprinted
obligations and flags each as mandatory ("shall/must/required to/may not") or
advisory. We grade four properties:

* recall      — every required obligation TERM appears in some extracted clause
* count       — at least ``expected_min_obligations`` clauses survive filtering
* mandatory   — at least ``expected_min_mandatory`` clauses flagged mandatory
* no-invention — every extracted clause is verbatim substring of the source
                 (the tool only splits; anything else means fabricated text)
"""

from __future__ import annotations

import re
from typing import Any

from ._util import tool_json


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def score_obligations(
    result: dict[str, Any], expected: dict[str, Any], source_text: str
) -> dict[str, Any]:
    obligations = tool_json(result).get("obligations", [])
    blob = _norm(" ".join(o.get("text", "") for o in obligations))
    norm_source = _norm(source_text)

    required_terms = expected.get("must_include_obligation_terms", [])
    found_terms = {t: (_norm(t) in blob) for t in required_terms}
    recall = (sum(found_terms.values()) / len(required_terms)) if required_terms else 1.0

    min_obligations = expected.get("expected_min_obligations", 1)
    count_ok = len(obligations) >= min_obligations

    min_mandatory = expected.get("expected_min_mandatory", 1)
    mandatory_count = sum(1 for o in obligations if o.get("is_mandatory"))
    mandatory_ok = mandatory_count >= min_mandatory

    # Integrity: the tool must not invent text — each clause is a substring of
    # the source (modulo whitespace + case normalization).
    no_invention = all(_norm(o.get("text", "")) in norm_source for o in obligations)

    return {
        "n_obligations": len(obligations),
        "mandatory_count": mandatory_count,
        "term_recall": round(recall, 3),
        "found_terms": found_terms,
        "count_ok": count_ok,
        "mandatory_ok": mandatory_ok,
        "no_invention": no_invention,
        "passed": bool(recall == 1.0 and count_ok and mandatory_ok and no_invention),
    }
