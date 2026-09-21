SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Claim confirmation message

## Frame

`CLAIM_CONFIRM` is a discovery-control assertion, not a node claim.

| Property | Rule |
|---|---|
| CAN identifier | `(0x02 << 7) | subject_node_id` (`0x101–0x17F`) |
| Frame form | Classic CAN 2.0A base data frame |
| DLC | 8 |
| Data bytes 0–7 | Subject `hardware_uuid`, little-endian `uint64_t` |

`subject_node_id` must be in `0x01–0x7F`. The profile frame gate applies before
decoding. A receiver counts only remote valid frames after associating the ID
and UUID with its current local discovery-session generation.

## Confirmation evidence

A claimant emits this frame every 250 ms after its collision-observation
window. It becomes locally confirmed only after three successful
emissions spanning 500–750 ms. A receiver confirms the mapping only after
three remote valid assertions for the same local session, node ID, and UUID
spanning 500–750 ms. CAN ACK, transmit completion, and local loopback are not
remote evidence.

The wire profile assigns no session field to this payload. The future session
reset procedure must clear local generation and evidence state before a new
session is accepted; until then it is intentionally unresolved.
