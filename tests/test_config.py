"""Tests for the pydantic-settings configuration layer.

These prove the env contract is validated (bad values fail fast) and that the
documented defaults hold — config is the one place a typo silently changes
governance behavior, so it gets its own coverage.
"""

import pytest
from pydantic import ValidationError

from regsentinel.config import DEFAULT_ALLOWED_FETCH_DOMAINS, Settings


def test_defaults():
    s = Settings()
    assert s.audit_log_path == "audit_trail.jsonl"
    assert s.subagent_model == "sonnet"
    assert s.max_turns == 60
    assert s.permission_mode == "acceptEdits"
    assert s.log_level == "INFO"
    assert s.allowed_fetch_domains == DEFAULT_ALLOWED_FETCH_DOMAINS


def test_domains_parsed_and_normalized():
    s = Settings(allowed_fetch_domains="EUR-Lex.europa.eu, Example.COM ,")
    assert s.allowed_fetch_domains == frozenset({"eur-lex.europa.eu", "example.com"})


def test_log_level_uppercased():
    assert Settings(log_level="debug").log_level == "DEBUG"


def test_rejects_non_positive_max_turns():
    with pytest.raises(ValidationError):
        Settings(max_turns=0)


def test_rejects_unknown_permission_mode():
    with pytest.raises(ValidationError):
        Settings(permission_mode="bogus")


def test_settings_is_immutable():
    s = Settings()
    with pytest.raises(ValidationError):
        s.max_turns = 5  # frozen model
