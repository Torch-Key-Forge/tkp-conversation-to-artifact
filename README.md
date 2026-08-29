# TKP Conversation-to-Artifact

**Turn reviewed conversation evidence into a portable, source-traceable project package without inventing new project truth.**

TKP Conversation-to-Artifact is the third public technical component in the Project Foreman recovery chain. It takes normalized conversation evidence plus reviewed authority intelligence and deterministically composes the project artifacts used by the Project Foreman recovery surface.

## Where it fits

```text
AI conversation export
        ↓
TKP Conversation Normalizer
        ↓
TKP Decision and Authority Intelligence
        ↓
TKP Conversation-to-Artifact
        ↓
Project Foreman workspace / recovery package
```

Related public components:

- [Project Foreman](https://github.com/Torch-Key-Forge/tkp-project-foreman) — the product-level recovery surface;
- [TKP Conversation Normalizer](https://github.com/Torch-Key-Forge/tkp-conversation-normalizer) — reconstructs and normalizes source conversation structure;
- [TKP Decision and Authority Intelligence](https://github.com/Torch-Key-Forge/tkp-decision-authority-intelligence) — separates operator authority from proposals and review candidates.

## Why it exists

A useful recovery product needs more than extracted facts. It needs a portable project representation that preserves where each claim came from, what authority state it carries, what remains unresolved, and what can be resumed safely.

This component performs that composition deterministically. It does not use the composition step to add new authority or silently resolve ambiguity.

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

## Fit and limitations

Use this component when the job is **deterministic composition of already-normalized, already-classified project evidence into a portable recovery package**.

It does not:

- acquire conversations;
- normalize raw exports;
- independently decide authority;
- resolve provisional review candidates;
- prove execution or completion;
- provide a general provider/target adapter framework;
- establish multi-target platform portability merely because its ZIP output is portable.

## Fastest first value

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

## Proof and evidence boundary

The included inputs are synthetic and sanitized. No private conversation corpus, account export, credentials, or private filesystem paths are included.

## Current release state

Current public release: **v0.1.0**, published July 19, 2026.

- Runnable standard-library Python package and CLI: yes
- Synthetic/sanitized public fixtures: yes
- Automated tests: yes
- Clean GitHub-hosted Windows verification on the release head: passed
- CLI composition and PASS receipt verification: passed
- Portable ZIP generation: passed
- Separate repository privacy-marker searches: recorded with no known matches
- Source mutation: no
- Authority promotion beyond upstream reviewed classification: no

See [PUBLICATION_READINESS.md](PUBLICATION_READINESS.md) and [WINDOWS_VERIFICATION_GATE.md](WINDOWS_VERIFICATION_GATE.md) for the bounded release evidence.

## Trust, support, and security

For ordinary usage questions and non-sensitive defects, see [SUPPORT.md](SUPPORT.md).

For sensitive-data and security-reporting guidance, see [SECURITY.md](SECURITY.md). The repository does not currently claim a dedicated private vulnerability-reporting channel.

## Product and portability boundary

This repository is a downstream **product component** for Project Foreman. It composes already-normalized conversation evidence and reviewed authority intelligence into a traceable project package.

The generated ZIP is portable as an artifact package. That does **not** by itself prove platform or provider portability of the underlying product family. This repository does not provide a general provider/target adapter framework and does not claim multi-target platform portability.

## License

Released under the MIT License. See `LICENSE`.
