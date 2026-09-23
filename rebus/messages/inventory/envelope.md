SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory manifest envelope

## Manifest envelope
**COMMON**


The manifest is a canonical binary record stream. All integer fields use fixed
widths and [little-endian encoding](../../encoding.md). No compiler struct layout, alignment,
padding, or host enum size is part of the format.

### Header

The first 24 bytes are the manifest header:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `format`; `0x01` |
| 1 | 1 | `uint8_t` | `header_length`; `24` |
| 2 | 2 | `uint16_t` | `total_length`; header plus all records |
| 4 | 2 | `uint16_t` | `revision`; source-local manifest generation; see [manifest transport](transport.md) for advancement, wrap, and comparison rules |
| 6 | 2 | `uint16_t` | `record_count`; top-level record count |
| 8 | 4 | `uint32_t` | `fingerprint`; [SHA-256 fingerprint](transport.md#manifest-advertisement) |
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
properties. The [inventory registries](registries.md) define the stable identifiers
for resource kinds, semantic values, units, scalar types, relation kinds,
parameter kinds, and constraints; [the model](model.md) defines their semantic
record meanings.
