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

See `packets.md` for byte-precise payload formats.

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
trigger a 30-second lockout (see `discovery.md`).

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

## Capability Service

**Service UUID**: `4f434352-0002-0000-1845-000000000000`

Exposes a single read-only characteristic that describes all hardware modules
attached to the MCU. The companion app reads this characteristic once after bonding
and uses the result to enable or disable UI features.

Capabilities are static for the lifetime of the connection (detected at MCU boot,
never change during a dive). No `Notify` property is provided.

| Characteristic | UUID | Properties | Auth | Length | Description |
|---|---|---|---|---|---|
| CapabilityDescriptor | `4f434352-0002-0001-1845-000000000000` | Read | L2 (bonded) | 8 + N×variable | Full hardware capability blob |

See `packets.md` for byte-precise payload format and `capabilities.md`
for the capability data model, feature enablement matrix, and exchange process.

### CapabilityDescriptor

Read-only. Available to bonded connections only (L2). If the payload exceeds
`ATT_MTU − 1` bytes, the ATT Long Read procedure (`Read Blob Request`) must be used.
Firmware SHOULD negotiate MTU ≥ 128 bytes. Companion app SHOULD request MTU ≥ 128
at connection time (`CONFIG_BT_L2CAP_TX_MTU` on Zephyr).

Typical payload size for a standard CCR build (3 O₂ cells, 1 solenoid, 1 depth sensor,
1 barometric sensor, 1 CO₂ temp stick, 1 general screen): approximately 56 bytes,
well within a single ATT packet at default MTU.

## Future Services

Data services (ppO₂ streaming, alarms, configuration, dive logs) are out of scope
for this revision. They will use the same UUID namespace with a different SSSS selector
and will require L2 encryption.
