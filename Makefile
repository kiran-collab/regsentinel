.PHONY: install test lint format type evals security lock run check clean

install:  ## install the package with dev + eval extras and git hooks
	pip install -e ".[dev,evals]"
	pre-commit install

test:  ## run the test suite with coverage gate
	pytest -q --cov=regsentinel --cov-report=term-missing --cov-fail-under=80

lint:  ## lint + format check (no changes)
	ruff check src tests evals
	ruff format --check src tests evals

format:  ## auto-format and auto-fix lint issues
	ruff format src tests evals
	ruff check --fix src tests evals

type:  ## static type check
	mypy src

evals:  ## deterministic eval layers (no API key required)
	python -m evals.run_unit_evals
	python -m evals.run_guardrail_evals

security:  ## SAST + dependency vulnerability scan
	bandit -q -r src
	pip-audit

lock:  ## regenerate the hashed dependency lockfile
	pip-compile --quiet --generate-hashes --extra dev --extra evals \
		--output-file requirements.lock pyproject.toml

run:  ## run a sample audit (needs ANTHROPIC_API_KEY)
	regsentinel "EU AI Act Article 9; GDPR Article 30" sample_data

check: lint type test evals  ## everything CI gates

clean:  ## remove caches and coverage artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
