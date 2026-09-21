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

| Class | Identifier range | Traffic | Source rule |
|---:|---:|---|---|
| `0x0` | `0x000–0x07F` | Safety | Reserved; no v0.1 payload assigned |
| `0x1` | `0x080–0x0FF` | Operational control | Reserved; no v0.1 payload assigned |
| `0x2` | `0x100–0x17F` | Discovery control | Only registered control frames |
| `0x3–0x4` | `0x180–0x27F` | Reserved | Must not be sent or accepted |
| `0x5` | `0x281–0x2FF` | Node claim | Low bits are requested node ID |
| `0x6` | `0x301–0x37F` | Role announce | Low bits are confirmed sender ID |
| `0x7` | `0x381–0x3FF` | Telemetry | Low bits are confirmed sender ID |
| `0x8–0xF` | `0x400–0x7FF` | Reserved | Must not be sent or accepted |

`0x280`, `0x300`, and `0x380` are reserved because node ID `0x00` is not
assignable. Lower numeric identifiers win CAN arbitration; this ordering is
priority, never an ownership decision.

## Registry

| Message | CAN identifier | DLC | Payload |
|---|---:|---:|---|
| Node claim | `(0x05 << 7) | requested_node_id` | 8 | UUID |
| Claim confirmation | `(0x02 << 7) | subject_node_id` | 8 | UUID |
| Role announce | `(0x06 << 7) | source_node_id` | 8 | Role mask, firmware fingerprint, config count |
| Telemetry | `(0x07 << 7) | source_node_id` | 8 | Publisher, sequence, status, context, value |

Claim confirmation is a discovery-control assertion for the identifier in its
low seven bits. Its UUID identifies the asserted owner. Session-reset,
reclaim, rejection, safety, and operational-control wire formats remain
unassigned and MUST NOT use a reserved range.

## Frame and sender invariants

- A sender MUST emit a Classic CAN base-format data frame: `IDE=0`, `RTR=0`,
  raw DLC `8`, and exactly eight data bytes. CAN FD (`FDF=1`), BRS, and ESI
  are prohibited. A receiver MUST discard a frame that fails any of those
  checks before Rebus dispatch, without a protocol response or remote-frame
  responder.
- Multi-octet payload values use little-endian octet order. CAN serializes bit
  7 through bit 0 of each octet; byte order does not reverse physical bits.
- `0x00` MUST NOT be a requested, source, or unicast destination node ID.
  `0x0000000000000000` and `0xffffffffffffffff` are invalid UUIDs.
- A role or telemetry frame is attributable only after its identifier's source
  ID resolves to a current-session `CONFIRMED` mapping; a tombstoned,
  provisional, reclaiming, rejected, or quarantined mapping is not enough.
- A receiver keys role state by `(session, node_id, hardware_uuid)` and
  telemetry state by `(session, node_id, hardware_uuid, publisher_id)`, and
  clears both at session reset or mapping invalidation.

## CAN transmission and recovery

Normal traffic uses controller automatic retransmission as one logical
emission. A node claim is the exception: its driver must disable automatic
retransmission, report completion/error/abort and bus state, and make one
submission in its commissioned claim slot per period. A non-completion defers
that submission to the same slot in the next period. Bus-off cancels queued
traffic and timers; after reported recovery the node completes the listen
window before reclaim or bootstrap. A controller lacking these controls is not
conformant for claims.

## Commissioned bootstrap admission

Before a session, commissioning must install a write-protected record bound to
each admitted UUID containing profile revision, bit rate, calculated `N_max`,
one claim slot unique among admitted UUIDs in `0..N_max-1`, and an immutable
ordered nonempty list of distinct candidate IDs in `0x01–0x7F`. A node
validates that record locally before probing or reclaiming. An absent, corrupt,
mismatched, or duplicated record leaves it a passive listener; CAN traffic
never grants admission.

## Discovery capacity

Only nodes with a valid commissioned admission record may be bootstrap-active;
all other nodes are passive listeners. The record, not CAN traffic, determines
admission. A deployment MUST admit no more bootstrap-active nodes than the
limit below.
Bootstrap-active nodes share a discovery limiter of at most ten completed
control/claim/initial-role transmissions per second per node. A confirmed
owner emits no more than one confirmation and one aggregate rejection per
250 ms. These are offered-load limits, not bandwidth reservations.

A DLC-8 standard Classic CAN frame is budgeted at 135 bus bits including
maximum stuffing and intermission. One bounded error/recovery episode is 287
bits. Discovery consumes at most 25% of nominal capacity:
`N_max = floor((0.25 * bitrate) / (10 * 287))`.

| Bit rate | Maximum bootstrap-active nodes |
|---:|---:|
| 125 kbit/s | 10 |
| 250 kbit/s | 21 |
| 500 kbit/s | 43 |
| 1 Mbit/s | 87 |

Continuous higher-priority traffic, repeated errors, or bus-off void the
bootstrap-time bound; they never authorize an abbreviated state transition.
