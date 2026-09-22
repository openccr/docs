SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus discovery

## Scope and precedence

This directory defines decentralized Rebus discovery: commissioned admission,
node-claim lifecycle, ownership recovery, and UUID-to-node-ID identity
resolution. The [wire profile](../profile.md) owns identifiers, frame format,
transmission recovery, capacity, and commissioned admission. Unassigned control
formats are listed in [open issues](../open-issues.md) and MUST NOT be guessed.

Discovery references message specifications for their payloads and
message-specific validation; it does not redefine those contracts.

## Protocol orientation

**Non-normative reading path:** start with commissioned admission and candidate
selection in [lifecycle.md](lifecycle.md), follow its claim procedure through
activation and recovery, then read [identity.md](identity.md) for identity
queries, binding changes, and duplicate-UUID fault handling. Consult the message
files named in each owner before encoding or accepting a frame.

## File map

| File | Owner | Primary consumer |
|---|---|---|
| [README.md](README.md) | Discovery scope, navigation, and task read sets | Discovery implementers |
| [lifecycle.md](lifecycle.md) | Claim admission, candidate lifecycle, ownership recovery, activation handoff, and persistence | Node lifecycle implementation |
| [identity.md](identity.md) | Identity queries, UUID collision handling, bindings, and identity-generation invalidation | Identity resolution implementation |

## Task read sets

| Task | Required read set |
|---|---|
| Claim lifecycle | [profile](../profile.md), [discovery README](README.md), [lifecycle](lifecycle.md), [node claim](../messages/node-claim.md), [claim reject](../messages/claim-reject.md) |
| Identity resolution | [profile](../profile.md), [discovery README](README.md), [identity](identity.md), [node claim](../messages/node-claim.md), [WHO_ARE_YOU](../messages/who-are-you.md), [UUID collision](../messages/uuid-collision.md) |
| Full discovery | [profile](../profile.md), [encoding](../encoding.md), [discovery README](README.md), [lifecycle](lifecycle.md), [identity](identity.md), [node claim](../messages/node-claim.md), [claim reject](../messages/claim-reject.md), [WHO_ARE_YOU](../messages/who-are-you.md), [UUID collision](../messages/uuid-collision.md) |

## Boundary warnings

[Profile](../profile.md) owns the frame gate, CAN identifiers, capacity, and
commissioned admission. [Wire encoding](../encoding.md) owns byte order and
physical serialization. The discovery message files own payload byte layouts and
message-specific validation. [Inventory transport](../messages/inventory/transport.md)
owns manifest advertisement and transfer behavior; [telemetry](../messages/telemetry/README.md)
owns telemetry acceptance, sequencing, and receiver-local state.

## Cross-domain flow

After [lifecycle activation](lifecycle.md#inventory-manifest), the node follows
[inventory transport's manifest-advertisement process](../messages/inventory/transport.md#manifest-advertisement).
Receivers use discovery bindings when accepting inventory and telemetry state;
see [inventory transport](../messages/inventory/transport.md) and
[scalar telemetry](../messages/telemetry/scalar.md).

This README is navigation, not a substitute for normative rules.
