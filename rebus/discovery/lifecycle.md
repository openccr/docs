SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus discovery lifecycle

## Application-level acceptance boundary

CAN ACK, transmit completion, and local loopback are not application-level
claim acceptance evidence.

## Node-claim lifecycle boundary

A claim uses the current candidate selected from the commissioned admission
record's immutable ordered candidate list as its `preferred_node_id`; it is in
`0x01–0x7F`. `0x00` and CAN ID `0x280` are reserved.

[Node claim](../messages/node-claim.md) owns its frame and payload contract.
The frame and sender gate in the [wire profile](../profile.md) applies before
claim decoding. This lifecycle defines when a node sends or acts on a valid
claim; it does not create a second payload or message-validation contract.

## Admission, candidates, and identity

Only a node with a valid commissioned bootstrap-admission record may select a
candidate or claim an ID. The record and capacity limit are defined in the
[wire profile](../profile.md#commissioned-bootstrap-admission). A node without
one remains a passive listener; observed bus traffic never grants admission.

For every bootstrap or recovery after power-on, reboot, or bus-off, the node
selects the lowest valid ID in its commissioned candidate list. The commissioned
list MUST be ordered from lowest to highest, so the first claim uses the lowest
possible serial defined by the profile. In v0.1, `0x00` is reserved and
invalid, so the first possible ID is `0x01`. After a loss, the node moves
immediately to the next unattempted ID in list order. It MUST NOT wrap or retry
an attempted candidate during that session. An exhausted node is `UNASSIGNED`
and listens only; it sends no normal Rebus traffic.

A changed, unreadable, or invalid persisted UUID is an identity fault: the node
MUST remain a passive listener for that session.

## States

```text
SELECT_CANDIDATE -> CLAIMING -> ACTIVE
       |                |
       v                v
   UNASSIGNED      SELECT_CANDIDATE

Any state with duplicate UUID activity -> IDENTITY_FAULT
```

- **SELECT_CANDIDATE:** select the next commissioned candidate. If none
  remains, enter `UNASSIGNED`.
- **CLAIMING:** submit ordinal claims for the selected candidate and observe
  claims and targeted rejections for that live attempt.
- **ACTIVE:** owns the selected ID and may send normal Rebus traffic.
- **UNASSIGNED:** listens only and sends no normal Rebus traffic.
- **IDENTITY_FAULT:** terminally suppresses all Rebus functions after a
  duplicate-UUID detection; external maintenance is required for recovery.

## Cooperative claim procedure

Claim timing is local to the sending node. A claim session begins when the node
is ready after power-on, reboot, or bus-off recovery. The node submits its first
one-shot claim for the selected candidate as soon as the CAN controller and bus
permit it; claims from different nodes therefore need not be synchronized.

After each one-shot submission, the claimant starts an internal nominal 500-ms
throttle interval. When that interval expires, it submits the next ordinal
claim, or retries the same ordinal after an aborted or failed submission, as
soon as the bus permits. The interval is not a network slot, deadline, or
shared epoch: bus activity may delay a submission, and the delayed submission
remains valid. A node MUST NOT use a delayed submission to infer a
network-wide clock or phase.

For this procedure, a successful claim is a one-shot submission that completes
without a driver-reported abort or error. This is only a local transmission
result, not application-level ownership acceptance; CAN ACK, transmit
completion, and local loopback do not establish ownership. Five successful
ordinal claims are required: ordinal one through ordinal five.

Before candidate arbitration, a node compares every valid foreign claim UUID
with its own valid UUID, regardless of the requested node ID. A matching UUID
is duplicate activity and triggers the [duplicate UUID detection](identity.md#duplicate-uuid-detection)
procedure. A node does not compare its own locally submitted claim as foreign,
and a correlated identity reminder is handled by the
[identity-query rules](identity.md#identity-query).

For claims for the same requested ID, the lower unsigned 64-bit UUID is the
only winner. Equal UUIDs are duplicates. Arrival order, wall-clock order,
firmware version, CAN priority, and CAN arbitration MUST NOT select a UUID
winner. On observing a lower UUID for its candidate, a claimant loses that
candidate.

For an uncontested claimant whose first successful claim is at `t`, later
successful claims have nominal due times `t + 500 ms`, `t + 1,000 ms`,
`t + 1,500 ms`, and `t + 2,000 ms`; each may occur later when the bus is busy.
The claimant enters `ACTIVE` immediately after the fifth successful claim and
persists that candidate as `last_active_node_id` for its self-view.
For example, a node whose first claim is transmitted at `T0 + 200 ms` has a
nominal next due time of `T0 + 700 ms` and may transmit at `T0 + 703 ms` if the
bus is busy at the nominal time. A node whose first claim is transmitted at
`T0 + 340 ms` independently has a nominal next due time of `T0 + 840 ms`.

## Active-owner rejection and recovery

An `ACTIVE` owner MUST immediately transmit
[`CLAIM_REJECT(rejected_node_id, rejected_claimant_uuid)`](../messages/claim-reject.md) for every valid claim
for its own ID, unless the claim UUID equals the owner's local UUID. An equal
UUID is duplicate activity and takes the [duplicate UUID detection](identity.md#duplicate-uuid-detection)
transition instead of ordinary rejection. It MUST NOT relinquish its ID
because of a claimant UUID, including one lower than its own. The rejection
targets the claimant UUID and is not an ownership or acceptance confirmation.

A claimant abandons a live attempt only when both the rejection ID and the
target UUID match its current candidate and UUID. After observing a lower UUID
or receiving such a matching rejection, it immediately selects the next
candidate. Its first transmission for that candidate MUST occur no earlier
than 100 ms after the loss and then follows the same local throttle procedure.
It MUST NOT retry or wrap the lost candidate.

On reboot or bus-off, a node suppresses normal Rebus traffic until it has
completed an ordinary five-claim procedure and become `ACTIVE`. It discards
an interrupted claim count and restarts at ordinal one after recovery. A node
in `IDENTITY_FAULT` does not automatically recover through reboot or bus-off;
external maintenance or a reset procedure outside this feature is required.
Normal traffic uses controller automatic retransmission; claims require the
profile's one-shot capability.

## Inventory manifest

After becoming `ACTIVE`, a node starts the
[manifest-advertisement process](../messages/inventory/transport.md#manifest-advertisement);
the [inventory manifests](../messages/inventory/README.md) provide domain
navigation. The advertisement identifies the node's cacheable static inventory
and begins the source's telemetry reset sequence. A node that lacks the
matching UUID-bound manifest MAY send the unicast query defined by the
[manifest query](../messages/inventory/transport.md#manifest-query). Manifest
advertisements and transfers neither confirm nor renew discovery ownership.

## Persistence

Persist the UUID, commissioned admission record, and the node's last active
node ID for the self-view used by identity-reminder classification. The
candidate order in that record determines the first candidate after every
bootstrap or recovery.
