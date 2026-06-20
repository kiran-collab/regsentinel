"""Centralized, validated configuration for RegSentinel.

All runtime knobs are read from the environment with safe defaults and validated
by ``pydantic-settings`` — invalid values (an unknown permission mode, a
non-positive turn budget) fail fast at startup rather than deep inside an audit.
Import ``get_settings()`` rather than reading ``os.environ`` directly; it caches
a single immutable ``Settings`` instance.

Environment variables
---------------------
REGSENTINEL_AUDIT_LOG             path for the tamper-evident audit trail
REGSENTINEL_ALLOWED_FETCH_DOMAINS comma-separated egress allowlist (overrides default)
REGSENTINEL_SUBAGENT_MODEL        model id for the specialist subagents
REGSENTINEL_MAX_TURNS             orchestrator turn budget (> 0)
REGSENTINEL_PERMISSION_MODE       Claude Agent SDK permission mode
REGSENTINEL_LOG_LEVEL             logging level (DEBUG/INFO/WARNING/...)
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions", "dontAsk", "auto"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Domains the researcher subagent may fetch. In production this would come from a
# policy service; here it is a conservative default that env config can override.
DEFAULT_ALLOWED_FETCH_DOMAINS: frozenset[str] = frozenset(
    {
        "eur-lex.europa.eu",
        "gdpr.eu",
        "www.iso.org",
        "csrc.nist.gov",
        "www.federalregister.gov",
        "aicpa.org",
        "www.aicpa.org",
    }
)


class Settings(BaseSettings):
    """Immutable, validated runtime configuration sourced from the environment."""

    model_config = SettingsConfigDict(
        env_prefix="REGSENTINEL_",
        populate_by_name=True,
        frozen=True,
        extra="ignore",
    )

    audit_log_path: str = Field(
        "audit_trail.jsonl",
        validation_alias=AliasChoices("REGSENTINEL_AUDIT_LOG", "audit_log_path"),
    )
    allowed_fetch_domains: frozenset[str] = Field(
        DEFAULT_ALLOWED_FETCH_DOMAINS,
        validation_alias=AliasChoices("REGSENTINEL_ALLOWED_FETCH_DOMAINS", "allowed_fetch_domains"),
    )
    subagent_model: str = Field(
        "sonnet",
        validation_alias=AliasChoices("REGSENTINEL_SUBAGENT_MODEL", "subagent_model"),
    )
    max_turns: int = Field(
        60,
        gt=0,
        validation_alias=AliasChoices("REGSENTINEL_MAX_TURNS", "max_turns"),
    )
    permission_mode: PermissionMode = Field(
        "acceptEdits",
        validation_alias=AliasChoices("REGSENTINEL_PERMISSION_MODE", "permission_mode"),
    )
    log_level: LogLevel = Field(
        "INFO",
        validation_alias=AliasChoices("REGSENTINEL_LOG_LEVEL", "log_level"),
    )

    @field_validator("allowed_fetch_domains", mode="before")
    @classmethod
    def _parse_domains(cls, v: object) -> object:
        """Accept a comma-separated string from the environment."""
        if isinstance(v, str):
            return frozenset(d.strip().lower() for d in v.split(",") if d.strip())
        return v

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_level(cls, v: object) -> object:
        return v.upper() if isinstance(v, str) else v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, validated once from the environment."""
    return Settings()


def configure_logging(level: str | None = None) -> None:
    """Configure root logging once, in a CLI-friendly format.

    Idempotent: safe to call from the CLI entry point without double-handlers.
    """
    resolved = (level or get_settings().log_level).upper()
    logging.basicConfig(
        level=getattr(logging, resolved, logging.INFO),
        format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
