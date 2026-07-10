SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# BLE Packet Formats

Byte-precise payload specifications for all advertising data and GATT characteristic payloads.

All multi-byte integers are little-endian unless noted otherwise.

---

## Advertising: Manufacturer Specific Data Payload

This is the 5-byte payload within the Manufacturer Specific Data AD structure
in the **scan response PDU** (bytes 22–26 — see `../discovery/README.md` for the
full scan response layout including AD headers and Company ID). The scan response
PDU is fixed-length (27 bytes) regardless of device name length.

| Offset | Length | Type | Range | Notes |
|---|---|---|---|---|
| 0 | 1 | uint8 | `0x01` | Protocol version; fixed at `0x01` for this revision |
| 1 | 1 | uint8 | 0–255 | Firmware major version |
| 2 | 1 | uint8 | 0–255 | Firmware minor version |
| 3 | 1 | uint8 | 0–255 | Firmware patch version |
| 4 | 1 | uint8 | bit-field | Flags (see below) |

**Flags byte (offset 4):**

| Bit | Name | Meaning |
|---|---|---|
| 0 | `has_companion` | `1` = device has an active BLE bond stored in NVS |
| 1–7 | (reserved) | Must be `0`; ignore on read |

---

## Characteristic: DeviceInfo — 12 bytes

UUID: `4f434352-0001-0001-1845-000000000000`
Properties: Read
Security: L1 (no encryption required)

| Offset | Length | Type | Range | Notes |
|---|---|---|---|---|
| 0 | 1 | uint8 | `0x01` | Protocol version; fixed at `0x01` for this revision |
| 1 | 1 | uint8 | 0–255 | Firmware major version |
| 2 | 1 | uint8 | 0–255 | Firmware minor version |
| 3 | 1 | uint8 | 0–255 | Firmware patch version |
| 4 | 6 | ASCII | printable alphanumeric | Serial suffix (6 characters, no null terminator) |
| 10 | 1 | uint8 | 0–255 | Model ID (TBD; use `0x00` until model IDs are assigned) |
| 11 | 1 | uint8 | bit-field | Flags (same encoding as advertising flags byte) |

**Flags byte (offset 11):**

| Bit | Name | Meaning |
|---|---|---|
| 0 | `has_companion` | `1` = device has an active BLE bond stored in NVS |
| 1–7 | (reserved) | Must be `0`; ignore on read |

---

## Characteristic: PairingKey — 6 bytes

UUID: `4f434352-0001-0002-1845-000000000000`
Properties: Write (with response preferred)
Security: L1 (no encryption required)

| Offset | Length | Type | Range | Notes |
|---|---|---|---|---|
| 0 | 6 | ASCII | `[A-Z0-9a-z]` | Pairing key; no null terminator; no padding |

- Exactly 6 bytes. Writes of any other length must be rejected with ATT error `Invalid Attribute Length` (`0x0D`).
- Case-sensitive. `"a1b2c3"` and `"A1B2C3"` are different keys.
- The key is validated against a 6-character pairing secret provisioned in NVS at manufacturing.
  The pairing secret is independent of the serial number and the device name identifier;
  it is not derivable from any information broadcast in the advertising packets.

---

## Characteristic: PairingResult — 3 bytes

UUID: `4f434352-0001-0003-1845-000000000000`
Properties: Read + Notify
Security: L1 (no encryption required)

| Offset | Length | Type | Range | Notes |
|---|---|---|---|---|
| 0 | 1 | uint8 | see table | Result code |
| 1 | 1 | uint8 | 0–3 | Remaining attempts (meaningful for `FAIL_WRONG_KEY` only; `0` otherwise) |
| 2 | 1 | uint8 | reserved | Must be `0x00` |

**Result codes (byte 0):**

| Code | Value | Remaining attempts field | Meaning |
|---|---|---|---|
| `PENDING` | `0x00` | `0` | Key received; SMP bonding in progress |
| `SUCCESS` | `0x01` | `0` | Bonding complete |
| `FAIL_WRONG_KEY` | `0x02` | 2 or 1 | Key did not match; field shows attempts remaining |
| `FAIL_LOCKED_OUT` | `0x03` | `0` | Third failure; 30-second lockout active |
| `FAIL_BONDING` | `0x04` | `0` | SMP bonding step failed; retry permitted |
| `FAIL_ALREADY_PAIRED` | `0x05` | `0` | Device already bonded; no action taken |

---

## Companion App Recognition Logic

The app uses two signals to classify a discovered device:

1. **`has_companion` flag** in advertising data (manufacturer specific data byte 4, bit 0)
   or equivalently in `DeviceInfo` byte 11, bit 0.
2. **Bond resolution** — whether the OS can successfully encrypt the connection using
   a stored bond for this device's address.

| `has_companion` | Bond resolves | Classification |
|---|---|---|
| `0` | N/A | Never paired — show pairing flow |
| `1` | Yes | Paired with this app — connect and proceed |
| `1` | No | Paired with a different app — show "device owned by another app" message |

**Bond resolution**: call `device.connect()`. If `flutter_blue_plus` raises a bond
or authentication error, the bond belongs to a different companion app instance.

The app must not attempt to overwrite or delete a foreign bond without explicit
user confirmation.
