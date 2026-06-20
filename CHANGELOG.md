# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Production tooling: CI quality gates (ruff, mypy, coverage), security scanning
  (Bandit, pip-audit, CodeQL, Dependabot), pinned GitHub Actions, a hashed
  dependency lockfile, `pre-commit`, `.editorconfig`, and a `Makefile`/`noxfile`.
- Governance docs: `LICENSE` (MIT), `SECURITY.md`, `CONTRIBUTING.md`,
  `CODEOWNERS`, this changelog, and issue/PR templates.
- `pydantic-settings`-based configuration with validation.
- Layered evaluation pipeline (`evals/`) and system architecture diagrams.

### Changed
- Refactored to a `src/` package layout with a `regsentinel` console entry point
  and structured logging.

## [0.1.0] - 2026-06-06

### Added
- Initial RegSentinel multi-agent compliance audit: orchestrator, five
  least-privilege subagents, in-process compliance MCP server, and governance
  hooks (egress guard + audit trail).
