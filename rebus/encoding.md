SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus wire encoding

## Scope

This document owns payload serialization and CAN data-field rules. Message
semantics and identifier assignment belong to the [profile](profile.md) and
[discovery](discovery.md) documents.

## Payload model

Each frame carries one complete declared payload in the CAN data field. The
largest declared payload is eight bytes:

| Payload | Length |
|---|---:|
| `rebus_msg_node_claim_t` | 8 bytes |
| `CLAIM_CONFIRM` UUID payload | 8 bytes |
| `rebus_msg_role_announce_t` | 8 bytes |
| `openccr_telemetry_frame_t` | 8 bytes |

All fit in a classic CAN data field. Rebus v0.1 prohibits CAN FD framing,
including an eight-byte CAN FD frame.

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
- `rebus_msg_role_announce_t`: role mask `[2]`, firmware hash `[4]`, configuration count `[2]`;
- `openccr_telemetry_frame_t`: publisher `[1]`, sequence `[1]`, status flags `[1]`, context `[1]`, then a four-byte context-selected value.

## Frame format, DLC, and padding

Every Rebus v0.1 frame is a Classic CAN 2.0A base-format data frame (`IDE=0`,
`RTR=0`) with raw DLC 8 and exactly eight data bytes. CAN FD, BRS, ESI,
extended frames, remote frames, and all other DLC values MUST be discarded
before message decoding without response. A conforming receive path must retain
the format, raw DLC, and data-length metadata needed to enforce that gate.

No trailing padding is part of any payload. There is no fragmentation header.

## Declaration requirements

Use standard C typedef notation for named declarations:

```c
typedef uint16_t openccr_role_mask_t;

enum {
    ROLE_NONE = 0x0000u,
    ROLE_TELEMETRY_NODE = 1u << 0,
    /* ... */
};

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

Enum constants MAY name roles, contexts, units, and other registries, but the
wire field MUST use its declared fixed-width integer representation. Do not
derive the wire format from enum size, host struct layout, alignment, padding,
or compiler-specific packing attributes. Encoders and decoders MUST serialize
the declared octets directly.
