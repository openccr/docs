SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# BLE Protocol Overview

This directory defines the BLE protocols used between openCCR firmware and the companion app.

## Scope

| Topic | File | Purpose |
|---|---|---|
| Discovery & Pairing | `discovery.md` | Advertising, scanning, and the two-phase pairing handshake |
| GATT Services | `services.md` | Characteristic definitions for all services |
| Packet Formats | `packets.md` | Byte-precise wire-format payloads |
| Capability Model | `capabilities.md` | Hardware capability data model and feature enablement matrix |

Two services are defined in this revision: the Device Service (pairing) and the Capability Service (hardware module inventory). Dive-data services (ppO₂ streaming, alarms, logs) are out of scope and will be specified separately.

## Firmware Stack

- RTOS: Zephyr
- BT API: Zephyr Bluetooth API (Nordic nRF MCU)

## Companion App Stack

- Framework: Flutter
- BLE library: `flutter_blue_plus` ^1.33.0

## Two-Phase Pairing Summary

openCCR uses a two-phase pairing sequence that gives the companion app full control of the pairing UX, avoiding the OS system dialog that standard BLE SMP fixed-passkey would require.

**Phase 1 — GATT key exchange** (unencrypted connection, L1 security):

1. Firmware advertises using its configured device name (see below).
2. App connects and reads `DeviceInfo` to confirm device identity.
3. App writes a 6-byte ASCII alphanumeric pairing key to the `PairingKey` characteristic.
4. Firmware validates the key against a pairing secret provisioned in NVS at manufacturing.
   The pairing secret is independent of the serial number and the device name.
   Three wrong attempts trigger a 30-second lockout.
5. On success, firmware sets `PairingResult` = `SUCCESS` and proceeds to Phase 2.

**Phase 2 — BLE SMP bonding** (standard Zephyr `BT_SECURITY_L2`):

1. Firmware calls `bt_conn_set_security(conn, BT_SECURITY_L2)`.
2. Just Works pairing is used (no MITM required — MITM protection was provided by Phase 1).
3. OS stores the bond; future reconnections are transparently re-encrypted.
4. `flutter_blue_plus` handles transparent reconnection.

After bonding, subsequent data services (defined in future specs) require L2 encryption.

## Device Name

The advertised local name is one of:

1. **Saved name** — a user-configured name stored in NVS (set via a future characteristic; TBD).
2. **Default name** — `openCCR-XXXXXX` where XXXXXX is the last 3 bytes of the BLE MAC
   address in uppercase hex (e.g., MAC `AA:BB:CC:DD:EE:FF` → name `openCCR-DDEEFF`).

The device name is **not** derived from the serial number and does **not** reveal the pairing
key. The pairing key is a separate secret provisioned at manufacturing and is only obtainable
from the physical device (e.g., printed on a label).

**Storage vs advertising**: firmware stores names up to 32 characters in NVS. The BLE
primary advertising PDU can carry at most 26 characters; if the stored name is longer,
firmware advertises the first 26 characters. The full name is readable via the Generic
Access Profile `Device Name` characteristic after connecting.

## Files

```
ble/
├── README.md        ← this file
├── discovery.md     ← advertising layout, pairing state machine, scan behavior
├── services.md      ← GATT service and characteristic table
├── packets.md       ← byte-precise payload specifications
└── capabilities.md  ← hardware capability model and feature enablement matrix
```
