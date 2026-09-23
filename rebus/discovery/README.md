SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus discovery

## Scope and applicability

This directory is non-normative navigation for decentralized Rebus discovery:
node-claim lifecycle, ownership recovery, and UUID-to-node-ID identity
resolution after commissioned physical admission. The [wire profile](../profile.md)
owns profile selection, identifiers, frame format, transmission recovery,
capacity, and commissioned admission; [wire encoding](../encoding.md) owns
physical payload decoding.

The completed rules in [lifecycle.md](lifecycle.md) and
[identity.md](identity.md) are **COMMON** logical rules after that owner path;
they do not define a separate discovery physical profile. Their message links
lead to the owners of payload shape and message-specific validation. Unassigned
control formats remain unresolved in the [missing-functionality deny-list](../missing-functionality.md).

## Protocol orientation

**Non-normative reading path:** begin with the commissioned selected-profile
gate in [profile.md](../profile.md), then read [wire encoding](../encoding.md)
for decoded physical payloads before following [lifecycle.md](lifecycle.md)
through claim activation and recovery or [identity.md](identity.md) through
identity queries, binding changes, and duplicate-UUID fault handling. The
selected gate owns pre-dispatch rejection; after it, use the linked message
owner for payload validation and the lifecycle or identity owner for state
effects.

## File map

| File | Owner | Primary consumer |
|---|---|---|
| [README.md](README.md) | Discovery scope, navigation, and task read sets | Discovery implementers |
| [lifecycle.md](lifecycle.md) | Claim admission, candidate lifecycle, ownership recovery, activation handoff, and persistence | Node lifecycle implementation |
| [identity.md](identity.md) | Identity queries, UUID collision handling, bindings, and identity-generation invalidation | Identity resolution implementation |

## Task read sets

| Task | Required read set |
|---|---|
| Claim lifecycle | [profile](../profile.md), [encoding](../encoding.md), [discovery README](README.md), [lifecycle](lifecycle.md), [node claim](../messages/node-claim.md), [claim reject](../messages/claim-reject.md) |
| Identity resolution | [profile](../profile.md), [encoding](../encoding.md), [discovery README](README.md), [identity](identity.md), [node claim](../messages/node-claim.md), [WHO_ARE_YOU](../messages/who-are-you.md), [UUID collision](../messages/uuid-collision.md) |
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
