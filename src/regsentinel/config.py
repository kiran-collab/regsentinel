"""Centralized configuration for RegSentinel.

All runtime knobs are read from the environment with safe defaults, so the same
code runs locally, in CI, and in production without edits. Import ``get_settings()``
rather than reading ``os.environ`` directly — it caches a single immutable
``Settings`` instance and keeps the env-var contract in one place.

Environment variables
---------------------
REGSENTINEL_AUDIT_LOG             path for the tamper-evident audit trail
REGSENTINEL_ALLOWED_FETCH_DOMAINS comma-separated egress allowlist (overrides default)
REGSENTINEL_SUBAGENT_MODEL        model id for the specialist subagents
REGSENTINEL_MAX_TURNS             orchestrator turn budget
REGSENTINEL_PERMISSION_MODE       Claude Agent SDK permission mode
REGSENTINEL_LOG_LEVEL             logging level (DEBUG/INFO/WARNING/...)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache

# Domains the researcher subagent may fetch. In production this would come from a
# policy service; here it is a conservative default that env config can override.
DEFAULT_ALLOWED_FETCH_DOMAINS: frozenset[str] = frozenset({
    "eur-lex.europa.eu",
    "gdpr.eu",
    "www.iso.org",
    "csrc.nist.gov",
    "www.federalregister.gov",
    "aicpa.org",
    "www.aicpa.org",
})


@dataclass(frozen=True)
class Settings:
    """Immutable, fully-resolved runtime configuration."""

    audit_log_path: str
    allowed_fetch_domains: frozenset[str]
    subagent_model: str
    max_turns: int
    permission_mode: str
    log_level: str


def _parse_domains(raw: str | None) -> frozenset[str]:
    if not raw:
        return DEFAULT_ALLOWED_FETCH_DOMAINS
    return frozenset(d.strip().lower() for d in raw.split(",") if d.strip())


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, resolved once from the environment."""
    return Settings(
        audit_log_path=os.getenv("REGSENTINEL_AUDIT_LOG", "audit_trail.jsonl"),
        allowed_fetch_domains=_parse_domains(os.getenv("REGSENTINEL_ALLOWED_FETCH_DOMAINS")),
        subagent_model=os.getenv("REGSENTINEL_SUBAGENT_MODEL", "sonnet"),
        max_turns=int(os.getenv("REGSENTINEL_MAX_TURNS", "60")),
        permission_mode=os.getenv("REGSENTINEL_PERMISSION_MODE", "acceptEdits"),
        log_level=os.getenv("REGSENTINEL_LOG_LEVEL", "INFO"),
    )


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
