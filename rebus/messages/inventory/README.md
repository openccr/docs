SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Inventory manifests

## Scope

This domain defines Rebus inventory manifests: the static description of a
node's physical resources, software modules, telemetry outputs, relationships,
and configuration interfaces. It covers the manifest wire messages, fragmented
transfer, manifest cache rules, and manifest content envelope.

A manifest is descriptive. It does not authorize configuration writes, prove
firmware integrity, or replace the node-claim procedure.

The manifest is the authoritative source for concrete node properties. Rebus
has no separate wire-level role bitmask. A receiver derives any local service
classification from the resources and interfaces present in the manifest.

## Normative file map

| File | Owner | Primary consumer |
|---|---|---|
| [transport.md](transport.md) | Manifest message lifecycle, transfer, cache identity, and active-session behavior | Transfer implementation |
| [envelope.md](envelope.md) | Canonical manifest header, record stream, and TLV framing | Manifest validation |
| [model.md](model.md) | Resource, output, relation, parameter, and provenance semantics | Inventory model implementation |
| [registries.md](registries.md) | Assigned semantic values and registry-population contract | Registry validation |
| [authoring.md](authoring.md) | Non-normative YAML and contribution guidance | Manifest authors |

## Dependencies

- [Profile](../../profile.md) owns the frame gate and CAN identifier conventions.
- [Wire encoding](../../encoding.md) owns byte order, physical payload rules, padding, and declarations.
- [Discovery](../../discovery/README.md) owns node states, UUID-to-node-ID bindings, claims, and identity recovery.
- Telemetry output descriptors and their transport consumers depend on the inventory model; see [telemetry messages](../telemetry/README.md).

## Task read sets

| Task | Required read set |
|---|---|
| Encode or decode a manifest transfer | [profile](../../profile.md), [encoding](../../encoding.md), [transport](transport.md) |
| Validate manifest bytes | [encoding](../../encoding.md), [envelope](envelope.md), [registries](registries.md) |
| Implement inventory resources or outputs | [envelope](envelope.md), [model](model.md), [registries](registries.md) |

## Boundary warnings

[Profile](../../profile.md), [encoding](../../encoding.md), and [discovery](../../discovery/README.md) own cross-cutting rules. Inventory documents MUST link to those owners rather than redefine frame admission, serialization, or identity behavior. In particular, manifest transport does not authorize configuration operations, and the manifest model does not assign new registry values.

## Protocol flow

For human reference, read [transport](transport.md) → [envelope](envelope.md) → [model](model.md) → [registries](registries.md) → [authoring](authoring.md).

This README is navigation, not a substitute for normative rules.
