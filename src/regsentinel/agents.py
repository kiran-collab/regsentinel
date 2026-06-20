"""
Subagent definitions for RegSentinel.

The orchestrator (the top-level `query`) delegates focused subtasks to these
specialized agents via the `Agent` tool. Each subagent gets a tightly scoped
toolset — least privilege applied to agents, not just users.

Design notes
------------
* `regulation_researcher` is the only agent allowed to touch the network
  (WebSearch / WebFetch). It pulls *current* regulatory text — critical because
  regulations change and stale training data is a liability in compliance.
* `obligation_extractor` and `control_mapper` are deterministic-leaning:
  they lean on the in-process compliance MCP tools rather than free-form reasoning.
* `risk_assessor` produces the scored register using the fixed risk matrix.
* `report_writer` has Write access to emit the final auditable artifact.

No single subagent can both fetch the web *and* write files, which bounds the
blast radius of prompt injection from a fetched regulator page.
"""

from claude_agent_sdk import AgentDefinition

from .config import get_settings
from .tools.compliance_tools import COMPLIANCE_TOOL_NAMES

EXTRACT, SCORE, VERIFY, MAP = COMPLIANCE_TOOL_NAMES

# Specialist model is configurable (REGSENTINEL_SUBAGENT_MODEL); resolved once.
_MODEL = get_settings().subagent_model


SUBAGENTS = {
    "regulation-researcher": AgentDefinition(
        description=(
            "Fetches the CURRENT authoritative text of a named regulation or "
            "standard from the open web. Use first, before any analysis, so the "
            "audit works against live requirements rather than stale knowledge."
        ),
        prompt=(
            "You are a regulatory research specialist. Given a regulation name "
            "(e.g. 'EU AI Act Article 9', 'SOC 2 CC6.1', 'GDPR Art. 30'), find "
            "the most recent authoritative source — prefer the official regulator "
            "or standards body over secondary commentary. Return the exact "
            "relevant clause text verbatim, the source URL, and the publication "
            "or last-amended date. If you cannot confirm currency, say so "
            "explicitly. Never paraphrase the binding text — downstream agents "
            "need the verbatim clause to verify citations."
        ),
        tools=["WebSearch", "WebFetch"],
        model=_MODEL,
    ),
    "obligation-extractor": AgentDefinition(
        description=(
            "Decomposes a block of regulatory text into discrete, fingerprinted "
            "obligations. Distinguishes mandatory ('shall'/'must') from advisory."
        ),
        prompt=(
            "You are an obligation extraction specialist. Use the "
            "extract_obligations tool to split regulatory text into atomic "
            "obligations. Do not invent obligations not present in the text. "
            "Return the structured list exactly as the tool produces it, then add "
            "a one-line plain-language restatement per mandatory obligation."
        ),
        tools=[EXTRACT],
        model=_MODEL,
    ),
    "control-mapper": AgentDefinition(
        description=(
            "Maps each regulatory obligation to the organization's internal "
            "controls (read from the provided controls inventory) and records "
            "coverage as full/partial/none."
        ),
        prompt=(
            "You are a controls-mapping specialist. Read the organization's "
            "control inventory from the working directory. For each obligation, "
            "decide whether an existing control provides full, partial, or no "
            "coverage, then record it with the map_control tool. Be conservative: "
            "if evidence of coverage is weak, mark 'partial', never 'full'. Cite "
            "the control ID you relied on in the rationale."
        ),
        tools=["Read", "Glob", "Grep", MAP],
        model=_MODEL,
    ),
    "risk-assessor": AgentDefinition(
        description=(
            "Scores every identified compliance gap with the fixed enterprise "
            "risk matrix and produces a prioritized risk register."
        ),
        prompt=(
            "You are a risk assessment specialist. For each gap (coverage != "
            "full), estimate likelihood and impact (each low/medium/high) with a "
            "brief justification, then call score_risk to obtain the official "
            "band. Never assign a band yourself — the matrix is authoritative. "
            "Sort the final register critical -> informational."
        ),
        tools=[SCORE],
        model=_MODEL,
    ),
    "report-writer": AgentDefinition(
        description=(
            "Compiles verified findings into a final Markdown compliance report "
            "with an executive summary, the risk register, and a full citation "
            "appendix."
        ),
        prompt=(
            "You are a compliance report writer. Before stating any finding, "
            "confirm it carries a verified citation (verify_citation was run "
            "upstream). Produce a Markdown report with: (1) executive summary, "
            "(2) prioritized risk register table, (3) per-obligation coverage, "
            "(4) citation appendix with source URLs and dates. Flag clearly any "
            "finding whose citation could NOT be verified. Write the file to "
            "'compliance_report.md'."
        ),
        tools=["Read", "Write", VERIFY],
        model=_MODEL,
    ),
}
