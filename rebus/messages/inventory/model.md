SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory model

## Resource model
**COMMON**


This document uses the [manifest envelope](envelope.md) for record and nested-TLV framing and the [inventory registries](registries.md) for assigned identifiers and registry validation.

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

The `resource_kind` field uses the [resource-kind registry](registries.md#resource-kinds).
A resource may have multiple outputs and parameters.

### Repeated assemblies and sensor groups

Repeated physical systems are represented by instance resources, not by
semantic IDs containing ordinal names.

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

The `origin` field uses the [output-origin registry](registries.md#output-origins).

`transform_id` is zero for direct and raw outputs. A derived output MUST name
the transform that produced it and MUST have one or more `DERIVED_FROM` or
`REQUIRES_INPUT` relations to exact output references.

Structured outputs use the output's `value_type` and [nested shape properties](registries.md#output-shapes).

The shape, dimension names, element type, element unit, and snapshot policy
are part of the output descriptor. A matrix such as gas saturation is one
logical output even when its wire representation spans multiple frames.

### Structured output encoded length
**COMMON**

For a `STRUCTURED_SNAPSHOT` output, nested properties MUST include
`encoded_length`, including the mandatory four-byte snapshot header, and the
exact dimension sizes. The encoded length MUST be at least four bytes.

#### Classic CAN
**CLASSIC CAN**

Under `REBUS_CLASSIC_0_1`, it MUST be no greater than 1,020 bytes.

#### CAN FD
**CAN FD**

Under `REBUS_FD_0_1`, it MUST be no greater than `255 * (L - 4)` for the
selected permitted decoded chunk length `L`, and never more than 15,300 bytes.

### Output metadata, relations, and parameters
**COMMON**

These profile-specific transfer bounds do not alter the descriptor's shape,
dimension names, element type, element unit, or snapshot policy.

Each output MAY declare a [delivery class](registries.md#delivery-classes) and request policy:

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

The [endpoint-scope registry](registries.md#endpoint-scopes) defines the assigned scope values.

The [endpoint-kind registry](registries.md#endpoint-kinds) defines the assigned kind values.

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
**COMMON**


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
