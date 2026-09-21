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

## Identity query

`WHO_ARE_YOU` is a discovery identity query defined by the
[message specification](messages/who-are-you.md). A specific query uses
`CAN_ID = (0x04 << 7) | target_node_id` for `target_node_id` in `0x01–0x7F`.
The broadcast query uses `CAN_ID = 0x200`; its low `0x00` is a query-only
exception and is not an assignable node ID. Both forms are Classic CAN base
data frames with raw DLC 8.

A commissioned node in `CLAIMING` or `ACTIVE` MAY send `WHO_ARE_YOU`. It MUST
use its current candidate ID while `CLAIMING` or its assigned ID while
`ACTIVE`. An uncommissioned passive listener remains receive-only. A receiver
MUST apply the profile frame gate, require message type `0x01`, require a
requester ID in `0x01–0x7F`, and require all six reserved payload bytes to be
zero. It MUST discard an invalid query without response. The requester ID
correlates the request and does not authorize or negotiate the target address.

For a specific query, only the node currently in `ACTIVE` state for the target
ID is selected. For a broadcast query, every node currently in `ACTIVE` state
is selected. Nodes in `SELECT_CANDIDATE`, `CLAIMING`, and `UNASSIGNED` do not
respond. Each selected node MUST send exactly one existing `node_claim` frame
for each accepted query.

Each selected node MUST choose an independent random response jitter in the
inclusive interval `0–200 ms` after receiving the query. The jitter is a
sender-local burst-throttling mechanism; it is not a network slot, claim
epoch, synchronization requirement, deadline, or substitute for the local
500-ms claim throttle. Bus activity may delay the response and does not
invalidate it. A node MUST coalesce duplicate observations of the same query
while its response timer is pending and MUST send no more than one response
for that query.

The response is a `node_claim` with the responder's current node ID in the
claim identifier and its immutable UUID in the eight-byte payload. A receiver
that observed the accepted query MUST correlate a response from a selected
active node as an identity reminder. It MUST establish or refresh the
UUID-to-node-ID mapping from that response; if a different UUID was previously
bound to that node ID, the current binding is replaced for subsequent identity
resolution.

The correlated response is an identity reminder only. It MUST NOT increment or
satisfy a claim count, arbitrate UUIDs, cause candidate loss, cause
`CLAIM_REJECT`, assign or relinquish an address, or act as ownership
acceptance, confirmation, or renewal.

A receiver MUST classify a `node_claim` correlated to its own accepted query as
an identity reminder before applying duplicate-UUID detection. A response that
cannot be correlated to an accepted query is not an identity reminder and
remains subject to ordinary claim validation.

Identity queries and their responses do not start, reset, delay, or synchronize
a claim session. The first claim after power-on, reboot, or bus-off still
occurs as soon as the node is ready and the bus permits it. Later claims still
use the sender-local nominal 500-ms throttle and may be delayed by bus activity.

## Duplicate UUID detection

Hardware UUID uniqueness is outside the manufacturing and provisioning scope
of Rebus. Rebus nevertheless MUST contain an observed duplicate identity.
Every commissioned node with a valid local UUID, including a node that is
`SELECT_CANDIDATE`, `CLAIMING`, `ACTIVE`, or `UNASSIGNED`, MUST listen for
valid `NODE_CLAIM` frames and compare each foreign claim UUID with its own UUID
without filtering on the requested node ID.

A matching UUID is a duplicate whether the foreign claim requests the same
node ID or a different node ID. The two cases use the same `UUID_COLLISION`
diagnostic; node-ID equality is not required for detection. A node excludes
only its own locally submitted claim from this comparison. Local transmit
bookkeeping is an origin filter, never ownership evidence.

On detecting a duplicate claim, a node emits one logical `UUID_COLLISION`
message with its own UUID using normal CAN retransmission, latches that it has
reported the collision for the boot/session, and enters `IDENTITY_FAULT`. The
node MUST NOT emit fixed application-level repeats or forward unrelated
collision reports.

A node that receives `UUID_COLLISION` carrying its own UUID emits one logical
matching report if its report latch is not set, then enters `IDENTITY_FAULT`.
This bounded echo ensures both reachable duplicate-UUID participants report
without creating a forwarding loop. A node with a different UUID remains
operational, but its interface node MAY record and report the diagnostic.

An identity reminder correlated to an accepted `WHO_ARE_YOU` query is excluded
from ordinary claim collision evaluation. Each node persists a self-view of
its own `(hardware_uuid, last_active_node_id)`. A correlated reminder carrying
the local UUID at that persisted node ID is the expected returning identity and
MUST NOT fault the node. A correlated reminder carrying the local UUID at any
other node ID is duplicate activity and MUST trigger `UUID_COLLISION`.

Whenever discovery establishes or refreshes a node-ID binding, it MUST compare
the observed UUID with the UUID currently bound to that ID. If the UUID
changes, discovery MUST advance that ID's local `identity_generation` and
invalidate the prior identity's transport state before the new binding is used.
This invalidation includes scalar sequence state, incomplete structured
snapshots, in-progress manifest transfers, local subscriptions, and
requester-bound control state. A binding refresh with the same UUID does not
advance the generation or invalidate state.

`IDENTITY_FAULT` is terminal for the current boot/session. A faulted node
suppresses claims, normal Rebus traffic, `CLAIM_REJECT`, and
`WHO_ARE_YOU` responses, and remains faulted until external maintenance or a
reset procedure outside this feature.

## Admission, candidates, and identity

Only a node with a valid commissioned bootstrap-admission record may select a
candidate or claim an ID. The record and capacity limit are defined in the
[wire profile](profile.md#commissioned-bootstrap-admission). A node without one
remains a passive listener; observed bus traffic never grants admission.

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
is duplicate activity and triggers the [duplicate UUID detection](#duplicate-uuid-detection)
procedure. A node does not compare its own locally submitted claim as foreign,
and a correlated identity reminder is handled by the identity-query rules
above.

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
`CLAIM_REJECT(rejected_node_id, rejected_claimant_uuid)` for every valid claim
for its own ID, unless the claim UUID equals the owner's local UUID. An equal
UUID is duplicate activity and takes the [duplicate UUID detection](#duplicate-uuid-detection)
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
[manifest-advertisement process](messages/inventory.md#manifest-advertisement).
The advertisement identifies the node's cacheable static inventory and begins
the source's telemetry reset sequence. A node that lacks the matching
UUID-bound manifest MAY send the unicast query defined by the [inventory
message specification](messages/inventory.md). Manifest advertisements and
transfers neither confirm nor renew discovery ownership.

## Persistence

Persist the UUID, commissioned admission record, and the node's last active
node ID for the self-view used by identity-reminder classification. The
candidate order in that record determines the first candidate after every
bootstrap or recovery.
