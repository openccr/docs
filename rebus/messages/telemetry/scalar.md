SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Scalar telemetry
**COMMON**


## Frame

A scalar telemetry frame is an eight-decoded-byte payload that carries one current
value from one logical publisher. Its fields separate stream identity, loss
detection, value status, and value interpretation:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `publisher_id`; node-local logical stream identifier |
| 1 | 1 | `uint8_t` | `sequence_id`; wrapping emission sequence for drop detection |
| 2 | 1 | `uint8_t` | `status_flags`; validity and alarm state |
| 3 | 1 | `uint8_t` | `context`; selects the value's meaning and representation |
| 4 | 4 | `uint8_t[4]` | Context-selected value bytes |

The fixed four-byte value area keeps every scalar emission within one Classic
CAN payload while allowing the [context registry](registries.md#contexts) to
choose the representation. The frame does not carry a unit or a manifest
resource ID; the [inventory output descriptor](../inventory/model.md) supplies
the publisher's meaning, unit, origin, and any structured shape.

### Physical framing

**COMMON**

After the selected [profile frame gate](../../profile.md), a scalar frame uses
exactly eight decoded bytes:

#### Classic CAN

**CLASSIC CAN**

A scalar frame uses a Classic data frame with raw DLC 8.

#### CAN FD

**CAN FD**

A scalar frame uses a CAN FD data frame with `FDF=1` and decoded length 8. The
FD requirement is a decoded-length rule, not a raw-DLC-as-byte-count
comparison. A receiver MUST discard an FD scalar frame of every other decoded
length; it MUST NOT aggregate scalar samples or extend the fixed payload.

#### Frame identity and profile validation

**COMMON**

Telemetry uses `CAN_ID = (0x07 << 7) | source_node_id` (`0x381–0x3FF`).
`publisher_id` is an 8-bit node-local logical publisher. On the wire, stream
identity remains `(source_node_id, publisher_id)`; receiver-local transport
state is additionally bound to the current [identity generation](../../discovery/identity.md)
for that source node ID. A receiver MUST apply the [profile frame gate](../../profile.md)
before decoding or sequencing a frame. [Wire encoding](../../encoding.md) owns
physical serialization.

## Manifest binding and descriptor acceptance

Before decoding, sequencing, assembling, or exposing telemetry, a receiver
MUST have a complete validated manifest currently bound to the source node ID's
hardware UUID and `identity_generation`, with the current
`manifest_revision` and `manifest_fingerprint`. A matching validated cache
entry activated from the current advertisement satisfies this requirement; an
advertisement without a validated manifest does not. If no such manifest is
available, the receiver MUST discard the telemetry frame.

The receiver MUST resolve the frame's `publisher_id` in that manifest. A scalar
frame is acceptable only when its `context` and value representation match the
publisher's output descriptor. A frame for an unknown publisher or a mismatching
descriptor MUST be discarded. [Structured snapshot descriptor acceptance](structured.md#complete-snapshot-validation)
is defined with structured assembly and commit.

Frames discarded by this gate MUST NOT advance sequence state, create a
baseline, count as drops, or create an incomplete structured snapshot. The
receiver resumes normal sequencing only after the manifest is validated and
active.

## Publisher identity and status

`publisher_id` values are node-local `0x00–0xFF`; a node may therefore expose
at most 256 distinct logical publishers in the v0.1 telemetry namespace.
Publisher IDs are not network-global and are unrelated to manifest
`resource_id` values. A resource may expose multiple publishers, and a
structured publisher may represent many scalar elements.

`status_flags`:

| Bit | Symbol | Meaning |
|---:|---|---|
| 0 | valid | Value is valid |
| 1 | warning | Warning state |
| 2 | alarm | Alarm state |
| 3–7 | reserved | Must be zero |

A frame with any reserved `status_flags` bit set is invalid and is discarded
without advancing sequence state.

The four value bytes can encode binary32, signed or unsigned 32-bit integers,
a Boolean, packed gradient factors, four packed tissue saturation values, or
one packed tissue-gas pair. [Context rules](registries.md) select exactly one
representation; receivers must not infer it from host ABI or payload value.

`publisher_id` is stable for one logical publisher while its source node remains
`ACTIVE` and MUST NOT be reassigned during that period. The active-entry
manifest-advertisement sequence creates a node-wide telemetry generation:
every local publisher's first scalar frame and first structured snapshot after
the 1,000-ms hold uses sequence zero, then scalar `sequence_id` and structured
`snapshot_sequence` advance independently modulo 256.

## Scalar sequencing and reset boundaries

After the manifest binding and descriptor gate passes, each
`(source_node_id, publisher_id, identity_generation)` stream is processed as
follows. Absence of a last accepted sequence value means that the next valid
scalar frame is a baseline and is accepted regardless of its `sequence_id`. A
conforming publisher's first baseline is zero, but a receiver can miss it.
Otherwise, with `advance = received - last` as `uint8_t`, accept `1..127`
(`report advance - 1 drops`), discard `0` as duplicate, and discard `128..255`
as stale. Each valid manifest advertisement clears scalar sequence state and
incomplete structured snapshot state for its source. The next valid frame from
each publisher is therefore a new baseline. A discovery UUID remap also
discards all sequence state from the prior identity generation. Silence does
not clear sequence state.

This modulo comparison is the shared ordering definition for telemetry. It is
unambiguous only within a forward distance of 127 snapshots. If a receiver
misses 128 or more logical snapshots, it follows the defined stale/duplicate
result until a reset boundary is observed; v0.1 has no separate
structured-snapshot reset message.

[Structured snapshots](structured.md) use this ordering definition for their
separate `snapshot_sequence` state; their chunk assembly, commit, and
replacement rules are defined there.
