# Safety Policy

## Specification Errors Are Dangerous

The openCCR documentation repository contains **authoritative protocol specifications** — BLE packet formats, CCRAN inter-board message definitions, alarm semantics, and control message structures — that firmware and companion-app implementations are built against directly.

A specification error is not merely a documentation defect. If an incorrect spec is used as the reference for a firmware build:

- Alarm thresholds may be silently misconfigured
- Safety-critical control messages may be misinterpreted
- Sensor readings may be processed with incorrect scaling or byte ordering
- The resulting firmware ships on life-support equipment used during dives

This repository is:

- **Not a dive instrument itself** — but the specifications here directly determine the behaviour of firmware that runs on dive instruments
- **Not validated** for correctness, safety, or completeness as a life-support instrument reference
- **Not certified** under any regulatory or medical device framework

Specification accuracy matters.

---

## Reporting Specification Errors

If you find an error in a protocol specification — incorrect field width, wrong byte ordering, missing error case, incorrect alarm semantics, or any other defect that could cause incorrect firmware behaviour — report it immediately.

Public reporting is essential because every firmware build derived from this repository may be affected.

**Open a Doc error issue**: [github.com/openccr/docs/issues/new/choose](https://github.com/openccr/docs/issues/new/choose)

Select **"Doc error"** and use the `[SAFETY]` title prefix for safety-relevant specification errors, e.g.:

```
[SAFETY] CCRAN alarm message field width incorrect — 2 bytes not 1
[SAFETY] BLE PO₂ packet byte ordering underdefined — big-endian assumed but not stated
[SAFETY] Setpoint command range check missing from spec — firmware accepts invalid values
```

Include in your report:

- The affected document and section
- The exact incorrect text or omission
- The correct specification (with source or rationale if known)
- Known or potential firmware impact
- Any firmware versions or companion-app versions known to have been built against the incorrect spec

---

## Responsible Disclosure

For specification errors where the defect could lead to a dangerous firmware build or a dangerous dive, contact the safety team directly before public disclosure:

**Email**: [safety@openccr.org](mailto:safety@openccr.org)

Response timeline:

- **Acknowledge** within 72 hours
- **Corrected specification** within 14 days
- **Public disclosure** on the issue tracker following correction

---

## Disclaimer

The openCCR project and its contributors provide this documentation with **no warranty of any kind**. Protocol specifications describe the openCCR system as designed; they do not constitute a guarantee of correctness, completeness, or fitness for any purpose. Use is entirely at your own risk. See [LICENSE.md](LICENSE.md) for full terms.
