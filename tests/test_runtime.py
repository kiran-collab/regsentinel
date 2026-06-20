"""Tests for the runtime wiring that doesn't need a live model or network.

Covers the CLI argument contract, the audit-trail hook's write path, and the
orchestrator's option assembly — the deterministic parts of the agent runtime.
"""

import asyncio
import json

from regsentinel.cli import build_parser
from regsentinel.config import get_settings
from regsentinel.hooks import audit_tool_use
from regsentinel.orchestrator import build_options


def test_cli_parser_defaults_and_overrides():
    args = build_parser().parse_args([])
    assert args.regulations  # has a sensible default
    assert args.working_dir == "sample_data"

    args = build_parser().parse_args(["GDPR Article 30", "wd"])
    assert args.regulations == "GDPR Article 30"
    assert args.working_dir == "wd"


def test_audit_tool_use_appends_record(tmp_path, monkeypatch):
    monkeypatch.setenv("REGSENTINEL_AUDIT_LOG", str(tmp_path / "audit.jsonl"))
    get_settings.cache_clear()
    try:
        asyncio.run(
            audit_tool_use({"tool_name": "Read", "tool_input": {"file_path": "x"}}, "tid-1", None)
        )
        record = json.loads((tmp_path / "audit.jsonl").read_text().strip())
        assert record["tool"] == "Read"
        assert record["tool_use_id"] == "tid-1"
        assert record["input"] == {"file_path": "x"}
    finally:
        get_settings.cache_clear()


def test_build_options_wires_agents_and_least_privilege():
    opts = build_options("sample_data")
    assert "Agent" in opts.allowed_tools
    assert set(opts.agents) == {
        "regulation-researcher",
        "obligation-extractor",
        "control-mapper",
        "risk-assessor",
        "report-writer",
    }
    # only the researcher may touch the network
    assert opts.agents["regulation-researcher"].tools == ["WebSearch", "WebFetch"]
    assert "WebFetch" not in opts.agents["report-writer"].tools
    assert opts.max_turns == 60
