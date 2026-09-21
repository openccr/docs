# Rebus implementation guide

## Ownership and precedence

There is no global document-precedence chain. For each subject, the owning
document below is authoritative; a consumer document may only reference it.
`open-issues.md` is a deny-list: do not implement its items as defaults.

## Minimal read sets

| Task | Read | Skip unless needed |
|---|---|---|
| Encode/decode one message | `profile.md`, `encoding.md`, target message file | discovery |
| Node claim or address ownership | `profile.md`, `discovery.md`, `messages/node-claim.md` | telemetry/role |
| Confirmation, reclaim, reset | `profile.md`, `discovery.md`, `messages/claim-confirm.md`, `open-issues.md` | other payload catalogues |
| Role announcement | `profile.md`, `discovery.md`, `messages/role-announce.md` | telemetry |
| Telemetry | `profile.md`, `encoding.md`, `messages/telemetry.md`, `messages/role-announce.md` | discovery internals |
| Reboot/persistence | `discovery.md`, `design-decisions.md`, `open-issues.md` | message payloads |
| New control message | `profile.md`, `open-issues.md`, target message file | unrelated messages |

## Non-negotiable invariants

- Classic CAN 2.0A base data frames only; raw DLC 8.
- Node IDs are `0x01–0x7F`; `0x00` and `0x280` are invalid for claims.
- Decode role/telemetry only after current-session sender confirmation.
- Unknown/reserved encodings are discarded; never coerce or infer values.
- Never add compatibility aliases for superseded encodings.

## Document ownership

| Document | Owns |
|---|---|
| `profile.md` | frame gate, identifiers, capacity, commissioned admission |
| `discovery.md` | discovery states, claims, confirmation, timing |
| `encoding.md` | byte/bit order and payload serialization |
| `messages/*.md` | payloads and message-specific validation |
| `design-decisions.md` | non-normative rationale |
| `open-issues.md` | intentionally unspecified behavior |

When changing a rule, update its owner and referenced consumers in the same
change. Remove superseded prose; never introduce a second rule by override.
