"""
RegSentinel orchestrator.

This is the entry point. It assembles the full agentic system:

    orchestrator (this query)
      ├─ regulation-researcher   (WebSearch / WebFetch, egress-guarded)
      ├─ obligation-extractor    (compliance MCP: extract_obligations)
      ├─ control-mapper          (Read/Grep + compliance MCP: map_control)
      ├─ risk-assessor           (compliance MCP: score_risk)
      └─ report-writer           (Write + compliance MCP: verify_citation)

Modern patterns demonstrated for the showcase:
  * Orchestrator -> subagent delegation via the `Agent` tool.
  * In-process MCP server for deterministic, auditable domain tools.
  * Optional external MCP servers (filesystem / Slack) wired the same way.
  * PreToolUse egress guard + PostToolUse audit log (governance hooks).
  * Session capture + resume for multi-phase, resumable audits.
  * Least-privilege tool scoping per subagent.

Run:  python -m regsentinel.orchestrator "EU AI Act Article 9; GDPR Article 30"
"""

from __future__ import annotations

import asyncio
import sys

from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    SystemMessage,
    query,
)

from .agents import SUBAGENTS
from .hooks import audit_tool_use, guard_egress
from .tools.compliance_tools import COMPLIANCE_TOOL_NAMES, build_compliance_server

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are RegSentinel, the orchestrator of a regulatory compliance audit.

You do NOT perform analysis yourself. You decompose the audit into phases and
delegate each phase to the correct specialist subagent via the Agent tool,
passing the prior phase's output forward. Run the phases in order:

1. regulation-researcher  -> fetch CURRENT verbatim text for each named reg.
2. obligation-extractor   -> split that text into atomic obligations.
3. control-mapper         -> map each obligation to internal controls.
4. risk-assessor          -> score every gap (coverage != full).
5. report-writer          -> compile the final compliance_report.md.

Rules:
- Never assert a finding without a verified citation.
- Never fabricate regulatory text; if research is inconclusive, say so.
- Keep each delegation tightly scoped to one phase.
At the end, summarize: # obligations, # gaps, and the highest risk band found.
"""


def build_options(working_dir: str) -> ClaudeAgentOptions:
    compliance_server = build_compliance_server()

    return ClaudeAgentOptions(
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        cwd=working_dir,
        # Orchestrator gets the Agent tool (to delegate) + read access to set up.
        # Subagents carry their own narrower toolsets (see agents.py).
        allowed_tools=[
            "Agent",
            "Read",
            "Glob",
            "Grep",
            "Write",
            "WebSearch",
            "WebFetch",
            *COMPLIANCE_TOOL_NAMES,
        ],
        agents=SUBAGENTS,
        mcp_servers={
            # In-process deterministic compliance tools.
            "compliance": compliance_server,
            # Example of an EXTERNAL MCP server wired in the same dict.
            # Uncomment to give the system real filesystem access via the
            # reference server, or swap for Slack/Jira/Confluence MCP servers.
            # "filesystem": {
            #     "type": "stdio",
            #     "command": "npx",
            #     "args": ["-y", "@modelcontextprotocol/server-filesystem", working_dir],
            # },
        },
        hooks={
            "PreToolUse": [HookMatcher(matcher="WebFetch", hooks=[guard_egress])],
            "PostToolUse": [HookMatcher(matcher=None, hooks=[audit_tool_use])],
        },
        permission_mode="acceptEdits",
        max_turns=60,
    )


async def run_audit(regulations: str, working_dir: str = ".") -> str | None:
    """Run a full compliance audit. Returns the orchestrator's final result text."""
    options = build_options(working_dir)
    prompt = (
        f"Run a full compliance audit for these regulations: {regulations}. "
        f"The organization's control inventory is in 'controls_inventory.md' in "
        f"the working directory. Follow your phased delegation process."
    )

    session_id: str | None = None
    final: str | None = None

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, SystemMessage) and message.subtype == "init":
            session_id = message.data.get("session_id")
            print(f"[session] {session_id}")
        elif isinstance(message, ResultMessage):
            final = message.result
            print("\n========== ORCHESTRATOR SUMMARY ==========")
            print(final)

    return final


def main() -> None:
    regs = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "EU AI Act Article 9; GDPR Article 30"
    )
    work = sys.argv[2] if len(sys.argv) > 2 else "sample_data"
    asyncio.run(run_audit(regs, work))


if __name__ == "__main__":
    main()
