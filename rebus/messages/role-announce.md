SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Role announce message

## Payload

`rebus_msg_role_announce_t` is an 8-byte declared payload:

| Offset | Length | Type | Meaning |
|---:|---:|---|---|
| 0 | 2 | `openccr_role_mask_t` | Supported role bits |
| 2 | 4 | `uint32_t` | `firmware_hash`; manifest SHA-256 fingerprint |
| 6 | 2 | `uint16_t` | `config_count`; manifest configuration catalogue entries |

Role announcements use `CAN_ID = (0x06 << 7) | source_node_id`
(`0x301–0x37F`). The low seven bits must resolve to the sender's current
confirmed session mapping before the payload is used.

## Role bitmask

| Bit | Symbol | Meaning |
|---:|---|---|
| 0 | `ROLE_TELEMETRY_NODE` | May publish raw or computed telemetry |
| 1 | `ROLE_CONFIGURATION_SERVER` | Configuration-service capability; its request protocol is unassigned |
| 2 | `ROLE_FIRMWARE_DISPATCHER` | Firmware-dispatch capability; its request protocol is unassigned |
| 3 | `ROLE_LOOP_CONTROLLER` | Issues real-time commands or solenoid actions relying on consensus |
| 4 | `ROLE_INTERFACE_NODE` | Handset/HUD display and user input controls |
| 5 | `ROLE_TELEMETRY_GATEWAY` | Bridges CAN to external radios such as BLE or Wi-Fi |
| 6 | `ROLE_SAFETY_WATCHDOG` | Monitors heartbeats and triggers hardware fail-safes |
| 7–15 | reserved | No meaning assigned by the headers |

`ROLE_NONE` is `0x0000`, the valid empty capability set. A confirmed node MAY
announce it; receivers record no roles and MUST NOT infer a capability from its
other metadata fields. Bits 7–15 are reserved and MUST be zero. A role
announcement with any reserved bit set is invalid and is discarded without
changing capability or telemetry-sequence state. A receiver that does not
implement a defined role records the announcement but MUST NOT act on that
role.

## Metadata

`firmware_hash` is a 32-bit little-endian fingerprint, not an integrity or
authorization credential. Its algorithm and configuration-schema catalogue
locator must be supplied through trusted out-of-band management; a matching
fingerprint is only a lookup hint. `config_count` is the unsigned count in that
catalogue and does not grant a configuration role.


The fingerprint is the little-endian integer formed from the first four bytes
of `SHA-256` over the UTF-8 manifest
`rebus-firmware-manifest-v1\nimplementation-id=<id>\nrelease-sha256=<digest>\nbuild-profile-sha256=<digest>\nconfig-catalogue-sha256=<digest>\n`.
Each digest is lowercase SHA-256 hexadecimal; the catalogue is an ordered
UTF-8 list of schema identifier, revision, and schema SHA-256 digest.
`config_count` is its entry count. The 32-bit fingerprint is only a lookup
hint: compatibility, update, and schema decisions require the full manifest
from trusted out-of-band management.

## Capability announcement process

A role announcement is Rebus v0.1's sole capability announcement. It is a
broadcast declaration, not a request: it has no acknowledgement, does not
confirm or renew discovery ownership, and does not act as a heartbeat.

After bootstrap or reclaim produces local `CONFIRMED` state, and after any
logical-publisher restart, a node begins a node-wide telemetry epoch:

1. Build one role-announcement payload from the roles currently available on
   the node and its manifest metadata. A node that may publish telemetry MUST
   set `ROLE_TELEMETRY_NODE`; a node with no capabilities sends `ROLE_NONE`.
2. Make four logical role-announcement emissions at epoch times 0, 250, 500,
   and 750 ms. The four payloads MUST be byte-identical.
3. Suppress every local telemetry publisher until 1,000 ms after the first
   role-announcement emission. All local telemetry publishers participate in
   the node-wide epoch and initialize their next sequence value to zero.

The 1,000-ms hold ensures that the four announcement emissions precede
telemetry. A logical-publisher restart therefore restarts every local telemetry
publisher's sequence epoch; it cannot reset only one publisher because a role
announcement identifies a node, not a publisher.

After the profile frame gate and current-session `CONFIRMED` source-mapping
check, a receiver validates the role mask, stores the payload as the capability
record keyed by `(session, node_id, hardware_uuid)`, and clears sequence state
for every publisher from that source. Each accepted repetition is idempotent:
it replaces the same capability record and keeps that source's sequence state
cleared. A role announcement never authorizes traffic from an unconfirmed
source.
