SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus messages

## Scope

This is a non-normative catalogue of assigned Rebus messages and their
post-gate logical owners. It does not allocate identifiers, define profile
admission, or duplicate payload validation.

## Applicability and physical reading path

The [agent implementation guide](../AGENTS.md#applicability-legend) defines
the **COMMON**, **CLASSIC CAN**, and **CAN FD** markers used by the normative
owners. For every catalogue entry, [wire profile](../profile.md) owns the
selected physical gate and rejects invalid or wrong-profile forms before
dispatch. [Wire encoding](../encoding.md) owns FD raw-DLC-to-decoded-length
mapping. Only after those owners admit a frame does the row's logical owner
apply its fixed or transfer-class decoded-length and payload rules.

## Catalogue

| Message | Post-gate logical owner |
|---|---|
| Node claim | [node claim](node-claim.md) |
| Claim rejection | [claim rejection](claim-reject.md) |
| UUID collision | [UUID collision](uuid-collision.md) |
| Identity query | [WHO_ARE_YOU](who-are-you.md) |
| Manifest query | [inventory transport](inventory/transport.md#manifest-query) |
| Manifest advertisement | [inventory transport](inventory/transport.md#manifest-advertisement) |
| Manifest transfer start | [inventory transport](inventory/transport.md#manifest-transfer-start-and-chunks) |
| Manifest chunk | [inventory transport](inventory/transport.md#manifest-transfer-start-and-chunks) |
| Scalar telemetry | [scalar telemetry](telemetry/scalar.md) |
| Structured snapshot chunk | [structured snapshots](telemetry/structured.md) |
| Telemetry control request | [telemetry control](telemetry/control.md) |

- [Node claim](node-claim.md) — hardware identity payload.
- [WHO_ARE_YOU](who-are-you.md) — targeted or broadcast identity query.
- [UUID_COLLISION](uuid-collision.md) — bus-wide duplicate-UUID diagnostic.
- [Claim rejection](claim-reject.md) — targeted claimant rejection.
- [Inventory manifests](inventory/README.md) — manifest transport, content
  envelope, semantic resource model, and registry assignments.
- [Telemetry](telemetry/README.md) — scalar values, structured snapshots,
  value registries, control requests, and receiver-local subscriptions.

Node claims, collision diagnostics, and rejection participate in the
decentralized procedure described in [discovery](../discovery/README.md). Session
reset remains an unassigned control message; it must not alter the node-claim
payload.
