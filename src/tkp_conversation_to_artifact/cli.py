from __future__ import annotations

import argparse
import json
from pathlib import Path

from .composer import compose_artifacts, write_artifact_package


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compose traceable project artifacts from normalized conversation evidence.")
    parser.add_argument("conversation", type=Path, help="Normalized conversation JSON")
    parser.add_argument("authority", type=Path, help="Decision and authority intelligence JSON")
    parser.add_argument("output", type=Path, help="Output directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    conversation = json.loads(args.conversation.read_text(encoding="utf-8"))
    authority = json.loads(args.authority.read_text(encoding="utf-8"))
    composed = compose_artifacts(conversation, authority)
    receipt = write_artifact_package(
        composed,
        args.output,
        conversation_input=conversation,
        authority_input=authority,
    )
    print(
        "PASS: "
        f"{receipt['spine_entries']} spine entries, "
        f"{receipt['canonical_authority_entries']} canonical authority entries, "
        f"{receipt['provisional_review_entries']} review entries, "
        f"next action={receipt['explicit_next_action_found']}"
    )
    return 0
