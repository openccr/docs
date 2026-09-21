SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus protocol

Rebus is the inter-board CAN-bus protocol for intra-firmware communication.
This documentation is derived from `openccr_discovery.h`,
`openccr_roles.h`, and `openccr_types.h`, plus the Rebus wire-profile
assignments documented below.

## Documents
- [Agent implementation guide](AGENTS.md) — minimal topic-specific read sets
  and document ownership.

- [Wire profile](profile.md) — normative profile rules and status.
- [Discovery](discovery.md) — decentralized node claim, confirmation,
  addressing, and arbitration.
- [Design decisions](design-decisions.md) — rationale for persistence,
  reboot recovery, and other implementation choices.
- [Message catalogue](messages/README.md) — message registry and fixed payloads.
- [Telemetry](messages/telemetry.md) — telemetry values, units, contexts, and
  tissue payloads.
- [Wire encoding](encoding.md) — CAN payload encoding, byte order, DLC, and
  declaration requirements.
- [Open issues](open-issues.md) — unresolved values and behaviors.

## Implementation rule

Each topic's owning document is authoritative; the [agent implementation
guide](AGENTS.md#ownership-and-precedence) names the owner and minimal read
set. The wire profile supersedes only conflicting original source declarations
within its own scope. Items in [open issues](open-issues.md) are undefined:
implementations must not guess them.
