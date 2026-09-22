# Rebus implementation guide

## Ownership and precedence

There is no global document-precedence chain. For each subject, the owning
document below is authoritative; a consumer document may only reference it.
`open-issues.md` is a deny-list: do not implement its items as defaults.

## Minimal read sets

These recipes are retrieval aids, not a precedence system. Normative files
identify their own authority and dependencies.

| Task | Required read set |
|---|---|
| Encode/decode a manifest transfer | `profile.md`, `encoding.md`, `messages/inventory/transport.md` |
| Validate manifest bytes | `encoding.md`, `messages/inventory/envelope.md`, `messages/inventory/registries.md` |
| Implement inventory resources or outputs | `messages/inventory/envelope.md`, `messages/inventory/model.md`, `messages/inventory/registries.md` |
| Implement scalar telemetry | `profile.md`, `encoding.md`, `messages/telemetry/scalar.md`, `messages/telemetry/registries.md`, `messages/inventory/model.md`, `messages/inventory/registries.md` |
| Implement structured telemetry | `profile.md`, `encoding.md`, `messages/telemetry/scalar.md`, `messages/telemetry/structured.md`, `messages/telemetry/registries.md`, `messages/inventory/model.md`, `messages/inventory/registries.md` |
| Implement telemetry control | `profile.md`, `encoding.md`, `messages/telemetry/control.md`, `messages/telemetry/registries.md`, `messages/inventory/model.md` |
| Implement claim lifecycle | `profile.md`, `discovery/README.md`, `discovery/lifecycle.md`, `messages/node-claim.md`, `messages/claim-reject.md` |
| Implement identity resolution | `profile.md`, `discovery/README.md`, `discovery/identity.md`, `messages/node-claim.md`, `messages/who-are-you.md`, `messages/uuid-collision.md` |
| Implement discovery end to end | `profile.md`, `encoding.md`, all discovery files, all four discovery message files |
| Implement subscriptions | `messages/telemetry/subscriptions.md`, `messages/telemetry/scalar.md`, `discovery/identity.md` |
| Implement inventory transport identity binding | `messages/inventory/transport.md`, `discovery/README.md`, `discovery/identity.md`, `profile.md` |
| Understand rationale or accepted limitations | `design-decisions.md` after the applicable normative files |

## Non-negotiable invariants

- Classic CAN 2.0A base data frames only; raw DLC 8.
- Node IDs are `0x01–0x7F`; `0x00` and `0x280` are invalid for claims.
- Decode manifest, telemetry, and control traffic directly from the frame's
  source or target ID after the frame gate and message-specific validation.
- Unknown/reserved encodings are discarded; never coerce or infer values.
- Never add compatibility aliases for superseded encodings.

## Document ownership

| Document | Owns |
|---|---|
| `profile.md` | frame gate, identifiers, capacity, commissioned admission |
| `discovery/README.md`, `discovery/lifecycle.md`, `discovery/identity.md` | discovery scope and navigation; claim lifecycle, ownership recovery, and persistence; identity queries, bindings, generation invalidation, and duplicate-UUID containment |
| `encoding.md` | byte/bit order and payload serialization |
| `messages/node-claim.md`, `messages/claim-reject.md`, `messages/who-are-you.md`, `messages/uuid-collision.md` | payloads and message-specific validation |
| `messages/inventory/transport.md` | manifest message lifecycle, transfer, cache identity, and active-session behavior |
| `messages/inventory/envelope.md` | canonical manifest header, record stream, and TLV framing |
| `messages/inventory/model.md` | resource, output, relation, parameter, and provenance semantics |
| `messages/inventory/registries.md` | assigned semantic values and registry-population contract |
| `messages/inventory/authoring.md` | non-normative YAML and contribution guidance |
| `messages/telemetry/scalar.md` | scalar frame acceptance, publisher identity, and scalar sequencing |
| `messages/telemetry/structured.md` | structured snapshot chunking, assembly, and snapshot sequencing |
| `messages/telemetry/registries.md` | scalar context, unit, and value-representation registries |
| `messages/telemetry/control.md` | telemetry-control requests and source scheduling |
| `messages/telemetry/subscriptions.md` | receiver-local subscription lifecycle |
| `design-decisions.md` | non-normative rationale |
| `open-issues.md` | intentionally unspecified behavior |

When changing a rule, update its owner and referenced consumers in the same
change. Remove superseded prose; never introduce a second rule by override.
