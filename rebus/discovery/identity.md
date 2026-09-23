SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus discovery identity
**COMMON**


## Scope and dependencies

This document owns discovery identity-query selection, UUID-to-node-ID bindings,
generation invalidation, duplicate-UUID containment, and the `IDENTITY_FAULT`
transition. The [discovery lifecycle](lifecycle.md) owns commissioned admission,
claim lifecycle, and state transitions other than identity fault. The [wire
profile](../profile.md) owns the frame gate, identifiers, transmission recovery,
capacity, and commissioned admission.

[WHO_ARE_YOU](../messages/who-are-you.md), [node claim](../messages/node-claim.md),
and [UUID collision](../messages/uuid-collision.md) own their payload shapes and
message-specific validation. This document defines when valid messages affect
discovery state; it does not redefine their wire contracts.

## Identity query

`WHO_ARE_YOU` is a discovery identity query defined by the [message
specification](../messages/who-are-you.md). A specific query uses
`CAN_ID = (0x04 << 7) | target_node_id` for `target_node_id` in `0x01–0x7F`.
The broadcast query uses `CAN_ID = 0x200`; its low `0x00` is a query-only
exception and is not an assignable node ID. Both forms are processed after the
selected profile gate; their fixed eight-byte payload validation is owned by
the message specification.

A commissioned node in `CLAIMING` or `ACTIVE` MAY send `WHO_ARE_YOU`. It MUST
use its current candidate ID while `CLAIMING` or its assigned ID while
`ACTIVE`. An uncommissioned passive listener remains receive-only. A receiver
MUST apply the selected profile gate, require message type `0x01`, require a
requester ID in `0x01–0x7F`, and require all six reserved payload bytes to be
zero. It MUST discard an invalid query without response. The requester ID
correlates the request and does not authorize or negotiate the target address.

For a specific query, only the node currently in `ACTIVE` state for the target
ID is selected. For a broadcast query, every node currently in `ACTIVE` state
is selected. Nodes in `SELECT_CANDIDATE`, `CLAIMING`, and `UNASSIGNED` do not
respond. Each selected node MUST send exactly one existing [`node_claim`](../messages/node-claim.md)
frame for each accepted query.

Each selected node MUST choose an independent random response jitter in the
inclusive interval `0–200 ms` after receiving the query. The jitter is a
sender-local burst-throttling mechanism; it is not a network slot, claim
epoch, synchronization requirement, deadline, or substitute for the local
500-ms claim throttle. Bus activity may delay the response and does not
invalidate it. A node MUST coalesce duplicate observations of the same query
while its response timer is pending and MUST send no more than one response
for that query.

The response is a selected-profile-gated
[`node_claim`](../messages/node-claim.md) with the responder's current node ID
in the claim identifier and its immutable UUID in the eight-byte payload. A
receiver that observed the accepted query MUST correlate a response from a
selected active node as an identity reminder. It MUST establish or refresh the
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
node ID or a different node ID. The two cases use the same
[`UUID_COLLISION`](../messages/uuid-collision.md) diagnostic; node-ID equality
is not required for detection. A node excludes only its own locally submitted
claim from this comparison. Local transmit bookkeeping is an origin filter,
never ownership evidence.

On detecting a duplicate claim, a node emits one logical,
selected-profile-gated `UUID_COLLISION` message with its own UUID using normal
CAN retransmission, latches that it has reported the collision for the
boot/session, and enters `IDENTITY_FAULT`. The node MUST NOT emit fixed
application-level repeats or forward unrelated collision reports.

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

## Identity binding and generation

Whenever discovery establishes or refreshes a node-ID binding, it MUST compare
the observed UUID with the UUID currently bound to that ID. If the UUID
changes, discovery MUST advance that ID's local `identity_generation` and
invalidate the prior identity's transport state before the new binding is used.
This invalidation includes scalar sequence state, incomplete structured
snapshots, in-progress manifest transfers, local subscriptions, and
requester-bound control state. A binding refresh with the same UUID does not
advance the generation or invalidate state.

## Identity fault

`IDENTITY_FAULT` is terminal for the current boot/session. A faulted node
suppresses claims, normal Rebus traffic, `CLAIM_REJECT`, and
`WHO_ARE_YOU` responses, and remains faulted until external maintenance or a
reset procedure outside this feature.
