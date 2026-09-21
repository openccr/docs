SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory manifest messages

## Scope

This document defines Rebus inventory manifests: the static description of a
node's physical resources, software modules, telemetry outputs, relationships,
and configuration interfaces. It owns the manifest wire messages, the
fragmented transfer, manifest cache rules, and manifest content envelope.

A manifest is descriptive. It does not authorize configuration writes, prove
firmware integrity, or replace the node-claim procedure.

The manifest is the authoritative source for concrete node properties. Rebus
has no separate wire-level role bitmask. A receiver derives any local service
classification from the resources and interfaces present in the manifest.

## Identifier assignments

Manifest messages use two identifier classes:

| Message | CAN identifier | Direction | Payload |
|---|---|---|---|
| Manifest query | `(0x01 << 7) \| target_node_id` (`0x081–0x0FF`) | unicast to target | Query opcode, requester ID, known revision |
| Manifest advertise/start/chunk | `(0x06 << 7) \| source_node_id` (`0x301–0x37F`) | source broadcast | Advertisement with revision and fingerprint, transfer start, or transfer chunk |

The query is the explicit subject-addressing exception in the profile: the low
seven identifier bits name the target node. The requester ID is also present
in the payload for rate limiting and request correlation. Advertisements,
transfer starts, and chunks use the low seven bits as the source node ID.

All four messages are exactly eight-byte Classic CAN data payloads. The
receiver applies the profile frame gate before message-specific validation.

## Manifest advertisement

`rebus_msg_manifest_advertise_t` is an eight-byte payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x01` for advertisement |
| 1 | 1 | `uint8_t` | `manifest_format`; `0x01` for this format |
| 2 | 2 | `uint16_t` | `manifest_revision`; source-local manifest generation |
| 4 | 4 | `uint32_t` | `manifest_fingerprint`; cache fingerprint hint |

All multi-octet fields use the little-endian encoding in
[wire encoding](../encoding.md).

The fingerprint is the little-endian integer formed from the first four bytes
of SHA-256 over the canonical manifest bytes, with the fingerprint field in the
manifest header zeroed for hashing. It is a cache and lookup hint, not an
integrity or authorization credential, and MUST NOT be the sole freshness
decision. The complete manifest remains the validation source. A fingerprint of
`0x00000000` is reserved and MUST NOT be advertised or stored as a current
manifest fingerprint; it is the query sentinel for “no cached manifest”.

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
limitation documented in [design decisions](../design-decisions.md).
Implementations SHOULD retain only the bounded cache depth appropriate for
their available memory and flash.

## Manifest query

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

`rebus_msg_manifest_transfer_start_t` is an eight-byte payload sent by the
source as a broadcast:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x03` for transfer start |
| 1 | 1 | `uint8_t` | `transfer_id`; source-local transfer identifier |
| 2 | 2 | `uint16_t` | `manifest_revision`; source-local revision |
| 4 | 4 | `uint32_t` | `manifest_fingerprint`; expected manifest fingerprint |

The source node ID is encoded in the CAN identifier. The source UUID is the
UUID currently bound by discovery to that node ID; it is not repeated in this
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

`rebus_msg_manifest_chunk_t` is an eight-byte payload sent by the source as a
broadcast:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `message_type`; `0x02` for transfer chunk |
| 1 | 1 | `uint8_t` | `transfer_id`; source-local transfer identifier |
| 2 | 2 | `uint16_t` | `chunk_index`; zero-based |
| 4 | 4 | `uint8_t[4]` | Canonical manifest bytes at this chunk offset |

Each chunk carries four manifest bytes. The source MUST send chunks in
increasing `chunk_index` order for a transfer. A receiver MAY accept them
out of order, MUST discard duplicate indexes after the first identical copy,
and MUST discard a conflicting duplicate. The maximum manifest length is
65,535 bytes; the maximum chunk index is therefore 16,383.

The transfer is an immutable snapshot. Every chunk accepted under a start
context MUST belong to that context's source UUID, manifest revision,
manifest fingerprint, and transfer ID. A source MUST NOT modify a transfer
after its first chunk. A receiver MUST reject a completed transfer unless its
header hardware UUID, revision, and fingerprint exactly match the start
context, in addition to the existing length and encoding checks. Transfer
timeout, retry, and cache replacement are local behaviors; a receiver MUST
NOT publish incomplete manifest data as current inventory.

The first bytes of the transfer are the manifest header. The header supplies
the total byte length, so completion is determined by receiving every chunk
covering that length. If `total_length` is not a multiple of four, the source
MUST fill the unused bytes in the final chunk's four-byte `manifest_data` field
with zero. A receiver MUST validate those unused bytes as zero and reject the
transfer if any is nonzero; the padding is not part of the canonical manifest.
The canonical manifest length MUST be nonzero and MUST be no greater than
65,535 bytes. A missing final partial chunk is invalid.

A changed UUID binding MUST invalidate every incomplete transfer context for
the prior identity generation. A valid advertisement with a different revision
or fingerprint MUST invalidate incomplete transfer contexts whose expected
identity differs; a matching identity may retain its context and cache.

A source MAY serve only one active transfer at a time. It MUST rate-limit
broadcast transfers to one start per requester per second and MUST avoid
starting an equivalent transfer more than once per 250 ms. These limits bound
bus load without preventing a broadcast response from serving multiple
requesters.

## Cache and identity rules

Discovery establishes the current mapping between a hardware UUID and a node
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
[WHO_ARE_YOU query](who-are-you.md) to the specific source node ID or
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

The manifest's hardware UUID MUST match both the UUID currently bound to the
source node ID and the start context. A mismatch invalidates the transfer and
MUST NOT replace a cache entry. A completed transfer MUST be hashed from its
canonical bytes before cache replacement. If an existing cache entry has the
same UUID and revision but different canonical bytes, the receiver MUST reject
the replacement and retain the previous valid entry. A fingerprint match is not
authentication and does not grant access to configuration operations.

## Manifest envelope

The manifest is a canonical binary record stream. All integer fields use fixed
widths and little-endian encoding. No compiler struct layout, alignment,
padding, or host enum size is part of the format.

### Header

The first 24 bytes are the manifest header:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `format`; `0x01` |
| 1 | 1 | `uint8_t` | `header_length`; `24` |
| 2 | 2 | `uint16_t` | `total_length`; header plus all records |
| 4 | 2 | `uint16_t` | `revision`; source-local monotonic manifest revision |
| 6 | 2 | `uint16_t` | `record_count`; top-level record count |
| 8 | 4 | `uint32_t` | `fingerprint`; SHA-256 fingerprint described above |
| 12 | 8 | `uint64_t` | `hardware_uuid`; UUID that owns the manifest |
| 20 | 2 | `uint16_t` | `flags`; must be zero in v0.1 |
| 22 | 2 | `uint16_t` | reserved; must be zero |

The canonical record stream follows immediately after the header. A manifest
with an unknown format, nonzero reserved fields, inconsistent length, or
mismatching record count is invalid.

### Top-level records

Each record is a length-delimited TLV:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `record_kind` |
| 1 | 1 | `uint8_t` | `record_flags`; reserved, must be zero |
| 2 | 2 | `uint16_t` | `record_length`; value bytes that follow |
| 4 | N | bytes | Record value |

Unknown record kinds MAY be skipped using `record_length`. A receiver MUST NOT
infer semantics from an unknown record or from a numeric value without its
registry entry.

The initial record-kind assignments are:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x01` | `RECORD_RESOURCE` | Physical, virtual, or software resource |
| `0x02` | `RECORD_OUTPUT` | Telemetry output of a resource |
| `0x03` | `RECORD_RELATION` | Relationship between resources |
| `0x04` | `RECORD_PARAMETER` | Configuration parameter exposed by a resource |
| `0x05–0x7F` | reserved | Must not be sent in v0.1 |
| `0x80–0xFF` | private | Deployment-private; not interoperable |

Record values use nested length-delimited TLVs where a record needs extensible
properties. The normative registry tables below define the stable identifiers
for resource kinds, semantic values, units, scalar types, relation kinds,
parameter kinds, and constraints.

## Resource model

Every resource has a stable `resource_id` scoped to its node and manifest. A
resource ID MUST remain stable while the node remains active and MUST NOT be
reused for a different resource within one manifest revision.

A resource record contains at minimum:

```text
resource_id      uint16
resource_kind    uint16
resource_flags   uint16
property_count   uint16
properties       nested TLVs
```

`resource_kind` identifies the class of thing, not its current value. The
initial registry must distinguish at least physical sensor, actuator, derived
value, software module, and interface/controller resource. A resource may have
multiple outputs and parameters.

### Repeated assemblies and sensor groups

Repeated physical systems are represented by instance resources, not by
semantic IDs containing ordinal names. The initial resource-kind registry
supports:

| Resource kind | Purpose |
|---|---|
| `LOOP_INSTANCE` | One rebreather loop |
| `SCRUBBER_INSTANCE` | One scrubber assembly |
| `GAS_CELL_BANK` | Group of cells measuring one gas in one assembly |
| `GAS_CELL` | One physical gas cell |
| `TEMPERATURE_STICK` | One multi-channel temperature assembly |
| `DECOMPRESSION_ENGINE` | One calculation module |
| `MEASUREMENT_SITE` | Physical point or medium being measured |

Each `GAS_CELL` MAY expose multiple outputs. Its properties identify
`measured_gas`, `technology`, and `interface`; its relations identify the
containing cell bank and loop. A `GAS_CELL_BANK` declares `expected_count`.
For example, two loop instances may each contain one oxygen bank with five
cells, one carbon-dioxide bank with one cell, and one CF4 bank with one cell.
Cell `instance_index` is scoped to its bank and is not a network identity.

A `TEMPERATURE_STICK` is one resource with a fixed-array or structured-snapshot
output. Its descriptor declares the element semantic, unit, count, and index
meaning. A decompression engine may expose one matrix output with dimensions
`[gas, tissue]`, such as `[4, 16]` or `[4, 32]`; the dimension values and gas
ordering are manifest properties, not separate semantic IDs.

An output record binds a resource to a telemetry publisher:

```text
resource_id       uint16
publisher_id      uint8
semantic_id       uint16
unit_id           uint8
value_type        uint8
telemetry_context uint8
origin            uint8
transform_id      uint16
flags             uint8
```

`publisher_id` is the node-local ID used in telemetry frames. The manifest is
the authority that gives `(source_node_id, publisher_id)` its meaning. The
`semantic_id`, `unit_id`, `value_type`, `origin`, and `transform_id` are
registry references; receivers MUST reject or quarantine a telemetry stream
whose manifest record is invalid.

Output-specific properties use nested TLVs. An output with a gas-dependent
semantic MUST carry a `gas_species` property. Structured outputs MUST carry
their shape and dimension properties. These properties are part of the output
descriptor and are not inferred from the semantic ID or numeric value.

`origin` distinguishes how the output was produced:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x01` | `ORIGIN_DIRECT_SENSOR` | Directly reported sensor result |
| `0x02` | `ORIGIN_RAW_INTERFACE` | Low-level interface signal, such as mV |
| `0x03` | `ORIGIN_DERIVED_LOCAL` | Calculated by the source node |
| `0x04` | `ORIGIN_DERIVED_EXTERNAL` | Calculated elsewhere and imported |

`transform_id` is zero for direct and raw outputs. A derived output MUST name
the transform that produced it and MUST have one or more `DERIVED_FROM` or
`REQUIRES_INPUT` relations to exact output references.

Structured outputs use the output's `value_type` and nested shape properties:

```text
SCALAR
FIXED_ARRAY
MATRIX
PACKED_TISSUE_VECTOR
STRUCTURED_SNAPSHOT
```

The shape, dimension names, element type, element unit, and snapshot policy
are part of the output descriptor. A matrix such as gas saturation is one
logical output even when its wire representation spans multiple frames.

For a `STRUCTURED_SNAPSHOT` output, nested properties MUST include
`encoded_length`, including the four-byte snapshot header, and the exact
dimension sizes. The encoded length MUST be no greater than 1,020 bytes for
the v0.1 structured snapshot transport.

Each output MAY declare a `delivery_class` and request policy:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x01` | `DELIVERY_CRITICAL` | Normal publication and prompt current-state requests |
| `0x02` | `DELIVERY_OPERATIONAL` | Normal publication and bounded requests |
| `0x03` | `DELIVERY_ADVISORY` | May be deferred or omitted under bus load |
| `0x04` | `DELIVERY_DIAGNOSTIC` | Best effort; requests may be ignored |

The request policy may specify `minimum_request_interval_ms`. This metadata
informs source scheduling; it does not guarantee a response or authorize a
requester to exceed source-wide bus and resource limits. A source remains free
to rate-limit or ignore any request.

A relation record binds either resources or exact telemetry outputs. Its record
value is a nested TLV sequence in ascending tag order:

| Tag | Value | Wire type | Meaning |
|---:|---|---|---|
| `0x01` | subject endpoint | nested TLV | Relation subject |
| `0x02` | relation kind | `uint16_t` | Registry relation identifier |
| `0x03` | target endpoint | nested TLV | Relation target |

Each relation tag MUST occur exactly once. The nested TLV header is the same
four-octet header used by the manifest record stream; nested flags MUST be
zero. Unknown or duplicate relation tags invalidate the relation in v0.1.

Each endpoint value is itself a nested TLV sequence in ascending tag order:

| Tag | Value | Wire type | Presence |
|---:|---|---|---|
| `0x01` | endpoint scope | `uint8_t` | Required |
| `0x02` | endpoint kind | `uint8_t` | Required |
| `0x03` | resource ID | `uint16_t` | Required |
| `0x04` | publisher ID | `uint8_t` | Required for `OUTPUT`; forbidden for `RESOURCE` |
| `0x05` | hardware UUID | `uint64_t` | Required for `FOREIGN`; forbidden for `LOCAL` |

The endpoint scope registry is:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x00` | `ENDPOINT_LOCAL` | Resource or output in this manifest |
| `0x01` | `ENDPOINT_FOREIGN` | Resource or output in another node's manifest |

The endpoint kind registry is:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x00` | `ENDPOINT_RESOURCE` | The resource identified by the resource ID |
| `0x01` | `ENDPOINT_OUTPUT` | The resource output identified by publisher ID |

All required endpoint tags MUST occur exactly once, optional tags MUST follow
the presence rules above, and unknown or duplicate endpoint tags invalidate
the relation. A local endpoint's identity is the manifest owner's
`hardware_uuid`; it MUST NOT carry a UUID. A foreign endpoint carries the
complete stable UUID of the other node and MUST NOT use a node address as
identity. A foreign endpoint MUST NOT repeat the manifest owner's UUID; that
endpoint is local.

The receiver validates every local endpoint against the active manifest:
`resource_id` MUST exist, and an `OUTPUT` endpoint's `publisher_id` MUST be
declared by that resource. The relation kind MUST be an assigned,
non-reserved registry value. For a foreign endpoint, the UUID MUST be neither
all zero nor all ones. When the receiver has a complete validated manifest
bound to that UUID, the foreign `resource_id` MUST resolve against it; when
the endpoint kind is `OUTPUT`, its `publisher_id` MUST also be declared by
that foreign resource. If that manifest is unavailable, the relation remains
syntactically valid but unresolved and MUST NOT be exposed as an active
relation until resolution succeeds. A later manifest resolution that fails
invalidates the relation.

Relations that cannot encode a cross-node endpoint with
`ENDPOINT_FOREIGN` and its UUID MUST NOT be emitted. This supports
`DERIVED_FROM`, `REQUIRES_INPUT`, `MEASURES_AT`, `CONTROLS`, and `PART_OF`
without making a reassigned node address part of relation identity.

A parameter record describes a configuration interface, not its current value:

```text
resource_id       uint16
parameter_id      uint16
value_type        uint8
unit_id           uint8
parameter_flags   uint16
constraint_length uint16
constraints       bytes
```

A parameter record says that the resource exposes that parameter and how a
value is represented and constrained. Configuration get/set messages and
authorization are separate protocol work.

## Sensor output provenance

A `GAS_CELL` resource may expose different combinations of raw, direct, and
derived outputs:

| Interface | Output | Origin |
|---|---|---|
| Analog voltage | `CELL_VOLTAGE`, usually mV | `ORIGIN_RAW_INTERFACE` |
| Analog voltage | `GAS_PARTIAL_PRESSURE` | `ORIGIN_DERIVED_LOCAL` |
| PPM sensor | `GAS_CONCENTRATION`, ppm | `ORIGIN_DIRECT_SENSOR` or `ORIGIN_RAW_INTERFACE`, as specified by the device |
| PPM sensor | `GAS_PARTIAL_PRESSURE` | `ORIGIN_DERIVED_LOCAL` |
| Digital ppO₂ sensor | `GAS_PARTIAL_PRESSURE` | `ORIGIN_DIRECT_SENSOR` |

An output described as `GAS_PARTIAL_PRESSURE` MUST also identify its
`gas_species`. A locally derived result MUST identify its exact input output
and `transform_id`. For example, `PPM_TO_PARTIAL_PRESSURE` requires a total
pressure input; it MUST NOT be represented as an independent direct sensor
reading.

The manifest distinguishes raw interface values from calibrated sensor
measurements. A ppm value is not automatically a raw signal, and a digital
ppO₂ value is not automatically a local derivation.

## Registry population contract

Registry additions MUST be supplied as Markdown tables in the owning message
or manifest document. Every row requires:

| Column | Requirement |
|---|---|
| Value | Stable numeric wire ID, written in hexadecimal |
| Symbol | C-style uppercase identifier |
| Meaning | Precise semantic definition |
| Wire type | Fixed representation and width |
| Unit/constraints | Canonical unit, range, and invalid values where applicable |
| Relations | Required source/resource/parameter relationships |

Use the existing telemetry unit and context registries as the model for stable
numeric assignments. Do not assign a new unit or semantic code when an existing
registry entry has the exact meaning.

For each concrete node inventory, provide a YAML source description for review
alongside the normative tables. YAML is authoring input only; the wire format
remains canonical binary TLV. The minimum shape is:

```yaml
format: 1
revision: 1
resources:
  - id: 1
    kind: gas_cell
    properties:
      measured_gas: oxygen
      technology: galvanic
      interface: analog_voltage
    outputs:
      - publisher_id: 1
        semantic: cell_voltage
        origin: raw_interface
        unit: millivolts
        value_type: f32
      - publisher_id: 2
        semantic: gas_partial_pressure
        gas: oxygen
        origin: derived_local
        transform: oxygen_cell_calibration
        unit: millibars
        value_type: f32
    relations:
      - kind: derived_from
        subject: { resource: 1, publisher: 2 }
        target: { resource: 1, publisher: 1 }

  - id: 2
    kind: gas_cell
    properties:
      measured_gas: carbon_dioxide
      technology: electrochemical
      interface: ppm_output
    outputs:
      - publisher_id: 3
        semantic: gas_concentration
        gas: carbon_dioxide
        origin: direct_sensor
        unit: ppm
        value_type: f32
      - publisher_id: 4
        semantic: gas_partial_pressure
        gas: carbon_dioxide
        origin: derived_local
        transform: ppm_to_partial_pressure
        unit: millibars
        value_type: f32
    relations:
      - kind: derived_from
        subject: { resource: 2, publisher: 4 }
        target: { resource: 2, publisher: 3 }
      - kind: requires_input
        subject: { resource: 2, publisher: 4 }
        target: { resource: 6, publisher: 60 }

  - id: 3
    kind: gas_cell
    properties:
      measured_gas: oxygen
      technology: digital
      interface: digital_partial_pressure
    outputs:
      - publisher_id: 5
        semantic: gas_partial_pressure
        gas: oxygen
        origin: direct_sensor
        unit: millibars
        value_type: f32

  - id: 20
    kind: decompression_engine
    outputs:
      - publisher_id: 40
        semantic: gas_tissue_saturation
        origin: derived_local
        value_type: structured_snapshot
        shape: [4, 32]
        dimensions:
          - name: gas
            values: [oxygen, nitrogen, helium, carbon_dioxide]
          - name: tissue
            count: 32
        element:
          value_type: u8
          unit: percent
        encoded_length: 132
        delivery_class: advisory
        minimum_request_interval_ms: 5000
```

The example names are illustrative until their registry IDs and exact wire
constraints are assigned. Future content contributions should provide the
following registries first:

1. `resource_kind`: physical sensors, actuators, derived values, software
   modules, and interface/controller resources.
2. `semantic_id`: measurements, states, commands, and derived quantities.
3. `unit_id`: canonical units and conversion policy, reusing telemetry units
   where they have the exact same meaning.
4. `value_type`: scalar and structured wire representations, including size
   and encoding rules.
5. `output_origin`: direct sensor, raw interface, local derivation, or
   external derivation.
6. `transform_id`: calibration and conversion functions such as cell
   calibration and ppm-to-partial-pressure.
7. `gas_species`: gases measured or represented by an output.
8. `output_shape`: scalar, fixed array, matrix, packed tissue vector, or
   structured snapshot dimensions.
9. `relation_kind`: resource-to-resource and output-to-output relationships.
10. `parameter_id`: configuration properties and their ownership.
11. Constraint kinds: numeric bounds, enumerations, cardinality, table shapes,
   and update requirements.

A registry entry is not complete until its stable ID, wire representation,
validation rules, and semantic meaning are specified.
