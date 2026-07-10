# openCCR Documentation

Protocol specifications and technical documentation for the openCCR rebreather platform.

## Contents

This repository covers:

- **BLE protocol** — discovery, GATT service definitions, and packet payload formats for firmware↔companion-app communication
- **CCRAN protocol** — inter-board CAN-bus protocol specification for intra-firmware communication between openCCR controller boards

This is a documentation-only repository. Source code lives in the sibling repositories listed below.

## Repository Structure

```
docs/
├── ble/           # BLE discovery and GATT packet definitions
│   ├── discovery/ # Advertising, scanning, connection establishment
│   ├── services/  # GATT service and characteristic definitions
│   └── packets/   # Packet payload formats
├── ccran/         # CCRAN inter-board CAN-bus protocol
│   ├── protocol/  # Protocol overview, framing, addressing
│   ├── messages/  # Message type catalogue and payloads
│   └── frames/    # Low-level frame format and encoding
└── licenses/
```

## Related Repositories

| Repository | Description |
|---|---|
| [openccr/firmware](https://github.com/openccr/firmware) | Zephyr RTOS firmware for all openCCR boards |
| [openccr/companion-app](https://github.com/openccr/companion-app) | Flutter iOS/Android companion app |
| [openccr/hardware](https://github.com/openccr/hardware) | KiCad schematics and PCB designs |
| [openccr/openccr.github.io](https://github.com/openccr/openccr.github.io) | Project website |

## License

All content in this repository is licensed under **CC BY 4.0** (Creative Commons Attribution 4.0 International).

See [LICENSE.md](LICENSE.md) for the full licensing framework.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributors must sign the [Contributor License Agreement](CLA.md) before their first pull request is merged.

---

© 2026 openCCR contributors
