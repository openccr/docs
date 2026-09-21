# Contributing to openCCR Documentation

We welcome documentation contributions from the community. This document covers requirements specific to this repository. For general project policies, see the [openCCR website](https://openccr.github.io).

---

## Safety First

**Specification errors are dangerous.** The BLE and rebus protocol specifications in this repository are the authoritative reference for firmware and companion-app implementations. An error in a protocol spec can propagate into firmware builds that ship on life-support equipment used during dives.

- Changes to protocol specifications that could cause incorrect firmware behaviour must include a `[SAFETY]` tag in the PR description.
- Changes affecting any of the following require review by **at least two contributors** before merge:
  - Packet payload formats, field widths, or byte ordering
  - Alarm or alert message definitions
  - Safety-critical control message definitions (setpoint commands, calibration commits, OTA triggers)
  - rebus addressing or arbitration rules
- Accuracy over style: if a specification is technically correct but awkward to read, fix the readability without changing the semantics. If you are unsure whether a change is semantically equivalent, note it explicitly in the PR.

---

## The Legal Stuff (Important)

openCCR uses a dual-licensing model. All contributors must sign the CLA.

**By submitting a Pull Request, you agree that:**

1. Your contribution is governed by the [openCCR Contributor License Agreement v1.0](CLA.md).
2. You authorize the openCCR non-profit (and its authorized commercial partners) to utilize, modify, and dual-license your contributions without restriction.

You will be prompted to sign the CLA automatically on your first Pull Request via our CLA bot. Unsigned PRs cannot be merged.

---

## How to Contribute

1. **Fork** this repository on GitHub.
2. **Sign the CLA** — prompted automatically on your first PR.
3. Create a **feature branch** from `main`.
4. Make your changes following the documentation guidelines below.
5. **Add SPDX headers** to all new files (see below).
6. Open a **Pull Request** with a clear description of what changed and why. Include a safety note if the change affects a protocol payload, alarm definition, or control message.

---

## Documentation Guidelines

### Accuracy

Specification text is normative. Word choices matter:

- Use **must** / **must not** for mandatory requirements (RFC 2119).
- Use **should** / **should not** for recommendations.
- Use **may** for permitted options.
- Do not use "will", "can", or "might" for requirements — they are ambiguous.

### Completeness

Protocol field tables must specify:

- Field name
- Byte offset and width
- Encoding (unsigned integer, IEEE 754, etc.)
- Valid range or enumeration
- Behaviour on out-of-range values

Omitting any of these makes the spec incomplete and may cause incorrect firmware behaviour.

### SPDX Headers

All new markdown files must include an SPDX header as the first lines of the file:

```
SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors
```

---

## Reporting Issues

Open an issue on this repository. For specification errors that could cause incorrect firmware behaviour — wrong packet format, incorrect field semantics, missing error handling — mark the issue **[SAFETY]** in the title.

For safety-relevant specification errors, see [SAFETY.md](SAFETY.md).

---

## Dual-Licensing Model

openCCR uses a dual-licensing model:

- **Open license** (CC BY 4.0) — for community use, research, and non-commercial implementations.
- **Commercial license** — available to commercial partners through the openCCR non-profit, funding continued development and ISO standardization work.

The CLA enables the non-profit to issue commercial licenses without requiring individual permission from each contributor. This is standard practice for open-source projects with a non-profit steward (examples: Eclipse Foundation, Linux kernel).
