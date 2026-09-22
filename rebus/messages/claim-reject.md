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

The [active-owner rejection and recovery procedure](../discovery/lifecycle.md#active-owner-rejection-and-recovery)
owns rejection emission, matching, and claimant recovery. This document defines
the frame identifier and rejected-claimant UUID payload.
