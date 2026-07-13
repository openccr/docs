SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# BLE Capability Model

Defines the hardware capability data model shared between MCU firmware and the
companion app. After bonding, the companion app reads a single GATT characteristic
(`CapabilityDescriptor`) and uses the result to enable or disable UI features
corresponding to physically present hardware modules.

Capabilities are **static at boot**: the MCU enumerates the CCRAN bus on startup,
detects all attached modules, and builds an in-memory capability record that does
not change during the dive. The companion app reads capabilities once and caches
the result for the session.

---

## MCU Capability Flags

Announced in the fixed header of `CapabilityDescriptor` (byte 1). Bit-field, uint8.

MCU capability flags express what the MCU can functionally **do**, computed at boot
from the combination of modules detected on the CCRAN bus. Dependencies are listed
in the Meaning column; the firmware must only set a flag when all prerequisites are met.

| Bit | Name | Meaning |
|---|---|---|
| 0 | `UNDERSTAND_PPO2` | MCU can produce a normalized ppO₂ reading from available O₂ cells |
| 1 | `CALCULATE_DECO` | MCU runs a decompression algorithm (requires `UNDERSTAND_PPO2` + `DEPTH_SENSOR`) |
| 2 | `SETPOINT_MAINTENANCE` | MCU can fire solenoids to maintain a target ppO₂ (requires `UNDERSTAND_PPO2` + `O2_SOLENOID_DRIVER`) |
| 3 | `DISPLAY_PPO2` | MCU drives a ppO₂-capable display (requires `UNDERSTAND_PPO2` + ppO₂-capable display module) |
| 4 | `DISPLAY_DECO` | MCU drives a deco-capable display (requires `CALCULATE_DECO` + deco-capable display module) |
| 5 | `AUTO_CALIBRATION` | MCU can trigger O₂ solenoid for an automated calibration sequence (requires `UNDERSTAND_PPO2` + `O2_SOLENOID_DRIVER` + `BAROMETRIC_SENSOR`) |
| 6–7 | (reserved) | Must be `0x0`; ignore on read |

---

## Module Type Registry

Each module type may appear multiple times in the capability payload (one entry per
physical instance). The `instance_id` field is a 0-based index scoped per type
(e.g., two O₂ cell readers: instance `0` and instance `1`).

Vendor extensions are not supported. This registry is the sole authority for type IDs.

| ID | Name | Description |
|---|---|---|
| `0x01` | `O2_CELL_READER` | Reads oxygen partial pressure (analog or digital) |
| `0x02` | `CO2_CELL_READER` | Reads CO₂ partial pressure (analog) |
| `0x03` | `CO_READER` | Reads carbon monoxide concentration (analog, ppm) |
| `0x04` | `HE_READER` | Reads helium partial pressure (analog or digital) |
| `0x05` | `O2_SOLENOID_DRIVER` | Controls O₂ injection solenoid(s) |
| `0x06` | `DILUENT_SOLENOID_DRIVER` | Controls diluent injection solenoid(s) |
| `0x07` | `BAROMETRIC_SENSOR` | Atmospheric pressure (surface reference) |
| `0x08` | `DEPTH_SENSOR` | Water depth reading |
| `0x09` | `CO2_TEMP_STICK` | Temperature series across CO₂ scrubber |
| `0x0A` | `STATUS_LIGHT` | Visual OK/warning/error indicator |
| `0x0B` | `PPO2_DISPLAY` | Dedicated ppO₂ display |
| `0x0C` | `DECO_DISPLAY` | Dedicated decompression display |
| `0x0D` | `GENERAL_SCREEN` | Multipurpose display (sub-capabilities declared in payload) |
| `0x0E` | `FLASH_MEMORY` | Non-volatile storage for dive logs and configuration data |
| `0x0F` | `BUTTONS` | User input device (button or encoder) |
| `0x10` | `WATER_CONTACT_SENSOR` | Detects whether the controller is submerged |
| `0x11` | `BUZZER` | Audible alarm output |
| `0x12–0xFF` | (reserved) | Must not be used |

---

## Feature Enablement Matrix

Companion app features exist to **configure** MCU and module functionality.
Each feature is only shown when the required hardware and MCU capabilities are present.
Features absent from the hardware are **hidden** (not greyed out) to avoid implying
unavailable functionality.

| App Feature | Required Capabilities | Notes |
|---|---|---|
| Cell calibration (manual) | ≥1 `O2_CELL_READER` with `cell_type=ANALOG` | Requires setting calibration gas |
| Cell calibration (automatic) | ≥1 `O2_CELL_READER` (`ANALOG`) + `O2_SOLENOID_DRIVER` + `BAROMETRIC_SENSOR` + MCU:`AUTO_CALIBRATION` | Requires setting calibration gas |
| Gas settings | MCU:`UNDERSTAND_PPO2` or MCU:`CALCULATE_DECO` | O₂ and/or diluent gas mix; used for calibration and/or deco calculation |
| Setpoint management | MCU:`SETPOINT_MAINTENANCE` | Target ppO₂ configuration |
| ppO₂ HUD settings | `STATUS_LIGHT`.`supports_ppo2_leds` or `GENERAL_SCREEN`.`acts_as_status_light` | LED-based ppO₂ display configuration |
| Deco HUD settings | `STATUS_LIGHT`.`supports_deco_leds` | LED-based deco indicator configuration |
| ppO₂ numeric settings | `PPO2_DISPLAY` or `GENERAL_SCREEN`.`acts_as_ppo2_display` | Graphical ppO₂ display configuration |
| Deco numeric settings | `DECO_DISPLAY` or `GENERAL_SCREEN`.`acts_as_deco_display` | Graphical deco display configuration |
| Dive log | `FLASH_MEMORY` | Access to stored dive records |
| In-dive controls | `BUTTONS` | Hardware button/encoder configuration |

---

## Capability Exchange Process

```
Firmware (Peripheral)                    Companion App (Central)
      |                                         |
      | [boot: enumerate CCRAN bus]             |
      | [detect attached modules]               |
      | [build CapabilityDescriptor blob]       |
      | [register Capability Service L2]        |
      |                                         |
      |   ← BLE connection established ←        |
      |   ← SMP bonding (L2) complete ←         |
      |                                         |
      |   ← ATT Read (CapabilityDescriptor) ←   |
      | → CapabilityDescriptor payload →        |
      |                                         |
      |                          [parse header] |
      |                  [parse TLV module list]|
      |              [evaluate feature matrix]  |
      |             [enable/disable UI sections]|
      |                                         |
```

**Step-by-step:**

1. **Boot** — MCU enumerates the CCRAN bus, detects attached modules, and builds an
   in-memory capability record. This record does not change while the device is running.

2. **Register** — The Capability Service characteristic is registered at L2
   (bonded connections only).

3. **Connect + Bond** — Standard pairing flow via Device Service (see
   `services.md`). Capability Service is not accessible before bonding.

4. **Read** — After bonding, the companion app reads `CapabilityDescriptor`
   (Long Read if the payload exceeds `ATT_MTU − 1` bytes).

5. **Parse header** — Extract `protocol_version`, `mcu_flags`, `module_count`,
   `body_length`. If `protocol_version` is greater than the version understood by
   the app, log a warning and attempt best-effort parsing.

6. **Parse TLV body** — Iterate `module_count` module descriptors. For each:
   - If `type_id` is unknown → skip `L` bytes and continue (forward-compatibility rule).
   - If `type_id` is known → decode and store per-type properties.

7. **Evaluate matrix** — Match the accumulated capability set against the feature
   enablement matrix above.

8. **UI adaptation** — Show or hide app sections. Features requiring absent capabilities
   are hidden entirely; they do not appear as greyed-out or disabled.

---

## Forward Compatibility Rules

The TLV encoding is designed to tolerate future additions without breaking older
companion apps:

- **Unknown type IDs**: The app MUST skip `L` bytes and continue parsing. It MUST NOT
  abort or report an error when it encounters an unrecognized type.
- **Unknown protocol versions**: If `protocol_version > 0x01`, the app should log a
  warning and attempt to parse using its current understanding. Fields that are parsed
  correctly should be used; unknown fields should be ignored.
- **Reserved bytes**: Reserved bytes in the fixed header and per-type data fields are
  currently `0x00`. Apps MUST ignore their value to allow future use.
- **Reserved flag bits**: Bit fields with `reserved` bits must be read as `0` today.
  Apps MUST ignore non-zero values in reserved bits.

See `packets.md` for byte-precise payload format.
