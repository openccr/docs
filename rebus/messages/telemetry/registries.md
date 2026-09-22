SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Telemetry value registries

## Scalar value representations

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
bytes at indexes `0`, `4`, `8`, or `12`, scaled exactly as `100*q/255`. Gas
kinds use two little-endian whole-millibar `uint16_t` values at even indexes
`0..14`. No other tissue context is valid; context selects pair versus quad and
no optional mode exists.

The legacy tissue contexts do not represent every structured tissue result.
They are limited to 16 compartments and do not provide a gas selector for
multiple saturation matrices. A decompression result such as four gas
saturation values across 16 or 32 tissues MUST use a manifest-declared
`STRUCTURED_SNAPSHOT`; it MUST NOT be coerced into an unrelated scalar or
legacy tissue context.
