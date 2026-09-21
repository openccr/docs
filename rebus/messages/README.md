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
| Claim confirmation | UUID payload | 8 | `0x101–0x17F` |
| Role announce | `rebus_msg_role_announce_t` | 8 | `0x301–0x37F` |
| Telemetry | `openccr_telemetry_frame_t` | 8 | `0x381–0x3FF` |

- [Node claim](node-claim.md) — hardware identity payload.
- [Claim confirmation](claim-confirm.md) — UUID ownership assertion.
- [Role announce](role-announce.md) — capabilities and firmware metadata.
- [Telemetry](telemetry.md) — dynamic values, units, contexts, and tissue data.

Node claims and confirmations participate in the decentralized procedure
described in [discovery](../discovery.md). Rejection, reclaim, and session
reset remain separate unassigned control messages; they must not alter the
node-claim payload.
