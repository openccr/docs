SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# CLAIM_REJECT message

## Frame

`CLAIM_REJECT` is a discovery-control rejection, not a node claim.

| Property | Rule |
|---|---|
| CAN identifier | `(0x02 << 7) | rejected_node_id` (`0x101–0x17F`) |
| Frame form | Classic CAN 2.0A base data frame |
| DLC | 8 |
| Data bytes 0–7 | Rejected claimant `hardware_uuid`, little-endian `uint64_t` |

An active owner MUST send one rejection for every valid matching `NODE_CLAIM`.
Only a live claimant whose current candidate ID and UUID both match the frame
MUST act on it. Every other receiver MUST discard it. The frame uses normal CAN
retransmission; it is neither acceptance nor ownership confirmation.
