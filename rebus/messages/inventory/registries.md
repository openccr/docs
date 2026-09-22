SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory registries

This document owns the assigned semantic inventory values and the registry-population contract. Record framing and record-kind assignments belong to the [manifest envelope](envelope.md); resource, output, relation, and parameter semantics belong to the [inventory model](model.md).

## Resource kinds

`resource_kind` identifies the class of thing, not its current value. The
initial registry must distinguish at least physical sensor, actuator, derived
value, software module, and interface/controller resource.

The initial resource-kind registry
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

## Output origins

`origin` distinguishes how the output was produced:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x01` | `ORIGIN_DIRECT_SENSOR` | Directly reported sensor result |
| `0x02` | `ORIGIN_RAW_INTERFACE` | Low-level interface signal, such as mV |
| `0x03` | `ORIGIN_DERIVED_LOCAL` | Calculated by the source node |
| `0x04` | `ORIGIN_DERIVED_EXTERNAL` | Calculated elsewhere and imported |

## Output shapes

Structured outputs use the output's `value_type` and nested shape properties:

```text
SCALAR
FIXED_ARRAY
MATRIX
PACKED_TISSUE_VECTOR
STRUCTURED_SNAPSHOT
```

## Value types

`value_type` entries define scalar and structured wire representations,
including size and encoding rules.

## Relation kinds

`relation_kind` entries define resource-to-resource and output-to-output
relationships.

## Delivery classes

Each output MAY declare a `delivery_class` and request policy:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x01` | `DELIVERY_CRITICAL` | Normal publication and prompt current-state requests |
| `0x02` | `DELIVERY_OPERATIONAL` | Normal publication and bounded requests |
| `0x03` | `DELIVERY_ADVISORY` | May be deferred or omitted under bus load |
| `0x04` | `DELIVERY_DIAGNOSTIC` | Best effort; requests may be ignored |

## Endpoint scopes

The endpoint scope registry is:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x00` | `ENDPOINT_LOCAL` | Resource or output in this manifest |
| `0x01` | `ENDPOINT_FOREIGN` | Resource or output in another node's manifest |

## Endpoint kinds

The endpoint kind registry is:

| Value | Symbol | Meaning |
|---:|---|---|
| `0x00` | `ENDPOINT_RESOURCE` | The resource identified by the resource ID |
| `0x01` | `ENDPOINT_OUTPUT` | The resource output identified by publisher ID |


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
