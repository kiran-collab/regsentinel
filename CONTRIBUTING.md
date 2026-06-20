# Contributing to RegSentinel

Thanks for your interest! This guide covers local setup and the checks your
change must pass.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,evals]"
pre-commit install        # run linters/formatters on every commit
```

## Day-to-day (via the Makefile)

```bash
make test        # pytest with coverage
make lint        # ruff check + format --check
make format      # ruff format + autofix
make type        # mypy
make evals       # deterministic unit + guardrail evals (no API key)
make security    # bandit + pip-audit
make check       # everything CI runs
```

## Standards

- **Style & types:** code is formatted and linted with `ruff` and type-checked
  with `mypy`; both gate CI. Public API ships type information (`py.typed`).
- **Tests:** add tests for new behavior. The deterministic core
  (`tools/`, `config.py`, hooks) is expected to stay near-fully covered; CI
  enforces a coverage floor.
- **Evals:** changes to agents, tools, or hooks should keep the deterministic
  eval layers green (`make evals`).
- **Commits:** keep messages imperative and scoped. Open a PR against `main`;
  CI (tests, coverage, lint, types, security) must be green and a CODEOWNER must
  approve before merge.

## Reproducible installs

Runtime deps are declared in `pyproject.toml`; `requirements.lock` pins exact,
hashed versions. Regenerate it after changing dependencies:

```bash
make lock        # pip-compile --generate-hashes
```
