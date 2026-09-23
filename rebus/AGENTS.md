# Rebus implementation guide

## Ownership, precedence, and applicability

This guide is non-normative navigation. Each subject has one authoritative
owner below; consumer documents link to that owner rather than restating its
rules. `missing-functionality.md` is a deny-list: none of its unspecified
contracts is an implementation default. `open-issues.md` records defects in
rules that are already specified; it does not override those rules.

### Applicability legend

- **COMMON** — a logical rule that applies identically after the selected
  profile's physical gate.
- **CLASSIC CAN** — a rule limited to `REBUS_CLASSIC_0_1`.
- **CAN FD** — a rule limited to `REBUS_FD_0_1`.

The markers in a normative owner identify the applicable scope. They do not
make a frame from one selected profile admissible under the other.

Normative owners MUST mark each completed rule **COMMON**, **CLASSIC CAN**, or
**CAN FD** at the scope where it applies. When a function depends on the
selected profile, its owner MUST provide two sibling, explicitly labeled
chapters, one for Classic CAN and one for CAN FD; do not hide a profile variant
in a common chapter or omit a profile because it inherits a common rule.
Profile-independent behavior belongs in a **COMMON** chapter or marked block.
The selected-profile gate still precedes all message-specific rules.

## Spec naming

Use the `rebus_` prefix, not `openccr_`, for illustrative C identifiers and
Rebus payload type names defined in these specifications. Retain `openccr_`
when citing actual upstream headers or identifiers rather than naming a
Rebus declaration.

## Minimal read sets

These recipes are retrieval aids, not a precedence system. Normative files
identify their own authority and dependencies.

| Task | Required read set |
|---|---|
| Encode/decode a manifest transfer | `profile.md`, `encoding.md`, `messages/inventory/transport.md` |
| Validate manifest bytes received in a transfer | `profile.md`, `encoding.md`, `messages/inventory/transport.md`, `messages/inventory/envelope.md`, `messages/inventory/registries.md` |
| Implement inventory resources or outputs | `profile.md`, `messages/inventory/envelope.md`, `messages/inventory/model.md`, `messages/inventory/registries.md` |
| Implement scalar telemetry | `profile.md`, `encoding.md`, `messages/telemetry/scalar.md`, `messages/telemetry/registries.md`, `messages/inventory/model.md`, `messages/inventory/registries.md` |
| Implement structured telemetry | `profile.md`, `encoding.md`, `messages/telemetry/scalar.md`, `messages/telemetry/structured.md`, `messages/telemetry/registries.md`, `messages/inventory/model.md`, `messages/inventory/registries.md` |
| Implement telemetry control | `profile.md`, `encoding.md`, `messages/telemetry/control.md`, `messages/telemetry/registries.md`, `messages/inventory/model.md` |
| Implement claim lifecycle | `profile.md`, `encoding.md`, `discovery/README.md`, `discovery/lifecycle.md`, `messages/node-claim.md`, `messages/claim-reject.md` |
| Implement identity resolution | `profile.md`, `encoding.md`, `discovery/README.md`, `discovery/identity.md`, `messages/node-claim.md`, `messages/who-are-you.md`, `messages/uuid-collision.md` |
| Implement discovery end to end | `profile.md`, `encoding.md`, all discovery files, all four discovery message files |
| Implement subscriptions | `profile.md`, `encoding.md`, `messages/telemetry/subscriptions.md`, `messages/telemetry/scalar.md`, `discovery/identity.md` |
| Implement inventory transport identity binding | `profile.md`, `encoding.md`, `messages/inventory/transport.md`, `discovery/README.md`, `discovery/identity.md` |
| Understand rationale or accepted limitations | `design-decisions.md` after the applicable normative files |

## Non-negotiable invariants

- Before physical framing work, read `profile.md`, then `encoding.md`, then the
  applicable message or lifecycle owner. `profile.md` owns selected-profile
  admission; `encoding.md` owns decoded payload serialization and FD DLC
  mapping; the final owner applies its post-gate validation.
- Read `profile.md` for identifier, sender, admission, and capacity rules;
  read the relevant discovery or message owner for its logical state and
  payload rules.
- Treat `missing-functionality.md` as the deny-list for unspecified contracts.
  Its subjects have no implied **COMMON**, **CLASSIC CAN**, or **CAN FD** behavior;
  consult `open-issues.md` for defects in the completed specification.

## Document ownership

| Document | Owns |
|---|---|
| `profile.md` | selected profile, frame gate, identifiers, capacity, commissioned admission |
| `discovery/README.md`, `discovery/lifecycle.md`, `discovery/identity.md` | discovery scope and navigation; claim lifecycle, ownership recovery, and persistence; identity queries, bindings, generation invalidation, and duplicate-UUID containment |
| `encoding.md` | byte/bit order, raw-FD-DLC mapping, and profile-aware payload serialization |
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
| `missing-functionality.md` | referenced contracts not yet specified; no defaults |
| `open-issues.md` | evidence-backed issues in completed rules |

When changing a rule, update its owner and referenced consumers in the same
change. Remove superseded prose; never introduce a second rule by override.
