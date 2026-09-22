SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# WHO_ARE_YOU message

## Identifier and frame

`WHO_ARE_YOU` is a discovery identity query. It uses the class-`0x4` range,
which is separate from class `0x2` because `CLAIM_REJECT` uses an
undiscriminated eight-byte UUID payload.

| Query | CAN identifier | Meaning |
|---|---:|---|
| Specific | `(0x04 << 7) \| target_node_id` (`0x201–0x27F`) | Ask the active owner of one node ID |
| Broadcast | `0x200` | Ask every active node; low ID `0x00` is a query-only exception |

Every query is a Classic CAN 2.0A base-format data frame with raw DLC 8 and
exactly eight data bytes. `0x00` remains invalid as a node assignment, source
ID, or unicast destination. No other class-`0x4` payload is assigned in v0.1.

## Payload

`rebus_msg_who_are_you_t` is an eight-byte declared payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x01` for `WHO_ARE_YOU` |
| 1 | 1 | `uint8_t` | `requester_node_id`; `0x01–0x7F` |
| 2 | 6 | `uint8_t[6]` | Reserved; every byte must be zero |

```c
typedef struct {
    uint8_t message_type;
    uint8_t requester_node_id;
    uint8_t reserved[6];
} rebus_msg_who_are_you_t;
```

The requester ID identifies the querying node for correlation and local
request-rate handling. It does not authorize, allocate, or negotiate the
queried node ID. Multi-byte fields are absent; the payload still follows the
fixed-width [wire encoding](../encoding.md) and frame gate.

A receiver MUST discard a query with an invalid message type, requester ID,
nonzero reserved bytes, non-Classic-CAN frame form, or raw DLC other than 8.
Invalid queries receive no response.

## Response

For an accepted query, response selection, timing, and identity-reminder
semantics are defined by the [discovery identity
specification](../discovery/identity.md#identity-query). The response uses an
existing [node claim](node-claim.md) frame containing the responder's immutable
hardware UUID.
