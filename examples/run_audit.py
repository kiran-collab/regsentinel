"""Minimal programmatic entry point for the audit."""
import asyncio
from regsentinel.orchestrator import run_audit

if __name__ == "__main__":
    asyncio.run(run_audit(
        regulations="EU AI Act Article 9; GDPR Article 30",
        working_dir="sample_data",
    ))
