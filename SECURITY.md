# Security

## Data sensitivity

Composition inputs and outputs can contain private conversation evidence, authority records, client material, organizational decisions, or credentials. Use synthetic or sanitized fixtures for public reproduction and debugging.

Do not commit or post private conversation records, access tokens, credentials, local private paths, client data, or sensitive authority artifacts.

## Reporting

This repository does not currently publish a dedicated private vulnerability-reporting contact or claim a verified private security-reporting channel.

Do **not** disclose secrets, private source data, sensitive authority material, or exploit details in a public GitHub issue. Public issues may be used only for sanitized, non-sensitive security hardening questions that are safe to discuss openly.

A dedicated private reporting route remains a public-governance gap rather than a capability claimed by this repository.

## Trust-boundary safety

Security and correctness defects include behavior that could:

- promote assistant statements or provisional candidates to canonical authority;
- treat a command as proof of execution;
- mutate source inputs;
- fabricate a next action without source evidence;
- omit or corrupt source references, manifests, checksums, or receipt evidence.

## Current supported state

The current public release observed during the August 29, 2026 GitHub Estate Reconciliation is `v0.1.0` under the MIT License. GitHub-hosted Windows verification exists for the release head, including package generation and receipt checks.

That verification is not a claim of penetration testing, security certification, or suitability for processing secrets without appropriate operator controls.
