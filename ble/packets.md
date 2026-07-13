SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# BLE Packet Formats

Byte-precise payload specifications for all advertising data and GATT characteristic payloads.

All multi-byte integers are little-endian unless noted otherwise.

---

## Advertising: Manufacturer Specific Data Payload

This is the 5-byte payload within the Manufacturer Specific Data AD structure
in the **scan response PDU** (bytes 22–26 — see `discovery.md` for the
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

---

## Characteristic: CapabilityDescriptor — variable length

UUID: `4f434352-0002-0001-1845-000000000000`
Properties: Read
Security: L2 (bonded connections only)

All multi-byte integers are little-endian.

### Fixed Header — 8 bytes

| Offset | Length | Type | Value | Notes |
|---|---|---|---|---|
| 0 | 1 | uint8 | `0x01` | Protocol version; `0x01` for this revision |
| 1 | 1 | uint8 | bit-field | MCU capability flags (see below) |
| 2 | 2 | uint16 | `0x0000` | Reserved; must be `0x0000` |
| 4 | 1 | uint8 | 0–255 | Module descriptor count (N) |
| 5 | 1 | uint8 | `0x00` | Reserved; must be `0x00` |
| 6 | 2 | uint16 | 0–65535 | Byte length of TLV body that follows |

**MCU capability flags (header byte 1):**

Firmware sets these bits at boot based on detected hardware. A flag must only be set
when all listed prerequisites are satisfied.

| Bit | Name | Meaning |
|---|---|---|
| 0 | `UNDERSTAND_PPO2` | MCU can produce normalized ppO₂ from available O₂ cells |
| 1 | `CALCULATE_DECO` | MCU runs deco algorithm (requires `UNDERSTAND_PPO2` + `DEPTH_SENSOR`) |
| 2 | `SETPOINT_MAINTENANCE` | MCU can fire solenoids to maintain target ppO₂ (requires `UNDERSTAND_PPO2` + `O2_SOLENOID_DRIVER`) |
| 3 | `DISPLAY_PPO2` | MCU drives a ppO₂-capable display (requires `UNDERSTAND_PPO2` + ppO₂-capable display module) |
| 4 | `DISPLAY_DECO` | MCU drives a deco-capable display (requires `CALCULATE_DECO` + deco-capable display module) |
| 5 | `AUTO_CALIBRATION` | MCU can trigger O₂ solenoid for calibration sequence (requires `UNDERSTAND_PPO2` + `O2_SOLENOID_DRIVER` + `BAROMETRIC_SENSOR`) |
| 6–7 | (reserved) | Must be `0`; ignore on read |

### TLV Module Descriptor — per-module envelope

Immediately follows the fixed header. Repeated N times (N = module descriptor count
from header byte 4).

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | Module type ID (see registry in `capabilities.md`) |
| 1 | 1 | uint8 | Instance ID (0-based, scoped per type) |
| 2 | 1 | uint8 | Data length L (bytes in data field that follow) |
| 3 | L | bytes | Module-specific data (see per-type specs below) |

**Forward compatibility**: If `type_id` is unknown, the app MUST skip `L` bytes and
continue parsing. It must not abort.

---

### O2_CELL_READER (type `0x01`) — data: 4 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `cell_type` (see below) |
| 1 | 1 | uint8 | `capability_flags` (see below) |
| 2 | 2 | uint8[2] | Reserved; must be `0x00 0x00` |

**`cell_type` values:**

| Value | Name | Notes |
|---|---|---|
| `0x00` | `ANALOG` | Analog galvanic cell |
| `0x01` | `DIGITAL_DIVO2` | DivO₂ digital cell |
| `0x02` | `DIGITAL_PYROSCIENCE` | Pyroscience digital cell |
| `0x03` | `DIGITAL_POSEIDON` | Poseidon digital cell |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `provides_raw_ppo2` — always `1` |
| 1–7 | Reserved; must be `0` |

Calibration support is derived by the app from `cell_type`:
- `ANALOG` → manual calibration available; auto-calibration available if
  `O2_SOLENOID_DRIVER` is also present and MCU:`AUTO_CALIBRATION` is set.
- Digital types → calibration not available via companion app (handled in firmware
  or sensor firmware).

---

### CO2_CELL_READER (type `0x02`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags`: bit 0 = `provides_ppco2` (always `1`); bits 1–7 reserved |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

---

### CO_READER (type `0x03`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags`: bit 0 = `provides_co_ppm` (always `1`); bits 1–7 reserved |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

---

### HE_READER (type `0x04`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `he_type`: `0x00` = `ANALOG`, `0x01` = `DIGITAL` |
| 1 | 1 | uint8 | `capability_flags`: bit 0 = `provides_pphe` (always `1`); bits 1–7 reserved |

---

### O2_SOLENOID_DRIVER (type `0x05`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `solenoid_count` — number of physical solenoids this driver controls (1–255) |
| 1 | 1 | uint8 | `capability_flags` (see below) |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `supports_calibration_trigger` |
| 1 | `supports_setpoint_control` |
| 2–7 | Reserved; must be `0` |

---

### DILUENT_SOLENOID_DRIVER (type `0x06`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `solenoid_count` — number of physical solenoids this driver controls (1–255) |
| 1 | 1 | uint8 | `capability_flags`: bits 0–7 reserved (future: bailout, flush, etc.); must be `0x00` |

---

### BAROMETRIC_SENSOR (type `0x07`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags`: bit 0 = `provides_baro_pressure` (always `1`); bits 1–7 reserved |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

---

### DEPTH_SENSOR (type `0x08`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags` (see below) |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `provides_depth` — always `1` |
| 1 | `provides_water_temp` — `1` if sensor also reads water temperature |
| 2–7 | Reserved; must be `0` |

---

### CO2_TEMP_STICK (type `0x09`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `sensor_count` — number of temperature sensors on the stick (≥1) |
| 1 | 1 | uint8 | `capability_flags`: bit 0 = `provides_temp_series` (always `1`); bits 1–7 reserved |

---

### STATUS_LIGHT (type `0x0A`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags` (see below) |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `supports_ppo2_leds` — `1` if this light indicates ppO₂ status (OK/warn/error) |
| 1 | `supports_rgb_color` — `1` if full-color RGB capable |
| 2 | `supports_deco_leds` — `1` if this light has dedicated deco-status LEDs |
| 3–7 | Reserved; must be `0` |

A `STATUS_LIGHT` with `capability_flags = 0x00` is an alarm-only indicator (driven
by MCU alarm logic, not by ppO₂ or deco data directly).

---

### PPO2_DISPLAY (type `0x0B`) — data: 2 bytes

Requires at least one `O2_CELL_READER` also present in the system.

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags` (see below) |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `shows_per_cell_ppo2` — `1` if can show individual cell values |
| 1 | `shows_normalized_ppo2` — `1` if can show MCU-voted result |
| 2–7 | Reserved; must be `0` |

---

### DECO_DISPLAY (type `0x0C`) — data: 2 bytes

Requires `DEPTH_SENSOR` and ≥1 `O2_CELL_READER` also present.

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags` (see below) |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `shows_deco_stops` — `1` if can show required deco stops |
| 1 | `shows_ndl` — `1` if can show no-decompression limit |
| 2–7 | Reserved; must be `0` |

---

### GENERAL_SCREEN (type `0x0D`) — data: 4 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `screen_type` (see below) |
| 1 | 1 | uint8 | `sub_capability_flags` (see below) |
| 2 | 2 | uint8[2] | Reserved; must be `0x00 0x00` |

**`screen_type` values:**

| Value | Name |
|---|---|
| `0x00` | `MONOCHROME` |
| `0x01` | `COLOR` |
| `0x02` | `E_INK` |
| `0x03–0xFF` | Reserved; must not be used |

**`sub_capability_flags` bits (which display roles this screen fulfills):**

| Bit | Meaning |
|---|---|
| 0 | `acts_as_ppo2_display` |
| 1 | `acts_as_status_light` |
| 2 | `acts_as_deco_display` |
| 3–7 | Reserved; must be `0` |

---

### FLASH_MEMORY (type `0x0E`) — data: 4 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `storage_type` (see below) |
| 1 | 1 | uint8 | `capability_flags`: bit 0 = `provides_dive_log` (always `1`); bits 1–7 reserved |
| 2 | 2 | uint16 | `capacity_kib` — storage capacity in kibibytes, LE; `0x0000` = unknown or not reported |

**`storage_type` values:**

| Value | Name |
|---|---|
| `0x00` | `INTERNAL_FLASH` |
| `0x01` | `EXTERNAL_NOR_FLASH` |
| `0x02` | `SD_CARD` |
| `0x03–0xFF` | Reserved; must not be used |

---

### BUTTONS (type `0x0F`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `input_type` (see below) |
| 1 | 1 | uint8 | `capability_flags` (see below) |

**`input_type` values:**

| Value | Name | Notes |
|---|---|---|
| `0x00` | `MOMENTARY_BUTTON` | Standard push button |
| `0x01` | `ENCODER` | Rotary encoder (physical implementation is irrelevant to firmware) |
| `0x02–0xFF` | Reserved | Must not be used |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `supports_click` — single click event |
| 1 | `supports_double_click` — double click event |
| 2 | `supports_long_click` — long press event |
| 3 | `supports_value` — device reports exact position/value, not just events (typical for encoders) |
| 4–7 | Reserved; must be `0` |

Multiple physical buttons or encoders are each reported as a separate TLV entry
with their own `instance_id`.

---

### WATER_CONTACT_SENSOR (type `0x10`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags`: bit 0 = `provides_water_contact` (always `1`); bits 1–7 reserved |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

---

### BUZZER (type `0x11`) — data: 2 bytes

| Offset | Length | Type | Notes |
|---|---|---|---|
| 0 | 1 | uint8 | `capability_flags` (see below) |
| 1 | 1 | uint8 | Reserved; must be `0x00` |

**`capability_flags` bits:**

| Bit | Meaning |
|---|---|
| 0 | `supports_variable_tone` — `1` if buzzer can produce distinct tones or patterns per alarm type; `0` = single tone only |
| 1–7 | Reserved; must be `0` |

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
