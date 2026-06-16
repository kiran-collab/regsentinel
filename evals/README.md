# RegSentinel Evaluation Pipeline

A layered eval harness that answers one question:

> Did each agent perform its assigned compliance task correctly — with verified
> sources, deterministic risk scoring, safe tool use, and a final report a human
> compliance reviewer can trust?

## Layers

| Layer | Runner | API key? | What it checks |
|---|---|---|---|
| **unit** | `evals.run_unit_evals` | no | deterministic MCP tools: risk matrix, citation integrity, control mapping, obligation extraction |
| **guardrail** | `evals.run_guardrail_evals` | no | egress allowlist hook denies off-list domains, allows authoritative ones |
| **agent** | `evals.run_agent_evals` | yes | each specialist subagent, in isolation, uses its assigned tools |
| **e2e** | `evals.run_end_to_end_evals` | yes | full orchestrated audit: report sections, phase order, gap count |

`unit` and `guardrail` are pure Python — no model, no network — and gate every
push. `agent` and `e2e` run the live models and **skip cleanly (exit 0)** when
`ANTHROPIC_API_KEY` is unset.

## Run

```bash
pip install -r requirements.txt          # claude-agent-sdk + pytest
pip install pyyaml                        # for eval_config.yaml (optional)

# deterministic layers (no key needed)
python -m evals.run_unit_evals
python -m evals.run_guardrail_evals

# model-driven layers (needs ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-ant-...
python -m evals.run_agent_evals
python -m evals.run_end_to_end_evals

# roll up all result JSON into results/eval_summary.md
python -m evals.summarize

# the deterministic layers + scorers are also gated under pytest
pytest -q
```

## Layout

```
evals/
├── datasets/                     # versioned benchmark cases (golden + adversarial)
│   ├── golden_regulatory_cases.json   # full-audit cases (e2e)
│   ├── agent_cases.json               # per-subagent isolation cases
│   ├── adversarial_cases.json         # egress allow/deny URLs
│   ├── citation_cases.json            # valid vs fabricated citations
│   ├── control_mapping_cases.json     # coverage → gap derivation
│   ├── obligation_cases.json          # extraction precision/recall + no-invention
│   └── risk_matrix_cases.json         # all 9 cells + invalid input
├── scorers/                      # pure grading functions (independent oracles)
│   ├── _util.py                       # unwrap MCP content envelope
│   ├── risk_scorer.py                 # independent risk-matrix oracle
│   ├── citation_scorer.py
│   ├── control_mapping_scorer.py
│   ├── obligation_scorer.py
│   ├── report_scorer.py
│   └── trace_scorer.py                # audit-trail tool presence + phase order
├── run_unit_evals.py
├── run_guardrail_evals.py
├── run_agent_evals.py
├── run_end_to_end_evals.py
├── summarize.py
├── eval_config.yaml
└── results/                      # generated artifacts (git-ignored)
```

## Design notes

- **Scorers are independent oracles.** `risk_scorer` keeps its own copy of the
  likelihood × impact matrix rather than importing
  `compliance_tools._RISK_MATRIX`, so a regression in the tool's matrix is
  *caught*, not mirrored. `test_evals.py` proves the oracle fails a mis-scored
  cell.
- **The audit trail is the test fixture.** The PostToolUse hook already writes
  `audit_trail.jsonl`; the trace scorer turns it into a regression signal for
  tool usage and phase ordering — governance instrumentation doubling as an
  eval substrate.
- **Integrity over fluency.** The obligation scorer verifies every extracted
  clause is a verbatim substring of the source (no invented obligations); the
  report scorer is a deterministic floor, with qualitative LLM-as-judge grading
  left as the optional next layer.
