# Security Policy

## Reporting a vulnerability

Please report security issues **privately** — do not open a public issue.

- Use [GitHub Private Vulnerability Reporting](https://github.com/kiran-collab/regsentinel/security/advisories/new), or
- email the maintainer at **dkiran238@gmail.com** with the details and a proof of concept.

We aim to acknowledge reports within **3 business days** and to provide a
remediation timeline after triage. Please give us a reasonable window to fix the
issue before any public disclosure.

## Scope notes specific to RegSentinel

RegSentinel is an agentic system that fetches third-party regulatory content and
executes tools. When reporting, it is especially useful to flag:

- ways to bypass the **egress allowlist** (`guard_egress`) or reach non-allowlisted hosts;
- prompt-injection paths from fetched pages that lead a subagent to exceed its
  least-privilege toolset (e.g. a researcher writing files);
- gaps that let a finding be asserted **without** a verified citation;
- anything that causes the **audit trail** to be incomplete or forgeable.

## Supported versions

This project is pre-1.0; only the latest `main` is supported.
