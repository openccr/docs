SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# CLAIM_REJECT message

## Frame
**COMMON**

`CLAIM_REJECT` is a discovery-control rejection, not a node claim.

| Property | Rule |
|---|---|
| CAN identifier | `(0x02 << 7) | rejected_node_id` (`0x101–0x17F`) |
| Data bytes 0–7 | Rejected claimant `hardware_uuid`, little-endian `uint64_t` |

The selected profile gate applies before `CLAIM_REJECT` validation. A claim
rejection with a decoded length other than 8 is invalid in either profile. A
receiver MUST discard an invalid physical form or decoded length without a
protocol response.

The [active-owner rejection and recovery procedure](../discovery/lifecycle.md#active-owner-rejection-and-recovery)
owns rejection emission, matching, and claimant recovery. This document defines
the frame identifier and rejected-claimant UUID payload.

### Classic CAN
**CLASSIC CAN**

The raw DLC is 8 and the decoded length is 8.

### CAN FD
**CAN FD**

`FDF=1` and the decoded length is 8. Spare CAN FD capacity MUST NOT extend
this fixed v0.1 UUID layout.
