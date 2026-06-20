"""Command-line entry point for RegSentinel.

Thin layer over :func:`regsentinel.orchestrator.run_audit`: parse arguments,
configure logging, run the audit, and print the final report summary to stdout.

    regsentinel "EU AI Act Article 9; GDPR Article 30" sample_data
    python -m regsentinel "GDPR Article 30" sample_data
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence

from .config import configure_logging, get_settings
from .orchestrator import run_audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="regsentinel",
        description="Multi-agent regulatory compliance audit on the Claude Agent SDK.",
    )
    parser.add_argument(
        "regulations",
        nargs="?",
        default="EU AI Act Article 9; GDPR Article 30",
        help="Regulations to audit, e.g. 'EU AI Act Article 9; GDPR Article 30'.",
    )
    parser.add_argument(
        "working_dir",
        nargs="?",
        default="sample_data",
        help="Directory containing controls_inventory.md (and where outputs land).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    configure_logging(get_settings().log_level)
    args = build_parser().parse_args(argv)
    final = asyncio.run(run_audit(args.regulations, args.working_dir))
    if final:
        print(final)


if __name__ == "__main__":
    main()
