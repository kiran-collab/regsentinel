"""Nox sessions for multi-version testing and quality checks.

    nox            # run the default sessions
    nox -s tests   # test across installed Python versions
    nox -s lint type
"""

import nox

nox.options.sessions = ["tests", "lint", "type"]
PYTHONS = ["3.10", "3.11", "3.12", "3.13"]


@nox.session(python=PYTHONS)
def tests(session: nox.Session) -> None:
    session.install("-e", ".[dev,evals]")
    session.run("pytest", "-q", "--cov=regsentinel", "--cov-fail-under=80")


@nox.session
def lint(session: nox.Session) -> None:
    session.install("ruff")
    session.run("ruff", "check", "src", "tests", "evals")
    session.run("ruff", "format", "--check", "src", "tests", "evals")


@nox.session
def type(session: nox.Session) -> None:
    session.install("-e", ".[dev]")
    session.run("mypy", "src")
