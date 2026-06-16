"""Scorers for the RegSentinel eval pipeline.

Each scorer is a pure function: it takes a tool/agent output (and the case's
expected values) and returns a result dict that always contains a boolean
``passed`` key, plus per-criterion detail for debugging.

Scorers are intentionally INDEPENDENT of the implementation they grade — e.g.
``risk_scorer`` keeps its own copy of the risk matrix so that a regression in
``compliance_tools._RISK_MATRIX`` is caught rather than mirrored.
"""
