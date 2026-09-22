SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus wire encoding

## Scope

This document owns payload serialization and CAN data-field rules. Message
semantics and identifier assignment belong to the [profile](profile.md) and
[discovery entrypoint](discovery/README.md).

## Payload model

Each physical frame carries one complete eight-byte declared payload in the
CAN data field. Manifest content and structured telemetry snapshots are the
logical multi-frame transfers defined by their owning message documents; each
transfer chunk is still one complete eight-byte CAN payload.

| Payload | Length |
|---|---:|
| `rebus_msg_node_claim_t` | 8 bytes |
| `CLAIM_REJECT` UUID payload | 8 bytes |
| `rebus_msg_who_are_you_t` | 8 bytes |
| `rebus_msg_manifest_advertise_t` | 8 bytes |
| `rebus_msg_manifest_query_t` | 8 bytes |
| `rebus_msg_manifest_transfer_start_t` | 8 bytes |
| `rebus_msg_manifest_chunk_t` | 8 bytes |
| `openccr_telemetry_frame_t` | 8 bytes |
| `rebus_msg_structured_snapshot_chunk_t` | 8 bytes |
| `rebus_telemetry_control_request_t` | 8 bytes |

All physical frames fit in a classic CAN data field. Rebus v0.1 prohibits CAN
FD framing, including an eight-byte CAN FD frame.

## Byte order

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
  chunk index `[2]`, manifest data `[4]`;
- `openccr_telemetry_frame_t`: publisher `[1]`, sequence `[1]`, status flags
  `[1]`, context `[1]`, then a four-byte context-selected value;
- `rebus_msg_structured_snapshot_chunk_t`: publisher `[1]`,
  snapshot sequence `[1]`, chunk index `[1]`, chunk count `[1]`,
  snapshot data `[4]`;
- `rebus_telemetry_control_request_t`: opcode `[1]`, target node ID `[1]`,
  publisher `[1]`, context `[1]`, period `[2]`, duration `[2]`.

Manifest transfer semantics are defined by
[manifest transport](messages/inventory/transport.md), while
[manifest envelope](messages/inventory/envelope.md) owns canonical manifest
envelope semantics. [Scalar telemetry](messages/telemetry/scalar.md) owns
scalar telemetry semantics. [Structured snapshots](messages/telemetry/structured.md)
own structured snapshot semantics and completion rules.

## Frame format, DLC, and padding

Every Rebus v0.1 frame is a Classic CAN 2.0A base-format data frame (`IDE=0`,
`RTR=0`) with raw DLC 8 and exactly eight data bytes. CAN FD, BRS, ESI,
extended frames, remote frames, and all other DLC values MUST be discarded
before message decoding without response. A conforming receive path must
retain the format, raw DLC, and data-length metadata needed to enforce that
gate.

There is no variable-length trailing padding in a physical payload. Fixed-size
logical data fields may contain canonical zero-filled unused bytes. For a final
manifest chunk whose `total_length` is not a multiple of four, the unused
bytes in its four-byte `manifest_data` field MUST be zero and are excluded from
the canonical manifest; receivers MUST reject nonzero unused bytes. For the
final structured snapshot chunk, unused bytes in its four-byte data field MUST
be zero and are excluded by the manifest's `encoded_length`.

## Declaration requirements

Use standard C typedef notation for named declarations:

```c
typedef uint16_t openccr_manifest_revision_t;
typedef uint16_t openccr_resource_id_t;
typedef uint16_t openccr_semantic_id_t;

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
