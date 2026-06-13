# RegSentinel — Multi-Agent Regulatory Compliance Intelligence

> An orchestrator-led, multi-agent system that audits an organization's internal
> controls against **live** regulatory requirements — built on the
> [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview) with
> subagents, an in-process MCP server, governance hooks, and resumable sessions.

Compliance is a deliberately hard target for an agentic showcase: it is
high-stakes, it depends on **current** information (regulations change, so stale
model knowledge is a liability), it requires multi-step reasoning across
documents, and — crucially — every claim must be **verifiable**. That last
property is what most agent demos skip and what this project is designed around.

---

## What it does

Given a list of regulations (e.g. `"EU AI Act Article 9; GDPR Article 30"`) and
an organization's control inventory, RegSentinel runs a five-phase audit and
produces an auditable Markdown report with a prioritized risk register and a
citation appendix.

```
orchestrator  (delegates, never analyzes directly)
  │
  ├─▶ regulation-researcher   WebSearch / WebFetch   → fetch CURRENT verbatim clause text
  ├─▶ obligation-extractor    mcp: extract_obligations → split into atomic obligations
  ├─▶ control-mapper          Read/Grep + mcp: map_control → map obligations → controls
  ├─▶ risk-assessor           mcp: score_risk          → score every gap (fixed matrix)
  └─▶ report-writer           Write + mcp: verify_citation → compile final report
```

## Why these design choices (the interesting part)

This is built to demonstrate the patterns production agent teams care about, not
just "many agents calling an LLM."

**1. Orchestrator → subagent delegation.** The top-level agent owns the *plan*
and delegates each phase to a specialist via the SDK's `Agent` tool. Each
subagent has its own focused system prompt and toolset.

**2. Least privilege, applied to agents.** Only `regulation-researcher` can
touch the network; only `report-writer` can write files. No single subagent can
*both* fetch the web and write to disk — which bounds the blast radius of a
prompt-injection attack served from a fetched regulator page.

**3. Deterministic core via an in-process MCP server.** Risk scoring, clause
fingerprinting, control-mapping, and citation checks live in real, unit-tested
Python (`tools/compliance_tools.py`), exposed as MCP tools with
`create_sdk_mcp_server`. The model *decides* what to score; it never *invents*
the score. The risk band comes from a fixed likelihood × impact matrix, so
findings are reproducible and defensible.

**4. Citation integrity.** `verify_citation` confirms a quoted snippet actually
appears in the cited source before the report asserts it — the system is
structurally biased against fabricated findings.

**5. Governance hooks.** A `PreToolUse` hook enforces a domain allowlist on
every web fetch (egress guard); a `PostToolUse` hook writes a tamper-evident
`audit_trail.jsonl` of every tool call. This is the deterministic governance
layer reviewers in regulated industries look for.

**6. Resumable sessions.** The orchestrator captures the SDK session ID, so a
long audit can be paused and resumed with full context.

**7. Pluggable external MCP servers.** The in-process compliance server sits in
the same `mcp_servers` dict as any external one — the commented filesystem
server shows how to drop in Slack, Jira, or Confluence MCP servers unchanged.

## Project layout

```
regsentinel/
├── regsentinel/
│   ├── orchestrator.py          # entry point: wires agents, tools, hooks, MCP, sessions
│   ├── agents.py                # 5 specialized subagent definitions (least-privilege)
│   ├── hooks.py                 # egress guard + audit-trail governance hooks
│   └── tools/
│       └── compliance_tools.py  # in-process MCP server: deterministic domain logic
├── tests/test_compliance_tools.py   # unit tests for the auditable core (6 passing)
├── examples/run_audit.py
├── sample_data/controls_inventory.md
├── requirements.txt
└── pyproject.toml
```

## Quickstart

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...        # from https://platform.claude.com/

# run an audit
python -m regsentinel.orchestrator "EU AI Act Article 9; GDPR Article 30" sample_data

# run the deterministic-core tests
pytest -q
```

Output: `compliance_report.md` (the deliverable) and `audit_trail.jsonl` (the
governance log) in the working directory.

## Tech

Python 3.10+, `claude-agent-sdk` (the same harness that powers Claude Code),
the Model Context Protocol for tool integration. Model: Claude (Sonnet for
subagents; configurable).

## Notes & honest limitations

- `sample_data/controls_inventory.md` is illustrative; point the control-mapper
  at your real inventory (or a Confluence/Drive MCP server) for live use.
- The egress allowlist in `hooks.py` is intentionally small — extend it for the
  regulators you actually consult.
- This is a reference architecture, not legal advice; a human compliance officer
  signs off on findings.
