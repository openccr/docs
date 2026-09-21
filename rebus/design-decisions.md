SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus design decisions

This document records implementation and product choices that support the
normative Rebus specifications without adding their rationale to wire-format
documents.

## Persist node identity and admission

**Decision:** Persist the immutable `hardware_uuid`, the commissioned
admission record, and the last node ID at which this UUID was active. The
record's candidate list is ordered from lowest to highest, so every bootstrap
or recovery after power-on, reboot, or bus-off starts with the lowest valid
candidate. In v0.1, `0x00` is reserved and invalid; the first possible
candidate is `0x01`.

A reboot and bus-off recovery are ordinary admission events. The node
suppresses normal Rebus traffic, discards any interrupted claim count, and
reruns the five-claim procedure from ordinal one. Claims begin as soon as the
node is ready and use a sender-local nominal 500-ms throttle interval; this
interval is not a shared network slot or synchronization epoch. A live owner
of the first candidate wins by sending a targeted `CLAIM_REJECT`; the
recovering node then selects its next unattempted commissioned candidate. A
previously active node that is silent reserves no ID.

Hardware UUID uniqueness remains outside Rebus manufacturing and provisioning.
When a node observes its UUID in foreign claim activity at either the same or a
different node ID, it emits one `UUID_COLLISION` diagnostic and enters terminal
`IDENTITY_FAULT`. A matching participant that hears the diagnostic emits one
logical copy if it has not reported in that boot/session, then enters the same
state. Normal CAN retransmission is sufficient; fixed application-level
repetition is deliberately avoided.

### Accepted duplicate-UUID limitation

Two physical nodes with the same UUID that claim the same node ID at exactly
indistinguishable times can emit byte-identical `NODE_CLAIM` frames. Classic
CAN carries no sender discriminator, so neither node can prove that a second
physical sender exists when the duplicate frame cannot be distinguished from
its own local emission. Those nodes could therefore complete the five-claim
procedure without emitting `UUID_COLLISION`.

This is an accepted low-probability limitation of the current Rebus scope. A
future revision MAY add a claim-origin discriminator or a second-stage
collision challenge if field experience makes the risk material.

### Why the lowest candidate is deterministic

Using the ascending commissioned list gives every node the same initial
candidate-selection rule without requiring synchronized clocks. The claim
transmission times remain independent: each node sends when ready, waits for
its local throttle interval, and may be delayed by bus activity.

### Why collision reports use one logical message

`UUID_COLLISION` carries the complete UUID at the bus-wide `0x480` identifier.
The message does not encode a node ID because equal UUIDs are conflicts whether
their claims use the same or different IDs. Each participating node reports at
most once, and a matching receiver reports once in response; CAN controller
retransmission handles bus errors without creating an application-level report
storm.

## Bind manifest transfers before chunk assembly

A manifest chunk preserves four bytes of canonical content, so its existing
eight-byte payload has no room for a revision and fingerprint in addition to
the transfer ID and chunk index. A separate transfer-start frame carries the
revision and fingerprint once; the receiver supplies the UUID and
identity-generation from discovery and requires every chunk to belong to that
accepted context. This preserves chunk capacity while preventing an orphan,
stale, or node-ID-reassigned chunk from creating a manifest assembly.

## Qualify manifest cache freshness with revision

**Decision:** Advertisements carry both the source-local
`manifest_revision` and the 32-bit SHA-256 prefix. The receiver may activate a
cached manifest only when the hardware UUID, revision, fingerprint, and
complete locally validated canonical bytes all match. The fingerprint remains a
lookup hint and is never the sole freshness decision.

The eight-byte manifest query cannot carry both the 16-bit revision and the
32-bit fingerprint in addition to its existing fields. It therefore carries
`known_revision`; the requester sends zero when its cached revision is not an
exact match for the advertised revision/fingerprint pair. The source may omit a
transfer only when the known revision matches its current revision.

`manifest_revision` persists across reboot and bus-off recovery, advances when
canonical manifest bytes change, and wraps from `0xFFFF` to `0x0001`;
`0x0000` is reserved as the no-known-revision sentinel. Revision comparison is
equality-only. A receiver that retains a pre-wrap cache can theoretically reuse
stale content if the wrapped revision and 32-bit fingerprint both match; this
low-probability limitation is accepted for v0.1 because embedded nodes are
expected to retain only a small bounded cache.

The bounded cache does not eliminate that theoretical collision. A future
revision MAY add a wider generation or full-digest wire exchange if the
limitation becomes material.

## Require a verified manifest before telemetry

**Decision:** A receiver discards scalar and structured telemetry until it has
a complete validated manifest bound to the source's current hardware UUID,
identity generation, manifest revision, and fingerprint. A matching validated
cache entry qualifies; an advertisement alone does not.

Once the manifest is active, the receiver resolves each publisher and requires
the frame's context and value representation, or the structured snapshot's
format, encoded length, element representation, and shape, to match the
manifest descriptor. Rejected frames do not advance sequence state, establish
baselines, count drops, or create partial snapshots. This prevents stale,
unknown, and semantically mismatched telemetry from reaching consumers without
adding fields to the telemetry payload.

## Structured snapshot ordering

**Decision:** Structured snapshots use their own eight-bit
`snapshot_sequence`, but receivers apply the same half-range modulo ordering
as scalar telemetry. A source increments the value once per newly generated
logical snapshot, keeps it constant across all chunks, wraps from `0xFF` to
`0x00`, and resets it only at active entry or a UUID-binding reset; values
recur within an active generation only through that modulo wrap. A receiver
accepts the first complete snapshot as a baseline, treats modulo advances
`1..127` as newer, `0` as duplicate, and `128..255` as stale, and discards an
older incomplete assembly when a newer sequence appears.

This preserves out-of-order chunk delivery while preventing late chunks from
an older snapshot from replacing current state. The half-range rule has the
usual bounded-loss limitation: after missing 128 or more snapshots, ordering
remains conservative until a manifest advertisement or identity-generation
reset clears the receiver's snapshot state.

## Encode cross-node relations by UUID

**Decision:** Relation endpoints explicitly declare `LOCAL` or `FOREIGN`
scope. Local endpoints inherit the manifest owner's hardware UUID; foreign
endpoints carry the complete referenced hardware UUID in a nested endpoint TLV.
Resource and output identity remains `(resource_id)` or
`(resource_id, publisher_id)` within that UUID's manifest. Node addresses are
never part of relation identity.

Receivers validate local references immediately. Foreign references are
syntactically valid only with a valid UUID and are semantically active only
after the referenced UUID's complete validated manifest resolves the resource
and, for output endpoints, the publisher. This permits manifests to arrive
before their referenced nodes while preventing unresolved relations from being
used.

## Consequences

- Node identity remains stable through the immutable UUID.
- The ascending candidate list gives deterministic initial selection without
  reserving an address.
- Reboot and bus-off recovery use the same cooperative procedure as initial
  bootstrap.
- Observed duplicate UUID activity is contained without making UUID uniqueness
  a Rebus provisioning guarantee.
