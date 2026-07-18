from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from tkp_conversation_to_artifact.composer import compose_artifacts, write_artifact_package

ROOT = Path(__file__).resolve().parents[1]


def load_inputs():
    conversation = json.loads((ROOT / "fixtures" / "sanitized_normalized_conversation.json").read_text(encoding="utf-8"))
    authority = json.loads((ROOT / "fixtures" / "sanitized_authority_intelligence.json").read_text(encoding="utf-8"))
    return conversation, authority


def test_canonical_authority_is_preserved_without_provisional_promotion():
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    assert len(result["authority_ledger"]["entries"]) == 3
    assert len(result["authority_review_queue"]["entries"]) == 3
    assert all(row["authority_status"] == "CANONICAL_STRUCTURED_COMMAND" for row in result["authority_ledger"]["entries"])


def test_assistant_non_authority_is_not_promoted():
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    canonical_statements = {row["statement"] for row in result["authority_ledger"]["entries"]}
    assert "ACCEPT_ATLAS_LOCAL_ARTIFACT_BASELINE" not in canonical_statements
    assert len(result["authority_review_queue"]["assistant_non_authority_register"]) == 2


def test_spine_entries_retain_source_refs_and_hashes():
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    entries = result["project_spine"]["entries"]
    assert entries
    assert all(row["source_refs"] for row in entries)
    assert all(len(row["text_sha256"]) == 64 for row in entries)


def test_explicit_next_action_is_used_exactly():
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    action = result["continuation_brief"]["next_action"]
    assert action["status"] == "EXPLICIT_SOURCE_ACTION"
    assert action["turn_id"] == "TURN-0011"
    assert action["statement"].startswith("Next action:")


def test_completion_is_not_inferred():
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    assert result["continuation_brief"]["execution_boundary"]["completion_not_inferred"] is True
    assert result["continuation_brief"]["execution_boundary"]["evidenced_complete_entries"] == []
    assert all(row["execution_status"] == "NOT_INFERRED" for row in result["authority_ledger"]["entries"])


def test_source_trace_covers_every_turn():
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    rows = result["source_trace_index"]["source_turns"]
    assert len(rows) == len(conversation["turns"])
    assert len({row["source_ref"] for row in rows}) == len(rows)


def test_package_contains_manifest_checksums_and_zip(tmp_path):
    conversation, authority = load_inputs()
    result = compose_artifacts(conversation, authority)
    receipt = write_artifact_package(result, tmp_path, conversation_input=conversation, authority_input=authority)
    assert receipt["status"] == "PASS"
    assert receipt["artifact_count"] == 9
    assert (tmp_path / "Manifest.json").exists()
    assert (tmp_path / "CHECKSUMS.sha256").exists()
    zip_path = tmp_path / "TKP_Conversation_Artifact_Package.zip"
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
    assert "Project_Spine.json" in names
    assert "Continuation_Brief.md" in names
    assert "CHECKSUMS.sha256" in names


def test_unknown_authority_source_ref_fails_closed():
    conversation, authority = load_inputs()
    authority["structured_authority_ledger"][0]["source_refs"] = ["SRC-MISSING"]
    with pytest.raises(ValueError, match="unknown source_refs"):
        compose_artifacts(conversation, authority)
