"""Agent-level evals: each specialist subagent, in isolation.

Instead of routing through the orchestrator, this runner promotes one subagent
definition to the top-level loop (its prompt + its least-privilege toolset + the
compliance MCP server + the governance hooks) and feeds it a single task. It then
reads the audit trail to confirm the agent used the tools it is supposed to use
(e.g. obligation-extractor must call extract_obligations; researcher must fetch
from an authoritative domain).

This isolates each agent's behaviour so a regression in one specialist doesn't
hide behind the others in an end-to-end run.

Requires ANTHROPIC_API_KEY (and network for the researcher case). Without a key
the runner SKIPS cleanly (exit 0).

Run:  python -m evals.run_agent_evals
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from regsentinel.agents import SUBAGENTS
from regsentinel.hooks import audit_tool_use, guard_egress
from regsentinel.tools.compliance_tools import build_compliance_server

from evals.scorers.trace_scorer import load_audit_trail

ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = Path(__file__).parent / "datasets" / "agent_cases.json"
RESULTS_PATH = Path(__file__).parent / "results" / "agent_eval_results.json"
AUDIT_PATH = ROOT / "audit_trail.jsonl"


def _tool_satisfied(spec: str, used: set[str]) -> bool:
    """A requirement is either an exact tool name or '__one_of__:a,b,c'."""
    if spec.startswith("__one_of__:"):
        options = spec.split(":", 1)[1].split(",")
        return any(o in used for o in options)
    return spec in used


async def _run_single_agent(agent_key: str, user_input: str, working_dir: str) -> None:
    """Promote one subagent to the top-level loop and run a single task."""
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, query

    agent = SUBAGENTS[agent_key]
    options = ClaudeAgentOptions(
        system_prompt=agent.prompt,
        cwd=str(ROOT / working_dir),
        allowed_tools=list(agent.tools),
        mcp_servers={"compliance": build_compliance_server()},
        hooks={
            "PreToolUse": [HookMatcher(matcher="WebFetch", hooks=[guard_egress])],
            "PostToolUse": [HookMatcher(matcher=None, hooks=[audit_tool_use])],
        },
        permission_mode="acceptEdits",
        model=agent.model,
        max_turns=20,
    )
    async for _ in query(prompt=user_input, options=options):
        pass


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    if AUDIT_PATH.exists():
        AUDIT_PATH.unlink()

    error = None
    try:
        asyncio.run(_run_single_agent(case["agent"], case["input"], case["working_dir"]))
    except Exception as exc:  # noqa: BLE001 — record, don't crash the suite
        error = f"{type(exc).__name__}: {exc}"

    records = load_audit_trail(AUDIT_PATH)
    used = {r.get("tool") for r in records}

    expected = case["expected"]
    tool_checks = {spec: _tool_satisfied(spec, used) for spec in expected.get("must_use_tools", [])}

    # For the researcher, every fetched URL host must be on the authoritative list.
    domain_ok = True
    auth_domains = expected.get("authoritative_domains")
    if auth_domains:
        fetched_hosts = [
            (r.get("input") or {}).get("url", "")
            for r in records if r.get("tool") in {"WebFetch", "WebSearch"}
        ]
        domain_ok = all(
            any(d in host for d in auth_domains)
            for host in fetched_hosts if host
        )

    passed = error is None and all(tool_checks.values()) and domain_ok
    return {
        "case_id": case["case_id"],
        "agent": case["agent"],
        "tools_used": sorted(t for t in used if t),
        "tool_checks": tool_checks,
        "authoritative_domain_ok": domain_ok,
        "error": error,
        "passed": passed,
    }


def run() -> dict[str, Any]:
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    results = [run_case(case) for case in dataset]
    passed = sum(1 for r in results if r["passed"])
    summary = {
        "layer": "agent",
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
        print("SKIP: agent evals need ANTHROPIC_API_KEY (live subagent runs).")
        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        RESULTS_PATH.write_text(
            json.dumps({"layer": "agent", "skipped": True, "reason": "no ANTHROPIC_API_KEY"}, indent=2),
            encoding="utf-8",
        )
        return

    summary = run()
    for r in summary["results"]:
        flag = "PASS" if r["passed"] else "FAIL"
        print(f"  [{flag}] {r['agent']:<22} {r['case_id']}")
    print(f"\nAgent evals: {summary['passed']}/{summary['total']} passed -> {RESULTS_PATH}")
    if not summary["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
