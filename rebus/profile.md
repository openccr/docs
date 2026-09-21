SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus wire profile

## Scope

This document owns normative profile decisions. Profile rules take precedence
over source headers and explanatory text elsewhere in the Rebus documents.

## Status

```text
Wire profile:       Rebus v0.1
CAN mode:           Classic CAN 2.0A base-format data frames only
Nominal bit rates:  125, 250, 500, or 1,000 kbit/s
Payload octet order: little-endian (CAN data bits: MSB-first)
Node IDs:           0x01–0x7F unicast; 0x00 reserved/unassigned
```

## Standard identifier classes

Every assigned Rebus identifier is an 11-bit base identifier. Unless a message
rule explicitly names a subject rather than a sender, it is
`CAN_ID = (class << 7) | node_id`.

| Class | Identifier range | Traffic | Source/target rule |
|---:|---:|---|---|
| `0x0` | `0x000–0x07F` | Safety | Reserved; no v0.1 payload assigned |
| `0x1` | `0x081–0x0FF` | Manifest query | Low bits are target node ID |
| `0x2` | `0x101–0x17F` | Discovery control | Low bits name the registered subject |
| `0x3` | `0x181–0x1FF` | Telemetry control request | Low bits are requester ID |
| `0x4` | `0x200–0x27F` | Identity query | `0x200` is broadcast; `0x201–0x27F` target one node ID |
| `0x5` | `0x281–0x2FF` | Node claim | Low bits are requested node ID |
| `0x6` | `0x301–0x37F` | Manifest advertise/transfer | Low bits are source sender ID |
| `0x7` | `0x381–0x3FF` | Scalar telemetry | Low bits are source sender ID |
| `0x8` | `0x401–0x47F` | Structured telemetry snapshot | Low bits are source sender ID |
| `0x9` | `0x480` | UUID collision diagnostic | Broadcast; low bits are zero by exception |
| `0x9` | `0x481–0x4FF` | Reserved | Must not be sent or accepted |
| `0xA–0xF` | `0x500–0x7FF` | Reserved | Must not be sent or accepted |

`0x080`, `0x100`, `0x180`, `0x280`, `0x300`, `0x380`, and `0x400` are reserved
because node ID `0x00` is not assignable. `0x200` and `0x480` are explicit
exceptions: they encode broadcast `WHO_ARE_YOU` and `UUID_COLLISION`,
respectively. Lower numeric identifiers win CAN arbitration; this ordering is
priority, never an ownership decision.

Manifest queries and identity queries are the explicit subject-addressing
exceptions. Manifest queries use the low seven identifier bits as a unicast
target. Identity queries use `0x201–0x27F` for a unicast target and `0x200` for
broadcast. `UUID_COLLISION` is bus-wide and has no target. Manifest
advertisements, transfer starts, chunks, scalar telemetry, and structured
snapshot chunks use the low seven bits as the source node ID.

| Message | CAN identifier | DLC | Payload |
|---|---:|---:|---|
| Node claim | `(0x05 << 7) | requested_node_id` | 8 | UUID |
| Claim rejection | `(0x02 << 7) | rejected_node_id` | 8 | Target UUID |
| UUID collision | `0x480` | 8 | Conflicting UUID |
| Manifest query | `(0x01 << 7) | target_node_id` | 8 | Query opcode, requester, known revision |
| Identity query | `0x200` broadcast or `(0x04 << 7) | target_node_id` | 8 | Query type, requester, zero reserved bytes |
| Manifest advertise | `(0x06 << 7) | source_node_id` | 8 | Format, revision, manifest fingerprint |
| Manifest transfer start | `(0x06 << 7) | source_node_id` | 8 | Transfer ID, revision, manifest fingerprint |
| Manifest chunk | `(0x06 << 7) | source_node_id` | 8 | Transfer ID, chunk index, four data bytes |
| Scalar telemetry | `(0x07 << 7) | source_node_id` | 8 | Publisher, sequence, status, context, value |
| Structured snapshot chunk | `(0x08 << 7) | source_node_id` | 8 | Publisher, snapshot sequence, chunk index, chunk count, four data bytes |
| Telemetry control request | `(0x03 << 7) | requester_node_id` | 8 | Telemetry control request |

`CLAIM_REJECT` is a discovery-control message for the identifier in its low
seven bits. Its eight-byte little-endian UUID payload targets the rejected
claimant. It is neither acceptance nor ownership confirmation. `UUID_COLLISION`
uses the complete UUID as a bus-wide diagnostic and does not replace
`CLAIM_REJECT` for ordinary active-owner rejection. `WHO_ARE_YOU` is assigned
only to class `0x4`; its `0x200` identifier is broadcast and its
`0x201–0x27F` identifiers target one node ID. Manifest advertisements,
transfer starts, and chunks share class `0x6` and are distinguished by their
payload message type.
Session-reset, safety, and other unassigned operational-control formats MUST
NOT use a reserved range.


## Frame and sender invariants

- A sender MUST emit a Classic CAN base-format data frame: `IDE=0`, `RTR=0`,
  raw DLC `8`, and exactly eight data bytes. CAN FD (`FDF=1`), BRS, and ESI
  are prohibited. A receiver MUST discard a frame that fails any of those
  checks before Rebus dispatch, without a protocol response or remote-frame
  responder.
- Multi-octet payload values use little-endian octet order. CAN serializes bit
  7 through bit 0 of each octet; byte order does not reverse physical bits.
- `0x00` MUST NOT be a requested, source, or unicast destination node ID. The
  `0x200` and `0x480` identifiers are the sole low-zero exceptions: they encode
  broadcast `WHO_ARE_YOU` and `UUID_COLLISION`, respectively.
  `0x0000000000000000` and `0xffffffffffffffff` are invalid UUIDs.
- A receiver attributes manifest, scalar telemetry, structured snapshot, and
  telemetry-control traffic directly to the source or target ID named by the
  frame identifier. Identity-query dispatch uses its target low bits, except
  that `0x200` selects every active node. Discovery state and UUID mappings
  MUST NOT gate initial frame dispatch. Telemetry acceptance after dispatch
  MUST follow the verified-manifest and descriptor gate below; a manifest cache
  MUST still validate its UUID binding before activation.

Telemetry receivers MUST discard scalar and structured telemetry before
sequencing or publication unless a complete validated manifest is active for
the source's current UUID, identity generation, revision, and fingerprint.
With that manifest active, the receiver MUST also require the publisher,
context, value representation, and structured shape/length to match the
advertised output descriptor. A discarded frame MUST NOT advance sequence
state, establish a baseline, count as a drop, or create an incomplete
snapshot.
A receiver keys manifest state by
`(hardware_uuid, manifest_revision, manifest_fingerprint)` and
source-bound transport state by `(node_id, identity_generation)`. A manifest
transfer assembly additionally records `(hardware_uuid, transfer_id,
manifest_revision, manifest_fingerprint)` from its accepted transfer-start
context.
`identity_generation` is an opaque receiver-local token associated with the
currently bound UUID for a node ID, with an explicit unbound sentinel before
discovery establishes a UUID. It MUST advance whenever that binding changes and
MUST NOT be reused for a different UUID while state from the prior generation
may exist.

When discovery changes the UUID bound to a node ID, the receiver MUST discard
all transport state for the prior identity generation, including scalar
sequence state, incomplete structured snapshots, and other in-progress
source-bound assemblies. It MUST revoke local subscriptions and requester-bound
control state associated with that generation. A new binding starts with no
inherited transport state.

Each valid manifest advertisement is a telemetry reset boundary. It clears
scalar sequence state and incomplete structured snapshot state for its source.
When either the revision or fingerprint changes, it also invalidates incomplete
manifest transfer assemblies whose expected identity differs. A receiver that
has observed a current advertisement for the source node ID and identity
generation MUST accept a manifest transfer start only when both its revision and
fingerprint match that advertisement; a receiver without such an advertisement
MAY accept a nonzero-revision, nonzero-fingerprint start after the source UUID
binding exists. The matching manifest cache remains valid only when both
identity fields are unchanged.

## CAN transmission and recovery

Normal traffic uses controller automatic retransmission as one logical
emission. A node claim is the exception: its driver must disable automatic
retransmission, report completion/error/abort and bus state, and submit the
first one-shot claim as soon as the node is ready. The claimant then uses its
local nominal 500-ms throttle interval; bus activity may delay a submission,
and no shared claim epoch or network slot is required.
Bus-off cancels queued traffic and timers; after reported recovery, the node
suppresses normal Rebus traffic and restarts its five-claim procedure at ordinal
one. A controller lacking these controls is not conformant for claims.

## Commissioned bootstrap admission

Before a session, commissioning must install a write-protected record bound to
each admitted UUID containing profile revision, bit rate, calculated `N_max`,
and an immutable ordered nonempty list of distinct candidate IDs in ascending
order within `0x01–0x7F`. A node validates that record locally before selecting
a candidate. An absent, corrupt, mismatched, or duplicated record leaves it a
passive listener; CAN traffic never grants admission.

## Discovery capacity

Only nodes with a valid commissioned admission record may be bootstrap-active;
all other nodes are passive listeners. The record, not CAN traffic, determines
admission. A deployment MUST admit no more bootstrap-active nodes than the
limit below.
A claimant MUST submit no more than one claim during each local 500-ms
throttle interval while pursuing a candidate. After losing a candidate, its
first claim for the next candidate MUST NOT occur earlier than 100 ms after the
loss. Each first claim may generate one rejection.

A DLC-8 standard Classic CAN frame is budgeted at 135 bus bits including
maximum stuffing and intermission. One bounded error/recovery episode is 287
bits. Discovery consumes at most 25% of nominal capacity:
`N_max = floor((0.25 * bitrate) / (20 * 287))`.

| Bit rate | `N_max` |
|---:|---:|
| 125 kbit/s | 5 |
| 250 kbit/s | 10 |
| 500 kbit/s | 21 |
| 1 Mbit/s | 43 |

Continuous higher-priority traffic, repeated errors, or bus-off void the
bootstrap-time bound; they never authorize an abbreviated state transition.
