SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Telemetry messages

## Scope

This domain defines Rebus scalar telemetry, structured telemetry snapshots,
telemetry-control requests, value registries, and receiver-local subscriptions.
It covers accepted telemetry after the profile frame gate and manifest binding;
it does not define physical serialization, discovery identity transitions, or
inventory output descriptors.

Subscriptions are receiver-local. They do not alter a source's cadence, message
contents, publisher roles, or shared sequence state. Inventory output
descriptors qualify telemetry acceptance, but telemetry files do not redefine
those descriptors.

## Normative file map

| File | Owner | Primary consumer |
|---|---|---|
| [scalar.md](scalar.md) | Scalar frame acceptance, publisher identity, and scalar sequencing | Scalar telemetry implementation |
| [structured.md](structured.md) | Structured snapshot chunking, assembly, and snapshot sequencing | Structured telemetry implementation |
| [registries.md](registries.md) | Scalar context, unit, and value-representation registries | Telemetry value validation |
| [control.md](control.md) | Telemetry-control requests and source scheduling | Telemetry-control implementation |
| [subscriptions.md](subscriptions.md) | Receiver-local subscription lifecycle | Receiver implementation |

## Dependencies

- [Profile](../../profile.md) owns the frame gate, identifier conventions, and
  cross-cutting identity state.
- [Wire encoding](../../encoding.md) owns byte order, physical CAN payload
  rules, padding, and declarations.
- [Discovery](../../discovery/README.md) owns node states, UUID-to-node-ID bindings,
  claims, and identity recovery.
- [Inventory model](../inventory/model.md) owns publisher output descriptors
  that qualify scalar and structured telemetry acceptance.

## Task read sets

| Task | Required read set |
|---|---|
| Implement scalar telemetry | [profile](../../profile.md), [encoding](../../encoding.md), [scalar](scalar.md), [registries](registries.md), [inventory model](../inventory/model.md), [inventory registries](../inventory/registries.md) |
| Implement structured telemetry | [profile](../../profile.md), [encoding](../../encoding.md), [scalar](scalar.md), [structured](structured.md), [registries](registries.md), [inventory model](../inventory/model.md), [inventory registries](../inventory/registries.md) |
| Implement telemetry control | [profile](../../profile.md), [encoding](../../encoding.md), [control](control.md), [registries](registries.md), [inventory model](../inventory/model.md) |
| Implement subscriptions | [subscriptions](subscriptions.md), [scalar](scalar.md), [discovery identity](../../discovery/identity.md) |

## Boundary warnings

[Profile](../../profile.md), [encoding](../../encoding.md), and
[discovery](../../discovery/README.md) own cross-cutting frame, serialization, and
identity rules. The [inventory model](../inventory/model.md) owns publisher
output descriptors: telemetry validates against them but does not redefine
their format, meaning, units, shapes, or origins. [Scalar telemetry](scalar.md)
owns the shared modulo ordering; structured telemetry links to it rather than
creating a second definition.

## Protocol flow

For human reference, read [scalar](scalar.md) → [structured](structured.md) →
[registries](registries.md) → [control](control.md) →
[subscriptions](subscriptions.md).

This README is navigation, not a substitute for normative rules.
