"""RegSentinel evaluation pipeline.

Layered evals for the compliance system:

* unit      — deterministic MCP tools (risk matrix, citation, control map, obligations)
* guardrail — governance hooks (egress allowlist)
* agent     — each specialist subagent in isolation        (needs ANTHROPIC_API_KEY)
* e2e       — the full orchestrated audit workflow          (needs ANTHROPIC_API_KEY)

The unit and guardrail layers are fully deterministic and run in CI without an
API key. See evals/README.md.
"""
