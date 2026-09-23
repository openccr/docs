SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Structured telemetry snapshots
**COMMON**


## Snapshot chunks

**COMMON**

Structured outputs declared by the [inventory manifest](../inventory/model.md)
use `CAN_ID = (0x08 << 7) | source_node_id` (`0x401–0x47F`). This class is
deliberately lower arbitration priority than scalar telemetry. A snapshot chunk
has this four-byte transfer header followed by a profile-specific data area:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `publisher_id` |
| 1 | 1 | `uint8_t` | `snapshot_sequence`; source-local generation |
| 2 | 1 | `uint8_t` | `chunk_index`; zero-based |
| 3 | 1 | `uint8_t` | `chunk_count`; `1..255` |
| 4 | `D` | `uint8_t[D]` | Logical snapshot bytes at this chunk offset |

`chunk_index` MUST be less than `chunk_count`. A receiver MUST discard an
out-of-range chunk without altering the pending assembly or sequence state.

After the selected [profile frame gate](../../profile.md), the chunk geometry
below selects the decoded length `L` and data-area length `D`. These
decoded-length requirements are applied only after the selected profile gate;
receivers MUST NOT infer a profile from a chunk.

For descriptor encoded length `encoded_length`, a sender MUST set
`chunk_count = ceil(encoded_length / D)`, and a receiver MUST require that
value before assembly. The descriptor bound is therefore `chunk_count <= 255`;
the table's maximum encoded lengths are `255 * D`. `encoded_length` includes
the mandatory four-byte logical snapshot header and MUST be at least four.
The transfer header alone does not establish a snapshot length. The inventory
output descriptor supplies that exact length, shape, element type, and
dimension semantics. A final partial data area is zero-padded; a receiver MUST
reject nonzero final padding, which is not part of the logical value.

The logical snapshot begins with a four-byte snapshot header:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | Snapshot format; `0x01` |
| 1 | 1 | `uint8_t` | Status flags; same valid/warning/alarm bits as scalar telemetry |
| 2 | 2 | `uint16_t` | Reserved; must be zero |

The status bits are defined by [scalar telemetry](scalar.md#publisher-identity-and-status).

Before accepting a chunk into an assembly, a receiver MUST have the active
verified manifest and matching output descriptor required by
[scalar telemetry](scalar.md#manifest-binding-and-descriptor-acceptance).
Invalid, unbound, or descriptor-mismatched chunks MUST NOT create an assembly,
advance snapshot state, or establish a baseline.

### Chunk geometry

#### Classic CAN

**CLASSIC CAN**

| Decoded length `L` | Data area `D = L - 4` | Maximum descriptor encoded length |
|---:|---:|---:|
| 8 | 4 | 1,020 |

Classic chunks require raw DLC 8 and decoded length 8.

#### CAN FD

**CAN FD**

| Decoded length `L` | Data area `D = L - 4` | Maximum descriptor encoded length |
|---:|---:|---:|
| 8 | 4 | 1,020 |
| 12 | 8 | 2,040 |
| 16 | 12 | 3,060 |
| 20 | 16 | 4,080 |
| 24 | 20 | 5,100 |
| 32 | 28 | 7,140 |
| 48 | 44 | 11,220 |
| 64 | 60 | 15,300 |

An FD snapshot's first accepted chunk pins one permitted decoded length `L`
from the table and its data area `D = L - 4` for that pending assembly. Every
later chunk for that assembly MUST use the pinned decoded length; a mismatch is
discarded and MUST NOT alter the assembly or sequence state. A sender MUST use
the same selected `L` for every chunk of one snapshot.

## Assembly, sequencing, and reset boundaries

`sequence_id` and `snapshot_sequence` are independent. A source increments
`snapshot_sequence` exactly once when it generates a new logical snapshot;
every chunk of that snapshot carries the same value. The source MUST increment
it modulo 256, including the `0xFF` to `0x00` wrap, and MUST NOT reset it or
reuse a value except as required by that modulo wrap within the same active
identity generation. Reusing sequence zero is otherwise permitted only at the
active-entry reset or after a UUID-binding reset.

For each structured stream, a receiver tracks the last committed sequence and
at most one pending assembly. After the frame and descriptor gates, it MUST
apply these checks to each valid chunk in order:

1. If a last committed sequence exists, compare `received - committed` as
   `uint8_t` using the
   [shared modulo ordering](scalar.md#scalar-sequencing-and-reset-boundaries).
   Discard `0` (duplicate) or `128..255` (stale) without changing the pending
   assembly or committed sequence. This check precedes any pending replacement.
2. If a pending assembly has the received sequence, accept its chunk in any
   index order. If the sequences differ, compare `received - pending` as
   `uint8_t`; only `1..127` supersedes the pending assembly and starts a new
   one. Discard `128..255` without changing state. If no assembly is pending,
   start one for the received sequence.

Without a committed sequence, the first valid chunk starts a pending baseline,
and the first complete valid snapshot is accepted regardless of its sequence.
The last committed sequence advances only when all chunks pass validation and
the snapshot is committed. A completed snapshot remains authoritative without
exposing a partial value or allowing late chunks to roll state back.

A valid manifest advertisement clears the committed sequence and any pending
assembly, and a discovery UUID remap does the same for the prior identity
generation. Silence does not clear this state. The shared ordering is
unambiguous only within its defined forward distance of 127 snapshots; v0.1
has no separate structured-snapshot reset message.

## Complete snapshot validation

A receiver MUST commit a structured snapshot only after every chunk index from
zero through `chunk_count - 1` for one
`(source_node_id, publisher_id, snapshot_sequence)` has arrived, the
`chunk_count` equals `ceil(encoded_length / D)`, and the assembled length,
format, element representation, and shape match the active publisher descriptor
in the verified manifest. It MUST accept chunks in any order after the FD
decoded length is pinned, but MUST NOT commit an incomplete snapshot and MUST
discard a conflicting duplicate chunk or a snapshot whose sequence is duplicate
or stale under the ordering rule above. It MUST NOT expose a partially
assembled matrix or array as current state.

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
