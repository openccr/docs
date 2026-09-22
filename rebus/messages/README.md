SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus messages

## Scope

Message identifiers, payload layouts, and message-specific registries. Wire
serialization rules are defined in [wire encoding](../encoding.md).

## Catalogue

| Message | Payload type | DLC | Status |
|---|---|---:|---|
| Node claim | `rebus_msg_node_claim_t` | 8 | `0x281–0x2FF` |
| Claim rejection | UUID payload | 8 | `0x101–0x17F` |
| UUID collision | `rebus_msg_uuid_collision_t` | 8 | `0x480` |
| Identity query | `rebus_msg_who_are_you_t` | 8 | `0x200` or `0x201–0x27F` |
| [Manifest query](inventory/transport.md#manifest-query) | `rebus_msg_manifest_query_t` | 8 | `0x081–0x0FF` |
| [Manifest advertise](inventory/transport.md#manifest-advertisement) | `rebus_msg_manifest_advertise_t` | 8 | `0x301–0x37F` |
| [Manifest transfer start](inventory/transport.md#manifest-transfer-start-and-chunks) | `rebus_msg_manifest_transfer_start_t` | 8 | `0x301–0x37F` |
| [Manifest chunk](inventory/transport.md#manifest-transfer-start-and-chunks) | `rebus_msg_manifest_chunk_t` | 8 | `0x301–0x37F` |
| [Scalar telemetry](telemetry/scalar.md) | `openccr_telemetry_frame_t` | 8 | `0x381–0x3FF` |
| [Structured snapshot chunk](telemetry/structured.md) | `rebus_msg_structured_snapshot_chunk_t` | 8 | `0x401–0x47F` |
| [Telemetry control request](telemetry/control.md) | `rebus_telemetry_control_request_t` | 8 | `0x181–0x1FF` |

- [Node claim](node-claim.md) — hardware identity payload.
- [WHO_ARE_YOU](who-are-you.md) — targeted or broadcast identity query.
- [UUID_COLLISION](uuid-collision.md) — bus-wide duplicate-UUID diagnostic.
- [Claim rejection](claim-reject.md) — targeted claimant rejection.
- [Inventory manifests](inventory/README.md) — manifest transport, content
  envelope, semantic resource model, and registry assignments.
- [Telemetry](telemetry/README.md) — scalar values, structured snapshots,
  value registries, control requests, and receiver-local subscriptions.

Node claims, collision diagnostics, and rejection participate in the
decentralized procedure described in [discovery](../discovery/README.md). Session
reset remains an unassigned control message; it must not alter the node-claim
payload.
