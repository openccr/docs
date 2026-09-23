SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Node claim message

## Physical framing
**COMMON**

The selected profile gate applies before node-claim validation. A node claim
with a decoded length other than 8 is invalid in either profile. A receiver
MUST discard an invalid physical form or decoded length without a protocol
response.

### Classic CAN
**CLASSIC CAN**

The raw DLC is 8 and the decoded length is 8.

### CAN FD
**CAN FD**

`FDF=1` and the decoded length is 8. Spare CAN FD capacity MUST NOT extend
this fixed v0.1 layout.


## Payload
**COMMON**


`rebus_msg_node_claim_t` is an 8-byte declared payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 8 | `uint64_t` | immutable physical-MCU UUID |

```c
typedef struct {
    uint64_t hardware_uuid;
} rebus_msg_node_claim_t;
```

The UUID uses the canonical little-endian [wire encoding](../encoding.md):
`0x1122334455667788` is transmitted as `88 77 66 55 44 33 22 11`.

The 7-bit `preferred_node_id` is not in the payload. It is the current
commissioned candidate encoded in the CAN identifier as specified by the
[discovery lifecycle](../discovery/lifecycle.md#node-claim-lifecycle-boundary), and must be in `0x01–0x7F`; `0x00`
and CAN ID `0x280` are reserved.

The all-zero and all-one UUID values are invalid. A node must use a
manufacturer-programmed immutable 64-bit identity or a write-once provisioned
value; an unreadable, changed, or invalid identity must remain unadmitted for
the session. Hardware UUID uniqueness is outside the Rebus protocol's
manufacturing and provisioning scope; observed duplicate use is contained by
`UUID_COLLISION` as defined by [discovery identity](../discovery/identity.md#duplicate-uuid-detection).

The five-claim cooperative procedure in the [discovery lifecycle](../discovery/lifecycle.md#cooperative-claim-procedure) defines
the node-claim lifecycle. This frame has two transmission contexts:

1. a claim emitted by a node in `CLAIMING`, supplying identity for concurrent
   UUID arbitration and targeted rejection; or
2. an identity reminder emitted by a selected `ACTIVE` node in response to
   `WHO_ARE_YOU`.

Identity-reminder binding, classification, duplicate-UUID handling, and
non-ownership semantics are defined by the [discovery identity
specification](../discovery/identity.md#identity-query).

This profile supersedes the original nine-byte source declaration, which
included `preferred_node_id` as a payload member. Firmware headers and
implementations must be synchronized with this profile before deployment.
