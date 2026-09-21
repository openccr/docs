SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Node claim message

## Payload

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
commissioned candidate encoded in the CAN identifier as specified by
[discovery](../discovery.md#node-claim), and must be in `0x01–0x7F`; `0x00`
and CAN ID `0x280` are reserved.

The all-zero and all-one UUID values are invalid. A node must use a
manufacturer-programmed immutable 64-bit identity or a write-once provisioned
value; an unreadable, changed, or invalid identity must remain unadmitted for
the session. Hardware UUID uniqueness is outside the Rebus protocol's
manufacturing and provisioning scope; observed duplicate use is contained by
`UUID_COLLISION` as defined by [discovery](../discovery.md#duplicate-uuid-detection).

The five-claim cooperative procedure in [discovery](../discovery.md) defines
the node-claim lifecycle. This frame has two transmission contexts:

1. a claim emitted by a node in `CLAIMING`, supplying identity for concurrent
   UUID arbitration and targeted rejection; or
2. an identity reminder emitted by a selected `ACTIVE` node in response to
   `WHO_ARE_YOU`.

An identity reminder MUST be used only to establish or refresh a UUID-to-node-ID
mapping and MUST be classified before duplicate-UUID detection when it is
correlated to the receiver's accepted `WHO_ARE_YOU` query. If a different UUID
was previously bound to that node ID, the current binding is replaced for
subsequent identity resolution. A correlated reminder carrying the receiver's
own UUID at its persisted last active node ID is the expected returning
identity and is not duplicate activity. A correlated reminder carrying the
receiver's own UUID at another node ID triggers `UUID_COLLISION`. An identity
reminder is not a claim, does not participate in UUID arbitration or counting,
and does not assign, confirm, renew, or change a node address.

This profile supersedes the original nine-byte source declaration, which
included `preferred_node_id` as a payload member. Firmware headers and
implementations must be synchronized with this profile before deployment.
