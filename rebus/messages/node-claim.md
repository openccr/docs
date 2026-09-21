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
manufacturer-programmed globally unique 64-bit identifier or a globally unique
write-once provisioned value; an unreadable, changed, or invalid identity must
remain unadmitted for the session.

This profile supersedes the original nine-byte source declaration, which
included `preferred_node_id` as a payload member. Firmware headers and
implementations must be synchronized with this profile before deployment.
