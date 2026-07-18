from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SPINE_CLASSES = {
    "spine",
    "decision",
    "scope",
    "authorization",
    "acceptance",
    "failure",
    "correction",
    "next_action",
}
BOUNDARY_CLASSES = {"SCOPE", "PROHIBITION", "DEFERRAL", "REJECTION"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def _turn_text(turn: dict[str, Any]) -> str:
    blocks = turn.get("content_blocks") or []
    parts: list[str] = []
    for block in blocks:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "\n".join(part for part in parts if part).strip()


def _validate_inputs(conversation: dict[str, Any], authority: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    conversation_id = str(conversation.get("conversation_id") or "").strip()
    if not conversation_id:
        raise ValueError("conversation_id is required")
    turns = conversation.get("turns")
    if not isinstance(turns, list) or not turns:
        raise ValueError("turns must be a non-empty list")

    turn_ids: set[str] = set()
    source_index: dict[str, dict[str, Any]] = {}
    for turn in turns:
        if not isinstance(turn, dict):
            raise ValueError("every turn must be an object")
        turn_id = str(turn.get("turn_id") or "").strip()
        if not turn_id or turn_id in turn_ids:
            raise ValueError("turn_id values must be present and unique")
        turn_ids.add(turn_id)
        refs = [str(ref) for ref in (turn.get("source_refs") or []) if str(ref).strip()]
        if not refs:
            raise ValueError(f"turn {turn_id} must retain at least one source_ref")
        text = _turn_text(turn)
        for ref in refs:
            if ref in source_index:
                raise ValueError(f"duplicate source_ref: {ref}")
            source_index[ref] = {
                "source_ref": ref,
                "conversation_id": conversation_id,
                "turn_id": turn_id,
                "ordinal": turn.get("ordinal"),
                "role": turn.get("role"),
                "text": text,
                "text_sha256": _sha256_text(text),
            }

    for key in ("structured_authority_ledger", "natural_language_review_queue", "assistant_non_authority_register"):
        rows = authority.get(key)
        if not isinstance(rows, list):
            raise ValueError(f"authority input requires list: {key}")
        for row in rows:
            refs = [str(ref) for ref in (row.get("source_refs") or []) if str(ref).strip()]
            if not refs:
                raise ValueError(f"authority row in {key} has no source_refs")
            missing = [ref for ref in refs if ref not in source_index]
            if missing:
                raise ValueError(f"authority row references unknown source_refs: {missing}")

    return turns, source_index


def _authority_by_ref(authority: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    canonical: dict[str, dict[str, Any]] = {}
    provisional: dict[str, dict[str, Any]] = {}
    for row in authority["structured_authority_ledger"]:
        for ref in row["source_refs"]:
            canonical[str(ref)] = row
    for row in authority["natural_language_review_queue"]:
        for ref in row["source_refs"]:
            provisional[str(ref)] = row
    return canonical, provisional


def _compose_spine(
    turns: list[dict[str, Any]],
    canonical_by_ref: dict[str, dict[str, Any]],
    provisional_by_ref: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for turn in sorted(turns, key=lambda row: (row.get("ordinal") is None, row.get("ordinal") or 0)):
        refs = [str(ref) for ref in turn.get("source_refs") or []]
        classes = {str(item).lower() for item in turn.get("classifications") or []}
        linked_canonical = next((canonical_by_ref[ref] for ref in refs if ref in canonical_by_ref), None)
        linked_provisional = next((provisional_by_ref[ref] for ref in refs if ref in provisional_by_ref), None)
        if not (classes & SPINE_CLASSES or linked_canonical or linked_provisional):
            continue

        text = _turn_text(turn)
        authority_status = "NON_AUTHORITY_SOURCE_EVENT"
        execution_status = "NOT_INFERRED"
        event_class = sorted(classes & SPINE_CLASSES)[0].upper() if classes & SPINE_CLASSES else "PROJECT_EVENT"
        if linked_canonical:
            authority_status = linked_canonical.get("authority_status", "CANONICAL_STRUCTURED_COMMAND")
            execution_status = linked_canonical.get("execution_status", "NOT_INFERRED")
            event_class = linked_canonical.get("decision_class", event_class)
        elif linked_provisional:
            authority_status = "PROVISIONAL_REVIEW"
            execution_status = linked_provisional.get("execution_status", "NOT_INFERRED")
            event_class = linked_provisional.get("decision_class", event_class)

        entries.append(
            {
                "spine_id": f"SPINE-{len(entries)+1:03d}",
                "turn_id": turn["turn_id"],
                "ordinal": turn.get("ordinal"),
                "event_class": event_class,
                "statement": text,
                "role": turn.get("role"),
                "authority_status": authority_status,
                "execution_status": execution_status,
                "source_refs": refs,
                "text_sha256": _sha256_text(text),
            }
        )

    return {
        "schema_version": "0.1.0",
        "entries": entries,
        "trust_boundary": {
            "assistant_statements_non_authoritative": True,
            "execution_not_inferred_from_command": True,
            "provisional_authority_not_promoted": True,
        },
    }


def _compose_continuation(
    conversation: dict[str, Any],
    turns: list[dict[str, Any]],
    authority: dict[str, Any],
) -> dict[str, Any]:
    canonical = authority["structured_authority_ledger"]
    provisional = authority["natural_language_review_queue"]
    accepted = [row for row in canonical if row.get("decision_class") == "ACCEPTANCE"]
    boundaries = [row for row in canonical + provisional if row.get("decision_class") in BOUNDARY_CLASSES]
    sorted_turns = sorted(turns, key=lambda row: (row.get("ordinal") is None, row.get("ordinal") or 0))
    last_turn = sorted_turns[-1]
    explicit_next = [
        turn
        for turn in sorted_turns
        if str(turn.get("role")).lower() == "user"
        and "next_action" in {str(item).lower() for item in turn.get("classifications") or []}
    ]
    next_turn = explicit_next[-1] if explicit_next else None

    return {
        "schema_version": "0.1.0",
        "conversation_id": conversation["conversation_id"],
        "accepted_baselines": accepted,
        "active_boundaries": boundaries,
        "unresolved_review_count": len(provisional),
        "current_return_point": {
            "turn_id": last_turn["turn_id"],
            "ordinal": last_turn.get("ordinal"),
            "source_refs": last_turn.get("source_refs") or [],
        },
        "next_action": (
            {
                "status": "EXPLICIT_SOURCE_ACTION",
                "statement": _turn_text(next_turn),
                "turn_id": next_turn["turn_id"],
                "source_refs": next_turn.get("source_refs") or [],
            }
            if next_turn
            else {"status": "NO_EXPLICIT_NEXT_ACTION_FOUND", "statement": None, "turn_id": None, "source_refs": []}
        ),
        "execution_boundary": {
            "completion_not_inferred": True,
            "evidenced_complete_entries": [
                row for row in canonical if row.get("execution_status") == "EVIDENCED_COMPLETE"
            ],
        },
    }


def _render_spine_markdown(spine: dict[str, Any], title: str) -> str:
    lines = [f"# {title} — Project Spine", ""]
    for row in spine["entries"]:
        lines.extend(
            [
                f"## {row['spine_id']} · {row['event_class']}",
                "",
                row["statement"] or "[No text content]",
                "",
                f"- Turn: `{row['turn_id']}`",
                f"- Authority: `{row['authority_status']}`",
                f"- Execution: `{row['execution_status']}`",
                f"- Source: {', '.join(f'`{ref}`' for ref in row['source_refs'])}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_continuation_markdown(brief: dict[str, Any], title: str) -> str:
    lines = [f"# {title} — Continuation Brief", ""]
    lines.extend(["## Return Point", "", f"Turn `{brief['current_return_point']['turn_id']}`.", ""])
    lines.extend(["## Next Action", ""])
    action = brief["next_action"]
    if action["statement"]:
        lines.extend([action["statement"], "", f"Source: {', '.join(f'`{ref}`' for ref in action['source_refs'])}", ""])
    else:
        lines.extend(["No explicit source-backed next action was found.", ""])
    lines.extend(["## Accepted Baselines", ""])
    if brief["accepted_baselines"]:
        lines.extend([f"- {row['statement']}" for row in brief["accepted_baselines"]])
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Active Boundaries", ""])
    if brief["active_boundaries"]:
        lines.extend([f"- **{row['decision_class']}** — {row['statement']}" for row in brief["active_boundaries"]])
    else:
        lines.append("- None recorded.")
    lines.extend(["", "## Trust Boundary", "", "Commands do not prove execution. Provisional authority remains under review.", ""])
    return "\n".join(lines)


def compose_artifacts(conversation: dict[str, Any], authority: dict[str, Any]) -> dict[str, Any]:
    turns, source_index = _validate_inputs(conversation, authority)
    canonical_by_ref, provisional_by_ref = _authority_by_ref(authority)
    title = str(conversation.get("title") or conversation["conversation_id"])
    spine = _compose_spine(turns, canonical_by_ref, provisional_by_ref)
    continuation = _compose_continuation(conversation, turns, authority)
    authority_ledger = {
        "schema_version": "0.1.0",
        "entries": authority["structured_authority_ledger"],
        "authority_boundary": authority.get("authority_boundary")
        or {
            "assistant_statements_non_authoritative": True,
            "execution_not_inferred_from_command": True,
        },
    }
    review_queue = {
        "schema_version": "0.1.0",
        "entries": authority["natural_language_review_queue"],
        "assistant_non_authority_register": authority["assistant_non_authority_register"],
    }
    source_trace = {
        "schema_version": "0.1.0",
        "coverage": "ARTIFACT_REFERENCED_SOURCE_TURNS",
        "source_turns": list(source_index.values()),
    }
    return {
        "title": title,
        "project_spine": spine,
        "project_spine_markdown": _render_spine_markdown(spine, title),
        "authority_ledger": authority_ledger,
        "authority_review_queue": review_queue,
        "continuation_brief": continuation,
        "continuation_brief_markdown": _render_continuation_markdown(continuation, title),
        "source_trace_index": source_trace,
    }


def write_artifact_package(
    composed: dict[str, Any],
    output_dir: Path,
    *,
    conversation_input: dict[str, Any],
    authority_input: dict[str, Any],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files: dict[str, bytes] = {
        "Project_Spine.json": _json_bytes(composed["project_spine"]),
        "Project_Spine.md": composed["project_spine_markdown"].encode("utf-8"),
        "Authority_Ledger.json": _json_bytes(composed["authority_ledger"]),
        "Authority_Review_Queue.json": _json_bytes(composed["authority_review_queue"]),
        "Continuation_Brief.json": _json_bytes(composed["continuation_brief"]),
        "Continuation_Brief.md": composed["continuation_brief_markdown"].encode("utf-8"),
        "Source_Trace_Index.json": _json_bytes(composed["source_trace_index"]),
    }
    for name, data in files.items():
        (output_dir / name).write_bytes(data)

    manifest = {
        "schema_version": "0.1.0",
        "package_type": "TKP_CONVERSATION_TO_ARTIFACT",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "conversation_id": conversation_input["conversation_id"],
        "input_sha256": {
            "normalized_conversation": _sha256_bytes(_json_bytes(conversation_input)),
            "authority_intelligence": _sha256_bytes(_json_bytes(authority_input)),
        },
        "artifacts": [
            {"path": name, "sha256": _sha256_bytes(data), "size_bytes": len(data)}
            for name, data in sorted(files.items())
        ],
        "trust_boundary": {
            "source_read_only": True,
            "assistant_authority_promoted": False,
            "provisional_authority_promoted": False,
            "execution_inferred": False,
        },
    }
    manifest_bytes = _json_bytes(manifest)
    (output_dir / "Manifest.json").write_bytes(manifest_bytes)
    files["Manifest.json"] = manifest_bytes

    checksum_lines = [f"{_sha256_bytes(data)}  {name}" for name, data in sorted(files.items())]
    checksums = "\n".join(checksum_lines) + "\n"
    (output_dir / "CHECKSUMS.sha256").write_text(checksums, encoding="utf-8")

    zip_path = output_dir / "TKP_Conversation_Artifact_Package.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(list(files) + ["CHECKSUMS.sha256"]):
            archive.write(output_dir / name, arcname=name)

    receipt = {
        "schema_version": "0.1.0",
        "status": "PASS",
        "conversation_id": conversation_input["conversation_id"],
        "artifact_count": len(files) + 1,
        "spine_entries": len(composed["project_spine"]["entries"]),
        "canonical_authority_entries": len(composed["authority_ledger"]["entries"]),
        "provisional_review_entries": len(composed["authority_review_queue"]["entries"]),
        "assistant_non_authority_entries": len(composed["authority_review_queue"]["assistant_non_authority_register"]),
        "explicit_next_action_found": composed["continuation_brief"]["next_action"]["status"] == "EXPLICIT_SOURCE_ACTION",
        "exceptions": 0,
        "zip_sha256": _sha256_bytes(zip_path.read_bytes()),
        "trust_boundary": manifest["trust_boundary"],
    }
    (output_dir / "Composition_Run_Receipt.json").write_bytes(_json_bytes(receipt))
    return receipt
