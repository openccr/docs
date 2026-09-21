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

- [Wire profile](profile.md) — normative profile rules and status.
- [Discovery](discovery.md) — decentralized node claims, active-owner
  rejection, addressing, and arbitration.
- [Design decisions](design-decisions.md) — rationale for persistence,
  reboot recovery, and other implementation choices.
- [Message catalogue](messages/README.md) — message registry and fixed payloads.
- [Telemetry](messages/telemetry.md) — telemetry values, units, contexts, and
  tissue payloads.
- [Inventory manifest](messages/inventory.md) — static resources, telemetry
  outputs, configuration schemas, cache advertisement, and retrieval.
- [Wire encoding](encoding.md) — CAN payload encoding, byte order, DLC, and
  declaration requirements.
- [Open issues](open-issues.md) — unresolved values and behaviors.

## Implementation rule

Each topic's owning document is authoritative; the [agent implementation
guide](AGENTS.md#ownership-and-precedence) names the owner and minimal read
set. [Discovery](discovery.md) owns decentralized node claims and active-owner
rejection. The wire profile supersedes only conflicting original source
declarations within its own scope. Items in [open issues](open-issues.md) are
undefined: implementations must not guess them.
