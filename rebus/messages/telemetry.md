SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Telemetry message

## Frame

A scalar telemetry frame is an eight-byte payload that carries one current
value from one logical publisher. Its fields separate stream identity,
loss detection, value status, and value interpretation:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `publisher_id`; node-local logical stream identifier |
| 1 | 1 | `uint8_t` | `sequence_id`; wrapping emission sequence for drop detection |
| 2 | 1 | `uint8_t` | `status_flags`; validity and alarm state |
| 3 | 1 | `uint8_t` | `context`; selects the value's meaning and representation |
| 4 | 4 | `uint8_t[4]` | Context-selected value bytes |

The fixed four-byte value area keeps every scalar emission within one
Classic CAN payload while allowing the context registry to choose the
representation. The frame does not carry a unit or a manifest resource ID;
the inventory output descriptor supplies the publisher's meaning, unit,
origin, and any structured shape.

Telemetry uses `CAN_ID = (0x07 << 7) | source_node_id` (`0x381–0x3FF`).
`publisher_id` is an 8-bit node-local logical publisher. On the wire, stream
identity remains `(source_node_id, publisher_id)`; receiver-local transport
state is additionally bound to the current `identity_generation` for that
source node ID. A receiver MUST apply the [profile frame gate](../profile.md)
before decoding or sequencing a frame.

## Manifest binding and descriptor acceptance

Before decoding, sequencing, assembling, or exposing telemetry, a receiver
MUST have a complete validated manifest currently bound to the source node ID's
hardware UUID and `identity_generation`, with the current
`manifest_revision` and `manifest_fingerprint`. A matching validated cache
entry activated from the current advertisement satisfies this requirement; an
advertisement without a validated manifest does not. If no such manifest is
available, the receiver MUST discard the telemetry frame.

The receiver MUST resolve the frame's `publisher_id` in that manifest. A scalar
frame is acceptable only when its `context` and value representation match the
publisher's output descriptor. A structured snapshot is acceptable only when
its format, encoded length, element representation, and shape match the
descriptor. A frame for an unknown publisher or a mismatching descriptor MUST
be discarded.

Frames discarded by this gate MUST NOT advance sequence state, create a
baseline, count as drops, or create an incomplete structured snapshot. The
receiver resumes normal sequencing only after the manifest is validated and
active.

`publisher_id` values are node-local `0x00–0xFF`; a node may therefore expose
at most 256 distinct logical publishers in the v0.1 telemetry namespace.
Publisher IDs are not network-global and are unrelated to manifest
`resource_id` values. A resource may expose multiple publishers, and a
structured publisher may represent many scalar elements.

`status_flags`:

| Bit | Symbol | Meaning |
|---:|---|---|
| 0 | valid | Value is valid |
| 1 | warning | Warning state |
| 2 | alarm | Alarm state |
| 3–7 | reserved | Must be zero |

A frame with any reserved `status_flags` bit set is invalid and is discarded
without advancing sequence state.

The four value bytes can encode binary32, signed or unsigned 32-bit
integers, a Boolean, packed gradient factors, four packed tissue saturation
values, or one packed tissue-gas pair. Context rules in this document select
exactly one representation; receivers must not infer it from host ABI or
payload value.

`publisher_id` is stable for one logical publisher while its source node remains
`ACTIVE` and MUST NOT be reassigned during that period. The active-entry
manifest-advertisement sequence creates a node-wide telemetry generation:
every local publisher's first scalar frame and first structured snapshot after
the 1,000-ms hold uses sequence zero, then scalar `sequence_id` and structured
`snapshot_sequence` advance independently modulo 256.

After the manifest binding and descriptor gate passes, each
`(source_node_id, publisher_id, identity_generation)` stream is processed as
follows. Absence of a last accepted sequence value means that the next valid
scalar frame is a baseline and is accepted regardless of its `sequence_id`. A
conforming publisher's first baseline is zero, but a receiver can miss it.
Otherwise, with `advance = received - last` as `uint8_t`, accept `1..127`
(`report advance - 1 drops`), discard `0` as duplicate, and discard `128..255`
as stale. Each valid manifest advertisement clears scalar sequence state and
incomplete structured snapshot state for its source. The next valid frame from
each publisher is therefore a new baseline. A discovery UUID remap also
discards all sequence state from the prior identity generation. Silence does
not clear sequence state.

Structured snapshot ordering uses the same modulo comparison explicitly. A
source increments `snapshot_sequence` exactly once when it generates a new
logical snapshot; every chunk of that snapshot carries the same value. The
source MUST increment it modulo 256, including the `0xFF` to `0x00` wrap, and
MUST NOT reset it or reuse a value except as required by that modulo wrap
within the same active identity generation. Reusing sequence zero is otherwise
permitted only at the active-entry reset or after a UUID-binding reset.

For each structured stream, a receiver tracks the last committed sequence and
at most one pending assembly. If neither exists, the first valid chunk starts a
pending baseline and the first complete valid snapshot is accepted regardless
of its sequence. If a pending assembly exists, a chunk with its sequence may
arrive in any order. A different sequence is compared against the pending
sequence using `advance = received - pending` as `uint8_t`: `1..127` is newer
and supersedes the pending assembly, `0` is a duplicate, and `128..255` is
stale. After a snapshot is committed, the same comparison is made against the
last committed sequence. Sequence state advances only when all chunks pass
validation and the snapshot is committed. This makes a completed snapshot
authoritative without exposing a partial value or allowing late chunks from an
older snapshot to roll state back.

The modulo comparison is unambiguous only within a forward distance of 127
snapshots. If a receiver misses 128 or more logical snapshots, it follows the
defined stale/duplicate result until a reset boundary is observed; v0.1 has no
separate structured-snapshot reset message. A valid manifest advertisement
clears the committed sequence and any pending assembly, and a discovery UUID
remap does the same for the prior identity generation.

## Structured telemetry snapshots

Structured outputs declared by the inventory manifest use
`CAN_ID = (0x08 << 7) | source_node_id` (`0x401–0x47F`). This class is
deliberately lower arbitration priority than scalar telemetry. A structured
snapshot chunk is an eight-byte payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | `publisher_id` |
| 1 | 1 | `uint8_t` | `snapshot_sequence`; source-local generation |
| 2 | 1 | `uint8_t` | `chunk_index`; zero-based |
| 3 | 1 | `uint8_t` | `chunk_count`; `1..255` |
| 4 | 4 | `uint8_t[4]` | Logical snapshot bytes at this chunk offset |

`chunk_index` MUST be less than `chunk_count`. The maximum logical snapshot
length is 1,020 bytes. The inventory output descriptor supplies the exact
encoded length, shape, element type, and dimension semantics. Unused bytes in
the final four-byte chunk MUST be zero and are not part of the logical value.

The logical snapshot begins with a four-byte snapshot header:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | Snapshot format; `0x01` |
| 1 | 1 | `uint8_t` | Status flags; same valid/warning/alarm bits as scalar telemetry |
| 2 | 2 | `uint16_t` | Reserved; must be zero |

The encoded value follows the header. A receiver MUST commit a structured
snapshot only after every chunk for one `(source_node_id, publisher_id,
snapshot_sequence)` has arrived and the assembled length, format, element
representation, and shape match the active publisher descriptor in the
verified manifest. It MUST accept chunks in any order, but MUST NOT commit an
incomplete snapshot and MUST discard a conflicting duplicate chunk or a
snapshot whose sequence is duplicate or stale under the ordering rule above. A
newer sequence supersedes and discards an incomplete older snapshot. It MUST
NOT expose a partially assembled matrix or array as current state.

Structured snapshots have no application-level retransmission or negative
acknowledgement. CAN controller error recovery remains subject to the normal
physical-frame retransmission rules. A receiver that misses or discards a
snapshot may issue a current-state request; the source produces a new snapshot
if its delivery policy permits and MUST NOT replay the missing historical
snapshot. A response that is a new logical snapshot receives the next
`snapshot_sequence`; all chunks in the response retain that value.

`snapshot_sequence` is independent of scalar `sequence_id`. Its sender
lifecycle, wrap behavior, modulo ordering, pending-assembly handling, and
reset boundaries are defined above. A structured snapshot request and its
response are rate-limited according to the output's manifest
`delivery_class` and request policy. A source MAY defer, coalesce, or
silently ignore requests, especially for advisory or diagnostic outputs.

For scalar contexts, the context registry selects the sole representation but
does not assign a unit. Boolean values use bytes `b0,00,00,00`, where `b0`
MUST be `0` or `1`. GF values use `gf_low,gf_high,00,00`, where both
percentages are in `0..100` and `gf_low <= gf_high`. Floating contexts accept
only finite normal binary32 values or positive zero; NaN, infinity,
subnormals, and negative zero are invalid. Invalid payloads are discarded and
do not advance sequence state.

All listed scalar measurement contexts use finite positive-zero-normalized
binary32 except `CTX_GENERIC` (`i32`), galvanic-cell/NDL/TTS/stop-duration/OTU
(`u32`), Boolean, GF, and tissue contexts. Tissue context byte layout is:
bit 7 set; bits 6..4 kind (0 saturation, 1 N2, 2 He, 3 H2, 4 CF4); bits 3..0
index. Saturation uses four 8-bit values at aligned indexes 0,4,8,12 and
means `100*q/255` percent. Gas tensions use two little-endian `uint16_t`
whole-millibar values at even indexes 0..14. Kinds 5..7 and all other
unlisted contexts are invalid.

Only values explicitly listed in the scalar context registry are valid scalar
contexts. Every other context with bit 7 clear is reserved and MUST be
discarded without coercion or sequence advancement.

## Unit vocabulary

The payload has no unit field. The codes below catalogue source vocabulary;
they do not map a scalar context to a canonical unit. Unit words in the context
registry describe source intent only. Until the per-context unit mapping and
numeric range are assigned, a receiver MUST NOT convert a scalar value or infer
its unit from its numeric value.
| Value | Symbol | Meaning |
|---:|---|---|
| `0x00` | `UNIT_RAW` | Raw counts, packed bytes, or dimensionless |
| `0x01` | `UNIT_BOOL` | Binary state, 0 or 1 |
| `0x02` | `UNIT_PERCENT` | 0.0–100.0 percent |
| `0x03` | `UNIT_VOLTS` | Volts |
| `0x04` | `UNIT_MILLIVOLTS` | Millivolts |
| `0x05` | `UNIT_AMPERES` | Amperes |
| `0x06` | `UNIT_MILLIAMPS` | Milliamperes |
| `0x07` | `UNIT_BAR` | Bar |
| `0x08` | `UNIT_MILLIBARS` | Millibars |
| `0x09` | `UNIT_CELSIUS` | Degrees Celsius |
| `0x0A` | `UNIT_LUX` | Illuminance |
| `0x0B` | `UNIT_METERS` | Distance or depth |
| `0x0C` | `UNIT_METERS_PER_MIN` | Velocity |
| `0x0D` | `UNIT_SECONDS` | Time |
| `0x0E` | `UNIT_MINUTES` | Time |
| `0x0F` | `UNIT_GRAMS_PER_LITER` | Gas density |
| `0x10` | `UNIT_OTU` | Oxygen Toxicity Units |

## Contexts

| Range | Contexts |
|---|---|
| `0x00–0x0F` | Generic, battery power, bus current, ambient light, temperature |
| `0x10–0x2F` | Water engagement, light power, solenoid state, calibration mode |
| `0x30–0x3F` | O₂, N₂, He, H₂, CO₂, CF₄ partial pressures |
| `0x40–0x4F` | O₂, N₂, He, H₂, CO₂, CF₄ gas fractions |
| `0x50–0x5F` | Galvanic cell, loop pressure, tank pressure, gas density |
| `0x60–0x6F` | Ambient pressure, depth, ascent rate |
| `0x70–0x7F` | NDL, TTS, ceiling, deco stop duration, GF, CNS, OTU |
| `0x80–0x8F` | Packed tissue saturation; only `0x80`, `0x84`, `0x88`, `0x8C` valid |
| `0x90–0x9F` | Packed N₂ tension; even low nibble only |
| `0xA0–0xAF` | Packed He tension; even low nibble only |
| `0xB0–0xBF` | Packed H₂ tension; even low nibble only |
| `0xC0–0xCF` | Packed CF₄ tension; even low nibble only |
| `0xD0–0xFF` | Reserved |

### Context registry

| Value | Symbol | Meaning |
|---:|---|---|
| `0x00` | `CTX_GENERIC` | Generic |
| `0x01` | `CTX_BATTERY_POWER` | Battery power |
| `0x02` | `CTX_BUS_CURRENT` | Bus current |
| `0x03` | `CTX_AMBIENT_LIGHT` | Ambient light |
| `0x04` | `CTX_TEMPERATURE` | Temperature |
| `0x10` | `CTX_WATER_ENGAGEMENT` | Wet switch; 0 dry, 1 submerged |
| `0x11` | `CTX_LIGHT_POWER` | Lamp; 0 off, 1 on |
| `0x12` | `CTX_SOLENOID_STATE` | Valve; 0 closed, 1 open |
| `0x13` | `CTX_CALIBRATION_MODE` | System mode; 0 active, 1 calibrating |
| `0x30` | `CTX_PP_O2` | Oxygen partial pressure |
| `0x31` | `CTX_PP_N2` | Nitrogen partial pressure |
| `0x32` | `CTX_PP_HE` | Helium partial pressure |
| `0x33` | `CTX_PP_H2` | Hydrogen partial pressure |
| `0x34` | `CTX_PP_CO2` | Carbon dioxide partial pressure |
| `0x35` | `CTX_PP_CF4` | Tetrafluoromethane partial pressure |
| `0x40` | `CTX_F_O2` | Oxygen fraction |
| `0x41` | `CTX_F_N2` | Nitrogen fraction |
| `0x42` | `CTX_F_HE` | Helium fraction |
| `0x43` | `CTX_F_H2` | Hydrogen fraction |
| `0x44` | `CTX_F_CO2` | Carbon dioxide fraction |
| `0x45` | `CTX_F_CF4` | Tetrafluoromethane fraction |
| `0x50` | `CTX_GALVANIC_CELL` | Raw cell voltage; millivolts |
| `0x51` | `CTX_LOOP_PRESSURE` | Breathing-loop pressure |
| `0x52` | `CTX_TANK_PRESSURE` | Cylinder pressure |
| `0x53` | `CTX_GAS_DENSITY` | Loop gas density |
| `0x60` | `CTX_AMBIENT_PRESSURE` | Environmental pressure |
| `0x61` | `CTX_DEPTH` | Calculated water depth; meters |
| `0x62` | `CTX_ASCENT_RATE` | Vertical velocity; meters/minute |
| `0x70` | `CTX_NDL` | No-decompression limit; minutes |
| `0x71` | `CTX_TTS` | Time to surface; minutes |
| `0x72` | `CTX_CEIL` | Decompression ceiling depth; meters |
| `0x73` | `CTX_CEIL_DECO` | Current stop duration; seconds |
| `0x74` | `CTX_GF` | Gradient factors; raw packed `gf_low`, `gf_high` |
| `0x75` | `CTX_CNS` | Central nervous system toxicity; percent |
| `0x76` | `CTX_OTU` | Cumulative oxygen toxicity; OTU |

`CTX_GF` is raw packed data: bytes 4–5 are `gf_low` and `gf_high`; bytes 6–7
are zero. Its corresponding source-vocabulary code is `UNIT_RAW`. Unknown or
reserved contexts and invalid context/value combinations are discarded;
receivers do not coerce, clamp, or advance sequence state.

## Tissue payloads

Byte 3 is the complete tissue discriminator: bit 7 is set, bits 6..4 select
kind (`0` saturation; `1` N₂; `2` He; `3` H₂; `4` CF₄), and bits 3..0 select
the first compartment. The vector has 16 compartments. Saturation uses four
bytes at indexes `0`, `4`, `8`, or `12`, scaled exactly as `100*q/255`.
Gas kinds use two little-endian whole-millibar `uint16_t` values at even
indexes `0..14`. No other tissue context is valid; context selects pair versus
quad and no optional mode exists.

The legacy tissue contexts do not represent every structured tissue result.
They are limited to 16 compartments and do not provide a gas selector for
multiple saturation matrices. A decompression result such as four gas
saturation values across 16 or 32 tissues MUST use a manifest-declared
`STRUCTURED_SNAPSHOT`; it MUST NOT be coerced into an unrelated scalar or
legacy tissue context.

## Telemetry control

Telemetry-control messages request a current value or a temporary higher
cadence for one exact telemetry selector. They never request retransmission:
a missing measurement remains missing, and a snapshot reports the source's
current cached value rather than an earlier frame.

### Frames and payload

A request uses `CAN_ID = (0x03 << 7) | requester_node_id`
(`0x181–0x1FF`); its low bits name the requester. Its 8-byte payload is:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 1 | `uint8_t` | Request opcode |
| 1 | 1 | `uint8_t` | Target source node ID |
| 2 | 1 | `uint8_t` | `publisher_id` |
| 3 | 1 | `uint8_t` | `context` |
| 4 | 2 | `uint16_t` | Requested period in milliseconds |
| 6 | 2 | `uint16_t` | Requested duration in seconds |

All `uint16_t` fields are little-endian. The request target discards a frame
unless the requester node ID is in `0x01–0x7F` and byte 1 equals its own
active node ID. The selector is `(source_node_id, publisher_id, context)`;
no UUID appears in the payload.

| Request opcode | Symbol | Fields 4–7 |
|---:|---|---|
| `0x01` | `TCTRL_SNAPSHOT_REQUEST` | all zero |
| `0x02` | `TCTRL_RATE_LEASE_REQUEST` | period and duration |

Unknown opcodes, nonzero snapshot fields, invalid node IDs, invalid contexts,
and invalid period/duration pairs are discarded without response. A source
MAY silently ignore any otherwise valid request, including one that fails its
local access policy, selects an unavailable stream, or exceeds its resource
limits. Request confirmation and rejection messages are intentionally absent;
a requester observes only any resulting telemetry.

### Snapshot request

For `TCTRL_SNAPSHOT_REQUEST`, a source MAY enqueue the latest current value
for the exact selector. A scalar output produces one scalar telemetry frame; a
`STRUCTURED_SNAPSHOT` output produces one fresh structured snapshot made of
the required chunks. The source MUST NOT replay an older missing frame or
snapshot and MUST NOT invent a sample.

A source without a current cached value, available snapshot-frame budget, or
willingness to serve the request emits no response. A request for a
structured snapshot is not a retransmission request: the source creates a new
snapshot sequence when it honors the request.

A source MUST process requests according to the selected output's manifest
`delivery_class` and `minimum_request_interval_ms`, subject to stricter
source-wide bus and resource limits. It MAY defer, coalesce, rate-limit, or
silently ignore requests. A requester observes only resulting telemetry and
must treat an incomplete structured snapshot as unavailable.

### Temporary rate lease

`TCTRL_RATE_LEASE_REQUEST` has one of these valid field pairs:

| Requested period | Requested duration | Meaning |
|---:|---:|---|
| `200–60,000` ms | `1–60` s | Request a temporary cadence no slower than the period |
| `0` | `0` | Cancel this requester's lease for the selector |

A nonzero period is a requested maximum telemetry interval, so `200` ms
requests 5 Hz. A source MAY honor a lease only if it can emit the selected
stream no slower than the requested interval for the full requested duration.
It sends no acceptance or rejection message. A processed cancellation removes
this requester's lease if one exists. A source that cannot honor a request
silently ignores it.

The source stores each lease by requester node ID, the requester identity
generation currently associated with that ID, publisher ID, and context. If no
UUID is currently bound to the requester ID, the source uses the explicit
unbound generation sentinel. A new valid lease request from that requester for
the same selector replaces its prior lease; expiry removes it. When discovery
binds or changes the UUID for a requester node ID, the source MUST revoke that
requester's leases from the prior generation, including the unbound
generation, before accepting new state for the replacement.
While one or more leases select a stream, the source emits one stream at the
fastest active effective cadence, never one copy per requester. When the final
lease expires or is cancelled, its normal cadence resumes.

To bound rate-control load, a source MUST NOT honor a lease that would
increase its aggregate telemetry schedule by more than five frames per second
above its normal schedule. It MUST also process at most one rate-lease request
per requester and selector per second; further requests in that interval are
discarded without response. These limits apply independently of any faster
normal cadence and do not guarantee delivery through CAN arbitration or bus
faults.

## Subscription lifecycle

Rebus v0.1 assigns no telemetry-subscribe or telemetry-unsubscribe CAN
identifier, payload, acknowledgement, or flow-control mechanism. A telemetry
subscription is receiver-local: it never changes a publisher's role
announcement, telemetry cadence, frame contents, or bus traffic.

An active subscription selects exactly one current stream context:
`(source_node_id, publisher_id, context)` and is bound locally to the current
`identity_generation` for that source node ID. `source_node_id` MUST be in
`0x01–0x7F`, and `context` MUST be valid under this document. A consumer that
needs several streams or contexts registers one subscription per exact
selector.

### Subscribe process

1. Validate the source node-ID range and selected context.
2. Resolve the source node ID to its current identity generation and store the
   exact selector with that generation. This creates no CAN frame and does not
   alter shared capability or sequence state.
3. Apply the profile frame gate, telemetry payload validation, and per-stream
   sequence processing before evaluating any subscription. For each accepted
   frame, deliver its value and status only to active selectors that exactly
   match its stream, context, and current identity generation.

The receiver processes sequence state once per accepted stream, not once per
subscriber. A subscription begins with future accepted frames only; it neither
replays an earlier value nor makes a missing source publish.

### Unsubscribe process

1. Remove the exact local selector.
2. Stop deliveries for that selector immediately, without changing shared
   capability or sequence state.
3. Send no CAN frame and make no request to the source.

An active subscription remains in effect until it is removed or discovery
changes the UUID bound to its source node ID. A UUID remap removes the
subscription and its associated requester-bound state; the replacement node
must be subscribed explicitly. Address reuse therefore cannot inherit or
recreate the prior selector.
