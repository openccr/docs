SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus protocol

Rebus is the inter-board CAN-bus protocol for intra-firmware communication.
This documentation is derived from `openccr_discovery.h`,
`openccr_types.h`, and the Rebus wire-profile assignments documented below.

The original `openccr_discovery.h` and `openccr_types.h` declarations are not
included in this repository, so this documentation cannot independently
confirm divergence from those unavailable sources.

## Documents
- [Agent implementation guide](AGENTS.md) — minimal topic-specific read sets
  and document ownership.

- [Wire profile](profile.md) — commissioned selected-profile rules, identifiers,
  physical admission, and capacity.
- [Discovery](discovery/README.md) — decentralized node claims, active-owner
  rejection, addressing, and arbitration. The [claim lifecycle](discovery/lifecycle.md)
  and [identity resolution](discovery/identity.md) files own the detailed behavior.
- [Design decisions](design-decisions.md) — rationale for persistence,
  reboot recovery, and other implementation choices.
- [Message catalogue](messages/README.md) — physical-validation reading order
  and links to the message-specific payload owners.
- [Inventory manifests](messages/inventory/README.md) — profile-aware transport,
  canonical envelope, semantic resource model, and registry assignments.
- [Telemetry](messages/telemetry/README.md) — scalar and structured framing,
  value registries, control requests, and receiver-local subscriptions.
- [Wire encoding](encoding.md) — profile-aware CAN payload encoding, byte
  order, raw-DLC mapping, and declaration requirements.
- [Defined-rule issues](open-issues.md) — evidenced inconsistencies and edge cases in completed rules.
- [Missing functionality](missing-functionality.md) — referenced contracts that still need definition; no implementation defaults.

## Applicability and reading order

This index is non-normative navigation. The single applicability legend is in
the [agent implementation guide](AGENTS.md#applicability-legend): the
normative owner marks its completed **COMMON**, **CLASSIC CAN**, and **CAN FD**
scopes.

Before decoding a physical Rebus frame, read the commissioned selected-profile
gate in [wire profile](profile.md), then [wire encoding](encoding.md), then the
applicable message or lifecycle owner. The linked owners allocate
pre-dispatch physical rejection to profile, FD decoded-length mapping to
encoding, and post-gate message validation to the named owner; profile
selection is determined by the [wire profile](profile.md), not this index.

The [agent implementation guide](AGENTS.md#minimal-read-sets) gives the
topic-specific required read sets. The [discovery lifecycle](discovery/lifecycle.md)
owns decentralized node claims and active-owner rejection; [discovery identity](discovery/identity.md)
owns identity resolution and duplicate-UUID handling. The [wire profile](profile.md)
supersedes only conflicting original source declarations within its own scope.
Items in [missing functionality](missing-functionality.md) remain undefined and
are not defaults; [defined-rule issues](open-issues.md) identify problems in
rules that have already been stated.
