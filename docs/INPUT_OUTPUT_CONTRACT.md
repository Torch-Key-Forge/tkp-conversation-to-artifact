# Input and Output Contract

## Required normalized-conversation fields

- `conversation_id`
- non-empty `turns`
- unique `turn_id` values
- one or more exact `source_refs` per turn
- `role`, `ordinal`, `content_blocks`, and optional `classifications`

## Required authority-intelligence collections

- `structured_authority_ledger`
- `natural_language_review_queue`
- `assistant_non_authority_register`

Every authority record must reference a source turn present in the normalized conversation. Unknown references fail closed.

## Composition rules

- Project Spine entries are source-backed project events and authority evidence.
- Canonical authority remains canonical only when supplied as structured operator authority.
- Provisional authority stays in the review queue.
- Assistant statements remain in the non-authority audit register.
- Continuation next action comes only from an explicit user turn classified `next_action`.
- Execution remains `NOT_INFERRED` unless separate upstream evidence explicitly marks it complete.
