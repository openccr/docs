SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Structured telemetry snapshots

## Snapshot chunks

Structured outputs declared by the [inventory manifest](../inventory/model.md)
use `CAN_ID = (0x08 << 7) | source_node_id` (`0x401–0x47F`). This class is
deliberately lower arbitration priority than scalar telemetry. A structured
snapshot chunk is an eight-byte payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `publisher_id` |
| 1 | 1 | `uint8_t` | `snapshot_sequence`; source-local generation |
| 2 | 1 | `uint8_t` | `chunk_index`; zero-based |
| 3 | 1 | `uint8_t` | `chunk_count`; `1..255` |
| 4 | 4 | `uint8_t[4]` | Logical snapshot bytes at this chunk offset |

`chunk_index` MUST be less than `chunk_count`. The maximum logical snapshot
length is 1,020 bytes. The inventory output descriptor supplies the exact
encoded length, shape, element type, and dimension semantics. Unused bytes in
the final four-byte chunk MUST be zero and are not part of the logical value.

The logical snapshot begins with a four-byte snapshot header:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | Snapshot format; `0x01` |
| 1 | 1 | `uint8_t` | Status flags; same valid/warning/alarm bits as scalar telemetry |
| 2 | 2 | `uint16_t` | Reserved; must be zero |

The status bits are defined by [scalar telemetry](scalar.md#publisher-identity-and-status).

## Assembly, sequencing, and reset boundaries

`sequence_id` and `snapshot_sequence` are independent. A source increments
`snapshot_sequence` exactly once when it generates a new logical snapshot;
every chunk of that snapshot carries the same value. The source MUST increment
it modulo 256, including the `0xFF` to `0x00` wrap, and MUST NOT reset it or
reuse a value except as required by that modulo wrap within the same active
identity generation. Reusing sequence zero is otherwise permitted only at the
active-entry reset or after a UUID-binding reset.

For each structured stream, a receiver tracks the last committed sequence and
at most one pending assembly. If neither exists, the first valid chunk starts a
pending baseline and the first complete valid snapshot is accepted regardless
of its sequence. If a pending assembly exists, a chunk with its sequence may
arrive in any order. A different sequence is compared against the pending
sequence with `advance = received - pending` as `uint8_t`, using the
[shared modulo ordering](scalar.md#scalar-sequencing-and-reset-boundaries): a
newer result supersedes the pending assembly, a duplicate result is discarded,
and a stale result is discarded. After a snapshot is committed, the
same comparison is made against the last committed sequence. Sequence state
advances only when all chunks pass validation and the snapshot is committed.
This makes a completed snapshot authoritative without exposing a partial value
or allowing late chunks from an older snapshot to roll state back.

A valid manifest advertisement clears the committed sequence and any pending
assembly, and a discovery UUID remap does the same for the prior identity
generation. Silence does not clear this state. The shared ordering is
unambiguous only within its defined forward distance of 127 snapshots; v0.1
has no separate structured-snapshot reset message.

## Complete snapshot validation

A receiver MUST commit a structured snapshot only after every chunk for one
`(source_node_id, publisher_id, snapshot_sequence)` has arrived and the
assembled length, format, element representation, and shape match the active
publisher descriptor in the verified manifest. It MUST accept chunks in any
order, but MUST NOT commit an incomplete snapshot and MUST discard a
conflicting duplicate chunk or a snapshot whose sequence is duplicate or stale
under the ordering rule above. A newer sequence supersedes and discards an
incomplete older snapshot. It MUST NOT expose a partially assembled matrix or
array as current state.

## Requests and retransmission

Structured snapshots have no application-level retransmission or negative
acknowledgement. CAN controller error recovery remains subject to the normal
physical-frame retransmission rules. A receiver that misses or discards a
snapshot may issue a current-state request; the source produces a new snapshot
if its delivery policy permits and MUST NOT replay the missing historical
snapshot. A response that is a new logical snapshot receives the next
`snapshot_sequence`; all chunks in the response retain that value.

A structured snapshot request and its response are rate-limited according to
the output's manifest `delivery_class` and request policy. A source MAY defer,
coalesce, or silently ignore requests, especially for advisory or diagnostic
outputs. Request wire behavior and source scheduling are defined in
[telemetry control](control.md).
