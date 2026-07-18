# TKP Conversation-to-Artifact

A deterministic, source-traceable composer that turns normalized AI conversation evidence and reviewed authority intelligence into portable project artifacts.

This is a supporting technical project for [Project Foreman](https://github.com/Torch-Key-Forge/tkp-project-foreman).

## Pipeline position

```text
conversation export
→ TKP Conversation Normalizer
→ TKP Decision and Authority Intelligence
→ TKP Conversation-to-Artifact
→ Project Foreman workspace and export package
```

## Inputs

1. A normalized conversation with stable turn identities, roles, classifications, content blocks, and exact source references.
2. An authority-intelligence result containing:
   - canonical structured operator commands;
   - provisional natural-language review candidates;
   - assistant non-authority audit entries.

## Outputs

- `Project_Spine.json`
- `Project_Spine.md`
- `Authority_Ledger.json`
- `Authority_Review_Queue.json`
- `Continuation_Brief.json`
- `Continuation_Brief.md`
- `Source_Trace_Index.json`
- `Manifest.json`
- `CHECKSUMS.sha256`
- `TKP_Conversation_Artifact_Package.zip`
- `Composition_Run_Receipt.json`

## Trust model

The composer does not decide who has authority. It preserves the authority classification supplied by the upstream intelligence stage.

It never:

- promotes assistant statements to operator authority;
- promotes provisional natural-language candidates to canonical authority;
- treats a command as proof that execution occurred;
- mutates source inputs;
- invents a next action when no explicit source-backed action exists.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest -q

python -m tkp_conversation_to_artifact `
  .\fixtures\sanitized_normalized_conversation.json `
  .\fixtures\sanitized_authority_intelligence.json `
  .\public-output
```

## Public evidence boundary

The included inputs are synthetic and sanitized. No private conversation corpus, account export, credentials, or private filesystem paths are included.

## Status

`0.1.0-publication-candidate`

The candidate is runnable and locally tested. A tagged release waits for an anonymous Windows clone/install/fixture verification and final license acceptance.
