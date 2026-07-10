SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# BLE GATT Services

GATT service and characteristic definitions for the Device Service.

## UUID Namespace

Base: `4f434352-SSSS-CCCC-1845-000000000000`

<!-- 1845 = Tx18/45 pun -->

The first four bytes (`4f 43 43 52`) encode "OCCR" in ASCII.

| Field | Width | Purpose |
|---|---|---|
| SSSS | 16-bit | Service selector |
| CCCC | 16-bit | Characteristic selector (`0000` = service itself) |

**Company ID in manufacturer data**: `0xFFFF` (development placeholder; unregistered).
Production builds require a Bluetooth SIG-registered Company ID.
Filter devices by Service UUID — not Company ID — as the primary identifier.

## Device Service

**Service UUID**: `4f434352-0001-0000-1845-000000000000`

All three characteristics below are exposed before bonding (L1 security) to support
the two-phase pairing handshake. After bonding, subsequent data services require
L2 encryption and are defined in future service specifications.

| Characteristic | UUID | Properties | Auth | Description |
|---|---|---|---|---|
| DeviceInfo | `4f434352-0001-0001-1845-000000000000` | Read | None (L1) | Firmware version, serial suffix, model, flags |
| PairingKey | `4f434352-0001-0002-1845-000000000000` | Write | None (L1) | App writes 6-byte pairing key here |
| PairingResult | `4f434352-0001-0003-1845-000000000000` | Read + Notify | None (L1) | Result of most recent pairing attempt |

See `../packets/README.md` for byte-precise payload formats.

### DeviceInfo

Read-only. App reads this immediately after connecting to verify device identity
and obtain the firmware version before writing `PairingKey`.

### PairingKey

Write-only (Write Without Response is acceptable; Write With Response is preferred
to detect disconnect mid-write). The app writes exactly 6 bytes of ASCII alphanumeric
characters (no null terminator, no padding). Case-sensitive.

The firmware validates the key against a pairing secret provisioned in NVS at
manufacturing. The pairing secret is independent of the serial number and the device
name; it is not derivable from any information visible in the BLE advertising packets
(e.g., the device name suffix or any characteristic readable before pairing).

Incorrect keys increment a per-connection failure counter. Three consecutive failures
trigger a 30-second lockout (see `../discovery/README.md`).

### PairingResult

Read + Notify. Firmware updates this characteristic and notifies the app after
evaluating a `PairingKey` write. The app should subscribe to notifications before
writing `PairingKey`.

Result codes:

| Code | Value | Meaning |
|---|---|---|
| PENDING | `0x00` | Key received; SMP bonding in progress |
| SUCCESS | `0x01` | Bonding complete |
| FAIL_WRONG_KEY | `0x02` | Key did not match; attempts remaining |
| FAIL_LOCKED_OUT | `0x03` | Third failure; 30-second lockout started |
| FAIL_BONDING | `0x04` | SMP bonding step failed; retry permitted |
| FAIL_ALREADY_PAIRED | `0x05` | Device already bonded; no action taken |

## Future Services

Data services (PO₂, alarms, configuration, logs) are out of scope for this revision.
They will use the same UUID namespace with a different SSSS selector and will require
L2 encryption.
