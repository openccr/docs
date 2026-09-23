SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus wire encoding

## Scope

This document owns payload serialization and CAN data-field rules. Message
semantics and identifier assignment belong to the [profile](profile.md) and
[discovery entrypoint](discovery/README.md).

## Payload model

**COMMON**

Physical payload admission begins with the commissioned selected profile in
[profile](profile.md). The profile gate supplies the accepted frame form.

Message owners apply their fixed or transfer-class decoded-length rules after
the selected profile supplies the decoded length.

The fixed logical messages below are exactly eight decoded bytes in both
profiles:

| Payload | Decoded length |
|---|---:|
| `rebus_msg_node_claim_t` | 8 bytes |
| `CLAIM_REJECT` UUID payload | 8 bytes |
| `rebus_msg_who_are_you_t` | 8 bytes |
| `rebus_msg_uuid_collision_t` | 8 bytes |
| `rebus_msg_manifest_advertise_t` | 8 bytes |
| `rebus_msg_manifest_query_t` | 8 bytes |
| `rebus_msg_manifest_transfer_start_t` | 8 bytes |
| `rebus_telemetry_frame_t` | 8 bytes |
| `rebus_telemetry_control_request_t` | 8 bytes |

Manifest and structured-snapshot chunks are transfer-class payloads. Each has
a four-byte transfer header followed by a profile data area. Their owning
message documents define transfer semantics and accepted chunk lengths.

### Classic CAN
**CLASSIC CAN**

The Classic data area is `D=4` bytes.

### CAN FD
**CAN FD**

The FD data area is `D=decoded_length-4` bytes.

## Byte order
**COMMON**

All multi-byte values use little-endian payload-octet encoding. For an
`N`-octet value `v`, byte `i` is `(v >> (8 * i)) & 0xff`; signed integers use
the corresponding two's-complement pattern and binary32 uses its IEEE-754
interchange bits. CAN then serializes each payload octet bit 7 first. Payload
octet order never changes physical CAN bit order.

```text
0x11223344 -> 44 33 22 11
1.0f       -> 00 00 80 3F
```

## Declared layout
**COMMON**

Declared layouts establish field widths and ordering:

- `rebus_msg_node_claim_t`: `hardware_uuid[8]`;
- `rebus_msg_who_are_you_t`: message type `[1]`, requester node ID `[1]`,
  reserved bytes `[6]`;
- `rebus_msg_manifest_advertise_t`: message type `[1]`, format `[1]`,
  manifest revision `[2]`, manifest fingerprint `[4]`;
- `rebus_msg_manifest_query_t`: query type `[1]`, requester ID `[1]`,
  known revision `[2]`, reserved bytes `[2]`, format `[1]`, flags `[1]`;
- `rebus_msg_manifest_transfer_start_t`: message type `[1]`, transfer ID `[1]`,
  manifest revision `[2]`, manifest fingerprint `[4]`;
- `rebus_msg_manifest_chunk_t`: message type `[1]`, transfer ID `[1]`,
  chunk index `[2]`, then a profile data area;
- `rebus_telemetry_frame_t`: publisher `[1]`, sequence `[1]`, status flags
  `[1]`, context `[1]`, then a four-byte context-selected value;
- `rebus_msg_structured_snapshot_chunk_t`: publisher `[1]`,
  snapshot sequence `[1]`, chunk index `[1]`, chunk count `[1]`, then a
  profile data area;
- `rebus_telemetry_control_request_t`: opcode `[1]`, target node ID `[1]`,
  publisher `[1]`, context `[1]`, period `[2]`, duration `[2]`.

Manifest transfer semantics are defined by
[manifest transport](messages/inventory/transport.md), while
[manifest envelope](messages/inventory/envelope.md) owns canonical manifest
envelope semantics. [Scalar telemetry](messages/telemetry/scalar.md) owns
scalar telemetry semantics. [Structured snapshots](messages/telemetry/structured.md)
own structured snapshot semantics and completion rules.

## Frame format, DLC, and padding
**COMMON**

The selected profile's gate in [profile](profile.md) is authoritative.

Fixed logical messages require exactly eight decoded bytes in both profiles.

For a final transfer chunk, unused bytes in the profile data area MUST be zero
and are not logical bytes. This applies to the Classic four-byte data area and
the FD `decoded_length - 4` data area. A receiver MUST reject nonzero unused
data-area bytes. Fixed-size logical data fields may contain canonical
zero-filled unused bytes.

A receiver MUST discard an invalid, unsupported, or inconsistent physical
payload without response.

### Classic CAN
**CLASSIC CAN**

Every accepted Classic physical payload has raw DLC 8 and decoded length 8.

### CAN FD
**CAN FD**

This document exclusively maps an accepted raw FD DLC to its decoded byte
length. Raw DLC `0..8` maps to the same decoded length. Raw DLC `9..15` maps,
respectively, to decoded lengths `12`, `16`, `20`, `24`, `32`, `48`, and `64`
bytes.

An FD decoder MUST map raw DLC to decoded length and validate that length
against the message's rule before reading a four-byte transfer header or
subtracting four to obtain its data-area length.

## Declaration requirements
**COMMON**

Use standard C typedef notation for named declarations:

```c
typedef uint16_t rebus_manifest_revision_t;
typedef uint16_t rebus_resource_id_t;
typedef uint16_t rebus_semantic_id_t;

typedef struct {
    uint8_t low;
    uint8_t high;
} rebus_packed_gf_u8_t;
```

For wire fields, use the fixed-width integer types from `<stdint.h>`:
`uint8_t`, `uint16_t`, `uint32_t`, and `uint64_t`, as specified by the
declared layout. Encode and decode those fields explicitly in little-endian
octet order. A binary32 value MUST use IEEE-754 binary32 interchange bits;
implementations using C `float` MUST verify that it is binary32 or serialize
through a `uint32_t` bit pattern.

Enum constants MAY name manifest record kinds, resource kinds, semantics,
units, contexts, and other registries, but the wire field MUST use its
declared fixed-width integer representation. Do not
derive the wire format from enum size, host struct layout, alignment, padding,
or compiler-specific packing attributes. Encoders and decoders MUST serialize
the declared octets directly.
