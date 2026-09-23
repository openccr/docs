SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory manifest transport

## Identifier assignments
**COMMON**


Manifest messages use two identifier classes:

| Message | CAN identifier | Direction | Payload |
|---|---|---|---|
| Manifest query | `(0x01 << 7) \| target_node_id` (`0x081–0x0FF`) | unicast to target | Query opcode, requester ID, known revision |
| Manifest advertise/start/chunk | `(0x06 << 7) \| source_node_id` (`0x301–0x37F`) | source broadcast | Advertisement with revision and fingerprint, transfer start, or transfer chunk |

The query is the explicit subject-addressing exception in the profile: the low
seven identifier bits name the target node. The requester ID is also present
in the payload for rate limiting and request correlation. Advertisements,
transfer starts, and chunks use the low seven bits as the source node ID.

**COMMON**

Manifest advertisement, query, and transfer start are fixed eight-decoded-byte
messages in both profiles. The receiver applies the [profile frame gate](../../profile.md)
before message-specific validation.

### Chunk geometry

#### Classic CAN
**CLASSIC CAN**

A manifest chunk has decoded length `L = 8` and data-area length `D = 4`.

#### CAN FD
**CAN FD**

A manifest chunk uses a permitted selected decoded length and data-area length
`D = L - 4`.


## Manifest advertisement
**COMMON**


`rebus_msg_manifest_advertise_t` is an eight-byte payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x01` for advertisement |
| 1 | 1 | `uint8_t` | `manifest_format`; `0x01` for this format |
| 2 | 2 | `uint16_t` | `manifest_revision`; source-local manifest generation |
| 4 | 4 | `uint32_t` | `manifest_fingerprint`; cache fingerprint hint |

All multi-octet fields use the little-endian encoding in
[wire encoding](../../encoding.md).

The fingerprint is the little-endian integer formed from the first four bytes
of SHA-256 over the canonical manifest bytes, with the fingerprint field in the
manifest header zeroed for hashing. It is a cache and lookup hint, not an
integrity or authorization credential, and MUST NOT be the sole freshness
decision. The complete manifest remains the validation source. A fingerprint of
`0x00000000` is reserved and MUST NOT be advertised or stored as a current
manifest fingerprint; it is the query sentinel for “no cached manifest”.

Before activating or caching a completed manifest, a receiver MUST recompute
the SHA-256 fingerprint with the header fingerprint field zeroed and require
its first four bytes to equal the nonzero fingerprint in both the completed
header and the accepted transfer-start context. A mismatch invalidates the
transfer even if no previous cache entry exists; this check is not
authentication.

`manifest_revision` is a source-local manifest generation. `0x0000` is reserved
as the no-known-revision query sentinel. A node MUST retain the same revision
across reboot, bus-off recovery, and ordinary admission sessions. It MUST
advance the revision whenever the canonical manifest bytes change and MUST NOT
reset the revision on reboot. The revision is compared for equality only; it is
not an ordered sequence number.

After entering `ACTIVE` following bootstrap or bus-off recovery, a node emits
one byte-identical advertisement at elapsed times 0, 250, 500, and 750 ms. The
node suppresses its local telemetry publishers until 1,000 ms after the first
advertisement. These four advertisements form the active-entry telemetry
reset sequence. Every local publisher starts its sequence at zero after this
reset sequence.

Each valid manifest advertisement is a telemetry reset marker. A receiver MUST
clear scalar sequence state and incomplete structured snapshot state for the
advertised source when it processes the advertisement. Repeated
advertisements with the same revision and fingerprint remain reset markers; they
do not invalidate a matching cached manifest.

An advertisement with either a different revision or a different fingerprint
indicates that the source's static inventory may be different. The receiver
MUST NOT activate a cached manifest unless both the advertised revision and
fingerprint match the cache entry bound to that UUID. A matching pair permits
the receiver to reuse its cached manifest; the telemetry reset does not require
manifest retrieval.

An advertisement neither confirms nor renews node ownership, nor does it act
as a heartbeat.

### Active-session manifest immutability

The canonical manifest, including its revision and fingerprint, MUST remain
unchanged for the entire `ACTIVE` session. A node MUST reject or defer any
local operation that would change the manifest bytes, revision, or fingerprint
while it is `ACTIVE`; it MUST NOT advertise or transfer a replacement
manifest during that session. Changes that do not alter the canonical
manifest are outside this rule.

A changed manifest may become current only in a subsequent admission session.
After the node next enters `ACTIVE`, the existing four-advertisement process
and immutable transfer procedure publish the new snapshot. No live manifest
update, handoff, or revision-transition procedure exists in v0.1.

The finite revision is modulo `uint16_t` except that `0x0000` remains reserved:
after `0xFFFF`, the next revision is `0x0001`. Revision wrap is not an ordering
event and MUST NOT reset or alter the hardware UUID. A receiver that retains a
pre-wrap cache can theoretically reuse stale data if the wrapped revision and
the 32-bit fingerprint both match; this is an accepted low-probability v0.1
limitation documented in [design decisions](../../design-decisions.md).
Implementations SHOULD retain only the bounded cache depth appropriate for
their available memory and flash.

## Manifest query
**COMMON**


`rebus_msg_manifest_query_t` is an eight-byte payload sent to the target node:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `query_type`; `0x01` for current-manifest query |
| 1 | 1 | `uint8_t` | `requester_node_id` |
| 2 | 2 | `uint16_t` | `known_revision`; `0` means no cached manifest |
| 4 | 2 | `uint8_t[2]` | Reserved; MUST be zero |
| 6 | 1 | `uint8_t` | `manifest_format`; `0x01` requested |
| 7 | 1 | `uint8_t` | `flags`; MUST be zero in v0.1 |

The target MUST begin each transfer with one logical
`MANIFEST_TRANSFER_START` frame before its first chunk when `known_revision`
differs from the target's current manifest revision. It MAY answer with no
frames when the revision matches. A requester that has observed an
advertisement whose revision/fingerprint pair does not match its cache MUST
send `known_revision = 0`, even if its stale cache has a nonzero revision, so
the target cannot suppress the required replacement transfer. A query never
changes the source's telemetry cadence or sequence state.

A receiver that misses the start frame MUST discard subsequent orphan chunks
and MAY issue the query again subject to the query rate limit.

A source MUST rate-limit queries per requester and MUST coalesce equivalent
queries while one transfer for the same immutable snapshot is active. A single
broadcast transfer may satisfy every receiver that needs the current manifest
identity.
The v0.1 minimum interval between accepted queries from one requester to one
source is one second; excess queries are discarded without response.

## Manifest transfer start and chunks
**COMMON**


`rebus_msg_manifest_transfer_start_t` is a fixed eight-decoded-byte payload in
both profiles, sent by the source as a broadcast:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x03` for transfer start |
| 1 | 1 | `uint8_t` | `transfer_id`; source-local transfer identifier |
| 2 | 2 | `uint16_t` | `manifest_revision`; source-local revision |
| 4 | 4 | `uint32_t` | `manifest_fingerprint`; expected manifest fingerprint |

The source node ID is encoded in the CAN identifier. The source UUID is the
UUID currently bound by [discovery identity](../../discovery/identity.md) to that node ID; it is not repeated in this
payload. A receiver MUST dispatch the frame, but MUST NOT create UUID-bound
manifest state until that binding exists. A zero fingerprint is invalid.

If the receiver has a current valid advertisement for this source node ID and
identity generation, the start revision and fingerprint MUST equal that
advertisement's revision and fingerprint; otherwise the receiver MUST discard
the start. A receiver that has not observed a current advertisement MAY accept
a nonzero-revision, nonzero-fingerprint start after the UUID binding exists.

Every transfer MUST begin with one logical transfer-start frame before its
first chunk. The start establishes the immutable binding inherited by all
following chunks:

```text
(
    source_node_id,
    identity_generation,
    hardware_uuid,
    transfer_id,
    manifest_revision,
    manifest_fingerprint
)
```

The receiver MUST create a manifest assembly only from an accepted start
context. A chunk without a matching active start context MUST be discarded.
An identical duplicate start MUST leave the existing assembly and received
chunks unchanged. If a start arrives for the same source node ID, identity
generation, and transfer ID with a different revision or fingerprint, the
receiver MUST discard the prior incomplete assembly before creating the new
context. A source MUST NOT reuse a transfer ID concurrently for different
immutable snapshots. It MAY reuse an ID for the same snapshot or after the
prior context has been invalidated.

### Selected chunk length
**COMMON**

The accepted start is the sole source of a transfer's `transfer_id` binding;
the receiver MUST NOT stage chunk header bytes to discover or combine a
transfer ID.

#### Classic CAN
**CLASSIC CAN**

For Classic, the context's selected decoded length is eight and its data area
is four bytes.

#### CAN FD
**CAN FD**

For FD, the first accepted chunk after the start MUST have `chunk_index = 0`
and a decoded length `L` in `{8, 12, 16, 20, 24, 32, 48, 64}`. That chunk pins
`L` and the data-area length `D = L - 4` for the assembly before any later
chunk is buffered. Chunks other than index zero received before the FD decoded
length is pinned are discarded.

### Common chunk validation
**COMMON**

A chunk MUST match its active start context's `transfer_id` and selected
decoded length. A transfer-ID or decoded-length mismatch, or a conflicting
duplicate chunk, MUST discard and evict the assembly.

The selected-profile gate rejects wrong physical forms before transport dispatch
without altering an existing assembly; it never infers a profile from traffic.

`rebus_msg_manifest_chunk_t` is a transfer-class payload sent by the source as
a broadcast:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x02` for transfer chunk |
| 1 | 1 | `uint8_t` | `transfer_id`; source-local transfer identifier |
| 2 | 2 | `uint16_t` | `chunk_index`; zero-based |
| 4 | `D` | `uint8_t[D]` | Canonical manifest bytes at this chunk offset |

The source MUST send chunks in increasing `chunk_index` order for a transfer.
Once the selected length is pinned, a receiver MAY accept them out of order,
MUST discard duplicate indexes after the first identical copy, and MUST discard
a conflicting duplicate. The maximum manifest length is 65,535 bytes.

### Chunk-index ceilings

#### Classic CAN
**CLASSIC CAN**

For `D = 4`, the maximum valid `chunk_index` is
`ceil(65,535 / D) - 1 = 16,383`; a receiver MUST reject a larger index.

#### CAN FD
**CAN FD**

For a permitted selected FD data-area length `D`, the maximum valid
`chunk_index` is `ceil(65,535 / D) - 1`; a receiver MUST reject a larger index.

### Transfer assembly and completion
**COMMON**

The transfer is an immutable snapshot. Every chunk accepted under a start
context MUST belong to that context's source UUID, manifest revision,
manifest fingerprint, and transfer ID. A source MUST NOT modify a transfer
after its first chunk. A receiver MUST reject a completed transfer unless its
header hardware UUID, revision, and fingerprint exactly match the start
context, in addition to the existing length and encoding checks. Transfer
timeout, retry, and cache replacement are local behaviors; a receiver MUST
NOT publish incomplete manifest data as current inventory.

The first bytes of the transfer are the [manifest header](envelope.md#header).
The header supplies the total byte length. For the assembly's data-area length
`D`, completion requires all `N = ceil(total_length / D)` chunks covering that
length. If `total_length` is not a multiple of `D`, the source MUST fill the
unused bytes in the final chunk's `manifest_data` area with zero. A receiver
MUST validate those unused bytes as zero and reject the transfer if any is
nonzero; the padding is not part of the canonical manifest. A deployment MUST
configure one maximum canonical manifest length in `24..65,535` bytes for all
its senders and receivers. A source MUST NOT advertise or transfer a manifest
above that limit. Once the 24-byte header is available, a receiver MUST reject
an assembly whose `total_length` exceeds the configured limit (or is smaller
than the header); a missing final partial chunk is invalid. The wire-format
ceiling and chunk-index bound remain 65,535 bytes.

A changed UUID binding MUST invalidate every incomplete transfer context for
the prior identity generation. A valid advertisement with a different revision
or fingerprint MUST invalidate incomplete transfer contexts whose expected
identity differs; a matching identity may retain its context and cache.

A source MAY serve only one active transfer at a time. It MUST rate-limit
broadcast transfers to one start per requester per second and MUST avoid
starting an equivalent transfer more than once per 250 ms. These limits bound
bus load without preventing a broadcast response from serving multiple
requesters.

## Transfer deadline commissioning inputs
**COMMON**


The deployment MUST commission a completion deadline and an inactivity deadline
for manifest transfer. Its proof MUST cover the deployment-wide configured
maximum manifest length.

The completion deadline bounds the elapsed time from accepted start through all
`N` chunks; the inactivity deadline bounds the interval after an accepted start
or chunk without the next required chunk. A receiver MUST evict an incomplete
assembly when either deadline expires.

### Classic CAN
**CLASSIC CAN**

The Classic proof uses the fixed eight-decoded-byte transfer start, `D = 4`,
`N = ceil(maximum_manifest_size / D)`, Classic's commissioned worst-case
elapsed frame costs, the source's bounded inter-chunk scheduling delay, and the
bounded competing-traffic and recovery assumptions.

### CAN FD
**CAN FD**

The FD proof covers every permitted selected chunk length and uses the fixed
eight-decoded-byte transfer start, `D = L - 4`,
`N = ceil(maximum_manifest_size / D)`, the selected profile's commissioned
worst-case elapsed frame costs, the source's bounded inter-chunk scheduling
delay, and the bounded competing-traffic and recovery assumptions.



## Cache and identity rules
**COMMON**


Discovery establishes the current mapping between a hardware UUID and a node ID.
The inventory cache is keyed by:

```text
(hardware_uuid, manifest_revision, manifest_fingerprint)
```

The cache entry MUST retain the complete validated canonical manifest and its
full locally computed SHA-256 digest. The revision and fingerprint are
wire-visible lookup fields; the full digest protects cache bookkeeping and
complete-manifest replacement but is not transmitted in v0.1 advertisements.

A node ID alone MUST NOT select a cached manifest. Node IDs are transport
locators and may be reassigned after a claim conflict, reboot, or recovery.
When an advertisement arrives, the receiver first resolves its current source
node ID to the UUID established by discovery, then looks up the UUID-bound
revision and fingerprint.

A late-joining receiver that lacks the current UUID mapping MAY send the
[WHO_ARE_YOU query](../who-are-you.md) to the specific source node ID or
broadcast it. After correlating the selected active node's identity reminder,
the receiver MUST establish or refresh the UUID binding for that source node
ID before accepting a transfer start or activating a UUID-bound manifest cache.
A different UUID replaces a previous binding for subsequent identity
resolution and invalidates any in-progress manifest transfer associated with
the prior identity generation. The reminder does not replace manifest
validation or authorize a configuration operation.

A matching cached manifest may be activated immediately after the advertisement
is validated only when both its revision and fingerprint match the advertised
identity and its complete canonical bytes remain locally valid. A missing or
mismatching cache entry requires a query before the manifest is considered
available. A full broadcast transfer may be cached by all observing nodes, even
when only one node sent the query.

The [manifest envelope](envelope.md)'s hardware UUID MUST match both the UUID currently bound to the
source node ID and the start context. A mismatch invalidates the transfer and
MUST NOT replace a cache entry. A completed transfer MUST be hashed from its
canonical bytes before cache replacement. If an existing cache entry has the
same UUID and revision but different canonical bytes, the receiver MUST reject
the replacement and retain the previous valid entry. A fingerprint match is not
authentication and does not grant access to configuration operations.
