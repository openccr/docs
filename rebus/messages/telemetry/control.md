SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Telemetry control

Telemetry-control messages request a current value or a temporary higher
cadence for one exact telemetry selector. They never request retransmission: a
missing measurement remains missing, and a snapshot reports the source's
current cached value rather than an earlier frame.

## Frames and payload

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
active node ID. The selector is `(source_node_id, publisher_id, context)`; no
UUID appears in the payload.

| Request opcode | Symbol | Fields 4–7 |
|---:|---|---|
| `0x01` | `TCTRL_SNAPSHOT_REQUEST` | all zero |
| `0x02` | `TCTRL_RATE_LEASE_REQUEST` | period and duration |

Unknown opcodes, nonzero snapshot fields, invalid node IDs, invalid contexts,
and invalid period/duration pairs are discarded without response. A source MAY
silently ignore any otherwise valid request, including one that fails its local
access policy, selects an unavailable stream, or exceeds its resource limits.
Request confirmation and rejection messages are intentionally absent; a
requester observes only any resulting telemetry.

## Snapshot request

For `TCTRL_SNAPSHOT_REQUEST`, a source MAY enqueue the latest current value
for the exact selector. A scalar output produces one scalar telemetry frame; a
`STRUCTURED_SNAPSHOT` output produces one fresh structured snapshot made of the
required chunks. The source MUST NOT replay an older missing frame or snapshot
and MUST NOT invent a sample.

A source without a current cached value, available snapshot-frame budget, or
willingness to serve the request emits no response. A request for a structured
snapshot is not a retransmission request: the source creates a new snapshot
sequence when it honors the request.

A source MUST process requests according to the selected output's manifest
`delivery_class` and `minimum_request_interval_ms`, subject to stricter
source-wide bus and resource limits. It MAY defer, coalesce, rate-limit, or
silently ignore requests. A requester observes only resulting telemetry and
must treat an incomplete structured snapshot as unavailable.

## Temporary rate lease

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
requester's leases from the prior generation, including the unbound generation,
before accepting new state for the replacement.

While one or more leases select a stream, the source emits one stream at the
fastest active effective cadence, never one copy per requester. When the final
lease expires or is cancelled, its normal cadence resumes.

To bound rate-control load, a source MUST NOT honor a lease that would increase
its aggregate telemetry schedule by more than five frames per second above its
normal schedule. It MUST also process at most one rate-lease request per
requester and selector per second; further requests in that interval are
discarded without response. These limits apply independently of any faster
normal cadence and do not guarantee delivery through CAN arbitration or bus
faults.
