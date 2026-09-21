SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# UUID_COLLISION message

## Frame

`UUID_COLLISION` is a bus-wide duplicate-identity diagnostic. It is not an
addressed command, a claim, or a claim rejection.

| Property | Rule |
|---|---|
| CAN identifier | `0x480` (class `0x9`, broadcast diagnostic) |
| Frame form | Classic CAN 2.0A base data frame |
| DLC | 8 |
| Data bytes 0–7 | Conflicting `hardware_uuid`, little-endian `uint64_t` |

The low identifier bits are zero only because this diagnostic is broadcast;
`0x480` does not name node ID `0x00`. All other class-`0x9` identifiers remain
reserved in v0.1. Every node on the bus receives the frame; it has no unicast
target and does not require a response from unrelated nodes.

## Payload

`rebus_msg_uuid_collision_t` is the complete conflicting UUID:

```c
typedef struct {
    uint64_t hardware_uuid;
} rebus_msg_uuid_collision_t;
```

The UUID uses the canonical little-endian [wire encoding](../encoding.md).
All-zero and all-one UUID values are invalid. A receiver MUST discard a frame
with an invalid UUID or a failed profile frame gate without a protocol response.

## Report behavior

A node that detects duplicate activity for its own UUID emits one logical
`UUID_COLLISION` report using normal CAN retransmission, latches that it has
reported the collision for the boot/session, and follows the `IDENTITY_FAULT`
transition defined by [discovery](../discovery.md#duplicate-uuid-detection).

A node that receives a report carrying its own UUID emits one logical matching
report if it has not already reported during the boot/session, then follows the
same transition. A node with a different local UUID remains operational; its
interface-facing control plane MAY record and report the diagnostic.

A report is not an acknowledgement, ownership decision, or reset request.
Fixed application-level repetition and forwarding are not used. CAN controller
retransmission remains available for the logical emission.
