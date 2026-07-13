SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# BLE Discovery & Pairing

Advertising data layout, scan response, pairing state machine, and implementation notes.

---

## Advertising Data

openCCR uses a dual-packet advertising scheme:

- **Primary advertising PDU** (up to 31 bytes): Flags + Complete Local Name
- **Scan response PDU** (27 bytes): Complete 128-bit Service UUID list + Manufacturer Specific Data

Manufacturer data is in the scan response (not the primary PDU) so that the primary PDU
can accommodate device names up to 26 characters without overflow. iOS and Android active
scanning both deliver scan responses; iOS background scanning delivers scan responses when
filtering by service UUID.

### Device Name

The advertised local name is either:

- **Saved name**: a user-configured name stored in NVS (set via a future characteristic; TBD).
- **Default name**: `openCCR-XXXXXX` where XXXXXX = last 3 bytes of the BLE MAC address
  in uppercase hex. Example: MAC `AA:BB:CC:DD:EE:FF` → name `openCCR-DDEEFF`.

The name is **not** derived from the serial number and does **not** expose the pairing key.

**Advertising name length**: firmware stores names up to 32 characters in NVS. The primary
advertising PDU accommodates names up to **26 characters** (31-byte PDU limit: 3 bytes Flags
+ 2-byte AD header + 26 bytes name). If the stored name exceeds 26 characters, firmware
advertises the first 26 characters. The full name is readable via the Generic Access Profile
`Device Name` characteristic after connection.

### Primary Advertising PDU — variable length (17 bytes min; 31 bytes max)

| Byte(s) | Value | Description |
|---|---|---|
| 0 | `0x02` | AD Length = 2 |
| 1 | `0x01` | AD Type = Flags |
| 2 | `0x06` | LE General Discoverable \| BR/EDR Not Supported |
| 3 | `0x01` + N | AD Length = 1 + N (where N = advertised name length, 1–26) |
| 4 | `0x09` | AD Type = Complete Local Name |
| 5–(4+N) | ASCII | Device name (N bytes; `"openCCR-XXXXXX"` = 14 chars for default) |

Primary PDU total: 3 + 2 + N bytes. For default 14-char name: **19 bytes**.

`has_companion` flag is carried in the scan response Manufacturer Specific Data (see below).

### Scan Response PDU — 27 bytes (fixed)

| Byte(s) | Value | Description |
|---|---|---|
| 0 | `0x11` | AD Length = 17 |
| 1 | `0x07` | AD Type = Complete list of 128-bit Service UUIDs |
| 2–17 | bytes | Device Service UUID in little-endian: `52 43 43 4f 01 00 00 00 45 18 00 00 00 00 00 00` |
| 18 | `0x08` | AD Length = 8 |
| 19 | `0xFF` | AD Type = Manufacturer Specific Data |
| 20–21 | LE16 | Company ID: `0xFF 0xFF` (dev placeholder; register with Bluetooth SIG for production) |
| 22 | uint8 | Protocol version = `0x01` |
| 23 | uint8 | Firmware major version |
| 24 | uint8 | Firmware minor version |
| 25 | uint8 | Firmware patch version |
| 26 | uint8 | Flags: bit 0 = `has_companion`; bits 1–7 = reserved (must be 0) |

`has_companion` (bit 0 of byte 26): set when the device has an active BLE bond stored in NVS.

The Device Service UUID is `4f434352-0001-0000-1845-000000000000`. In little-endian
byte order (each UUID field reversed independently):

```
4f434352 → 52 43 43 4f
0001     → 01 00
0000     → 00 00
1845     → 45 18
000000000000 → 00 00 00 00 00 00
```

---

## Pairing State Machine

### States

| State | Description |
|---|---|
| `ADVERTISING_UNPAIRED` | No bond; advertising to all scanners |
| `CONNECTED_UNPAIRED` | Central connected; key exchange in progress |
| `BONDING_IN_PROGRESS` | Key accepted; SMP bonding under way |
| `PAIRED_CONNECTED` | Bonded and connected |
| `ADVERTISING_PAIRED` | Bonded but not connected; advertising to bonded address |
| `LOCKED_OUT` | Three failed key attempts; 30-second lockout active |

### Transitions

| Current State | Event | Next State | Firmware Action |
|---|---|---|---|
| `ADVERTISING_UNPAIRED` | Connection established | `CONNECTED_UNPAIRED` | Stop advertising; start 60 s inactivity timer |
| `ADVERTISING_UNPAIRED` | BLE stack error | `ADVERTISING_UNPAIRED` | Reset BT stack; restart advertising |
| `CONNECTED_UNPAIRED` | PairingKey write — correct key, attempts < 3 | `BONDING_IN_PROGRESS` | Set PairingResult = `PENDING`; call `bt_conn_set_security(L2)` |
| `CONNECTED_UNPAIRED` | PairingKey write — wrong key, attempt 1 or 2 | `CONNECTED_UNPAIRED` | Increment fail counter; set PairingResult = `FAIL_WRONG_KEY` |
| `CONNECTED_UNPAIRED` | PairingKey write — wrong key, attempt 3 | `LOCKED_OUT` | Set PairingResult = `FAIL_LOCKED_OUT`; start 30 s timer; disconnect |
| `CONNECTED_UNPAIRED` | Inactivity timer fires | `ADVERTISING_UNPAIRED` | Disconnect; restart advertising |
| `CONNECTED_UNPAIRED` | Connection lost | `ADVERTISING_UNPAIRED` | Reset fail counter; restart advertising |
| `BONDING_IN_PROGRESS` | SMP bonding success | `PAIRED_CONNECTED` | Set PairingResult = `SUCCESS`; store bond in NVS; notify app |
| `BONDING_IN_PROGRESS` | SMP bonding failure | `CONNECTED_UNPAIRED` | Set PairingResult = `FAIL_BONDING`; allow retry |
| `BONDING_IN_PROGRESS` | Connection lost | `ADVERTISING_UNPAIRED` | Discard partial bond; restart advertising |
| `PAIRED_CONNECTED` | Connection lost | `ADVERTISING_PAIRED` | Start directed advertising to bonded address (10 s); then switch to undirected |
| `PAIRED_CONNECTED` | PairingKey write (device already bonded) | `PAIRED_CONNECTED` | Set PairingResult = `FAIL_ALREADY_PAIRED`; no other action |
| `ADVERTISING_PAIRED` | Connection established | `PAIRED_CONNECTED` | Stop advertising; verify bond |
| `LOCKED_OUT` | 30 s timer fires and connection is lost | `ADVERTISING_UNPAIRED` | Reset fail counter; restart advertising |

### Timers

| Timer | Duration | Purpose |
|---|---|---|
| Inactivity | 60 s | Disconnect idle unpaired centrals |
| Lockout | 30 s | Enforce key-attempt rate limit |
| Directed advertising | 10 s | Attempt fast reconnect to bonded address before falling back to undirected |

---

## Error Handling

| Condition | Firmware Response |
|---|---|
| Wrong key, attempt 1 or 2 | Notify `FAIL_WRONG_KEY`; remain in `CONNECTED_UNPAIRED` |
| Wrong key, attempt 3 | Notify `FAIL_LOCKED_OUT`; disconnect; start 30 s lockout |
| Connection lost before bonding | Reset fail counter; restart advertising |
| SMP bonding failure | Notify `FAIL_BONDING`; remain connected; permit retry |
| Partial bond on connection loss during bonding | Discard bond data from NVS |
| BLE stack error during advertising | Reset stack; restart advertising |

---

## Companion App Scan Behavior

### Identifying openCCR Devices

Filter on **service UUID** `4f434352-0001-0000-1845-000000000000` in the scan response.
Do not filter on the local name — the name may be a user-configured string that does
not follow the `openCCR-XXXXXX` pattern. The service UUID is the only reliable identifier.

After matching by service UUID, parse the manufacturer-specific data from the **scan
response** PDU (fixed offsets — not affected by name length).

1. Verify Company ID = `0xFFFF` (dev builds) or registered production value.
2. Verify protocol version field = `0x01`.
3. Read firmware version fields (major, minor, patch).
4. Read flags field (bit 0 = `has_companion`).

### Interpreting `has_companion` (flags bit 0)

| `has_companion` | Bond key matches this app | Meaning |
|---|---|---|
| `0` | N/A | Device has never been paired; proceed with pairing flow |
| `1` | Yes | Device is bonded to this app; connect and auto-encrypt |
| `1` | No | Device is bonded to a different companion app |

**"Paired with this app"** is determined by attempting to connect with the stored bond.
If the BLE stack reports an authentication error, the bond belongs to a different app.
Do not rely solely on the local address or device name.

### Recommended Scan Flow

1. Start BLE scan filtered by service UUID.
2. For each discovered device:
   a. Parse manufacturer-specific data to extract firmware version and flags.
   b. If `has_companion == 0`: show "Pair this device" UI.
   c. If `has_companion == 1`: attempt connection; if bond succeeds, go to main UI;
      if bond fails, show "Device paired with another app" message.
3. Stop scanning once the target device is connected.

---

## Zephyr Implementation Notes

> **Non-normative.** These are hints for the firmware implementer, not part of the protocol contract.

### Relevant Kconfig Options

```
CONFIG_BT=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_SMP=y
CONFIG_BT_BONDABLE=y
CONFIG_BT_SETTINGS=y          # persist bonds across resets
CONFIG_BT_MAX_CONN=1
CONFIG_BT_DEVICE_NAME="openCCR-XXXXXX"   # set dynamically: saved name from NVS, or
                                          # "openCCR-" + last 3 bytes of BLE MAC in hex
CONFIG_BT_DEVICE_APPEARANCE=0
```

### Advertising API Sketch

Manufacturer data is in the scan response so the primary PDU can hold names up to 26 chars.

```c
/* Primary advertising data: Flags + Name only */
static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR),
    BT_DATA(BT_DATA_NAME_COMPLETE, device_name, device_name_len), /* max 26 bytes */
};

/* Scan response: Service UUID + Manufacturer Specific Data (fixed 27-byte PDU) */
static const struct bt_data sd[] = {
    BT_DATA_BYTES(BT_DATA_UUID128_ALL,
        0x52, 0x43, 0x43, 0x4f,   /* 4f434352 LE */
        0x01, 0x00,               /* 0001 LE */
        0x00, 0x00,               /* 0000 LE */
        0x45, 0x18,               /* 1845 LE */
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    BT_DATA(BT_DATA_MANUFACTURER_DATA, mfr_data, sizeof(mfr_data)),
};
```

`device_name` must be at most 26 bytes; truncate at 26 if the NVS-stored name is longer.

Set security after key validation:

```c
bt_conn_set_security(conn, BT_SECURITY_L2);
```

---

## flutter_blue_plus Implementation Notes

> **Non-normative.** These are hints for the companion app implementer, not part of the protocol contract.

### Scan Filter

```dart
FlutterBluePlus.startScan(
  withServices: [Guid('4f434352-0001-0000-1845-000000000000')],
);
```

### Parsing Manufacturer Data

`flutter_blue_plus` merges primary PDU and scan response into one `ScanResult`.
Manufacturer data is keyed by Company ID — no offset arithmetic needed regardless
of name length.

```dart
// Manufacturer data is in the scan response; flutter_blue_plus merges it transparently.
final mfr = scanResult.advertisementData.manufacturerData;
final payload = mfr[0xFFFF]; // 0xFFFF = dev builds Company ID
if (payload != null && payload.length >= 5) {
  final protocolVersion = payload[0];  // must be 0x01
  final fwMajor = payload[1];
  final fwMinor = payload[2];
  final fwPatch = payload[3];
  final hasCompanion = (payload[4] & 0x01) != 0;
}
```

### Reconnection

`flutter_blue_plus` handles transparent re-encryption on reconnect when a bond exists.
No application-level reconnection logic is required beyond calling `device.connect()`.
