SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus discovery

## Scope and precedence

This document defines decentralized node-claim state and timing for Rebus v0.1.
The [wire profile](profile.md) owns identifiers, frame format, transmission
recovery, capacity, and commissioned admission. Unassigned control formats are
listed in [open issues](open-issues.md) and MUST NOT be guessed.

CAN ACK, transmit completion, and local loopback are not application-level
claim acceptance evidence.

## Node claim

A claim is an 11-bit Classic CAN base data frame with raw DLC 8:

```text
CAN_ID = (0x05 << 7) | preferred_node_id
payload = little-endian uint64_t hardware_uuid
```

`preferred_node_id` is the current candidate selected from the commissioned
admission record's immutable ordered candidate list; it is in `0x01–0x7F`.
`0x00` and CAN ID `0x280` are reserved. The UUID is a validated immutable
physical-MCU or write-once provisioned identity; all-zero and all-one UUIDs are
invalid. The frame and sender gate in the wire profile applies before claim
decoding. A receiver accepts only `0x281–0x2FF`, decodes the low seven bits as
the requested ID, and MUST NOT infer a UUID winner from CAN arbitration.

## Admission, candidates, and identity

Only a node with a valid commissioned bootstrap-admission record may probe or
reclaim. The record and capacity limit are defined in the [wire profile](profile.md#commissioned-bootstrap-admission).
A node without one remains a passive listener; observed bus traffic never
grants admission.

Fresh bootstrap starts with the first candidate in the commissioned admission
record's immutable ordered list. After a UUID loss or valid rejection, the node
stops using that ID, waits randomized 250–750 ms, and tries the next candidate
once. It MUST NOT wrap or retry an attempted candidate during the session. An
exhausted node is `UNASSIGNED` and listens only.

A changed, unreadable, or invalid persisted UUID is an identity fault: the node
MUST NOT reclaim or fresh-claim in that session. If one UUID is confirmed for
two IDs, or two UUIDs are confirmed for one ID, every affected association is
`QUARANTINED` until explicit session reset. Quarantined nodes suppress all
application traffic and MUST NOT elect a retroactive winner.

## States

```text
LISTEN -> PROBING -> PROVISIONAL -> CONFIRMED
                  |                |
                  +-> REJECTED     +-> RECLAIMING
                  |                |
                  +-> UNASSIGNED   +-> QUARANTINED
```

- **LISTEN:** collect discovery frames; no claims or application traffic.
- **PROBING:** submits the scheduled claims for its selected candidate and
  collects contenders during the 500-ms collision-observation window.
- **PROVISIONAL:** stops claims for that candidate, remains the lowest UUID
  among observed contenders, and completes the confirmation evidence requirement.
- **CONFIRMED:** owns its ID locally and emits confirmations every 250 ms.
- **REJECTED:** stops traffic, backs off, and advances its candidate list.
- **RECLAIMING:** returning node validates its persisted UUID-to-ID record and
  uses confirmation evidence before traffic resumes.
- **UNASSIGNED:** candidate list exhausted; listens only.
- **QUARANTINED:** conflicting confirmed identity; traffic suppressed through
  the session.

## Collision and confirmation

For unconfirmed claims for the same requested ID, the numerically lower unsigned
64-bit UUID wins. Equal UUID/ID observations are duplicates, not a collision.
Arrival order, clock time, firmware version, and CAN data ordering MUST NOT
select a winner. A lower UUID observed before confirmation immediately rejects
the higher attempt.

After its 500-ms collision-observation window, a probing claimant that has
observed no lower UUID stops claiming, enters `PROVISIONAL`, and emits
`CLAIM_CONFIRM` every 250 ms. Its identifier is `(0x02 << 7) | node_id`; its
eight-byte payload is the claimant UUID. A claimant is locally `CONFIRMED` only
after three successful emissions spanning 500–750 ms. A receiver accepts a
mapping only after three remote valid confirmations for the same local
discovery-session generation, node ID, and UUID over the same span. The session
generation is local state and is reset only by the as-yet-unassigned
session-reset control procedure; confirmations carry no session field. Sender
and receiver independently suppress application traffic until their own
criterion succeeds.

Confirmation refresh preserves the mapping but does not make an ID reusable.
A missing refresh does not release a tombstone. Rejection, reclaim, and session
reset require the assigned control formats still recorded as open issues.

## Claim schedule and recovery

Only a `PROBING` claimant submits one claim in its commissioned claim slot
during every 100-ms claim period. The slot is an integer in `0..N_max-1`,
therefore within the 100 one-millisecond slots, and is unique among admitted
UUIDs. A one-shot claim that is aborted or fails is retried only in that same
slot in the next period. Normal traffic uses controller automatic
retransmission; claims require the profile's one-shot capability. On bus-off,
cancel queued traffic and timers; after controller recovery, complete LISTEN
before reclaim or bootstrap.

## Timing bound

The initial cohort enters LISTEN within 2,000 ms of its enrollment epoch. For
one unrejected initial candidate, the upper bound is:

```text
2.000 s enrollment skew
+0.250 s listen
+0.500 s collision observation
+0.500 s three-frame evidence
=3.250 s
```

This bound requires the profile's commissioned capacity admission and a
serviceable Classic CAN bus. It excludes retries, late joiners, continuous
higher-priority traffic, repeated errors, and bus-off; none authorizes a
shortened transition.

## Role announcement

After local confirmation, a node starts the [capability-announcement
process](messages/role-announce.md#capability-announcement-process). Role bits
are capabilities, not message IDs. The [role-announcement
specification](messages/role-announce.md) owns the payload, cadence, and
telemetry-epoch rules. Receivers accept an announcement only for their current
confirmed mapping; it never confirms or renews a claim.

## Persistence

Persist UUID, confirmed node ID, discovery session identifier, confirmation
state, and commissioned admission record. A reboot is not a new allocation:
it reclaims its own tombstoned ID and sends no application traffic until its
confirmation criterion succeeds. The rationale is in [design decisions](design-decisions.md).
