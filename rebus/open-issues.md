SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus open issues

These are protocol gaps, not safe defaults. They must be resolved before
interoperable or safety-critical implementations are released.

## Identifiers and discovery

- CAN identifiers and wire formats for session reset, safety, and
  operational-control messages.
- Session identifier/generation, stale-frame handling, and authentication or
  physical authorization for explicit session reset.
- Protocol-version negotiation policy beyond the fixed v0.1 profile.
- Inventory manifest authentication and authorization: the manifest fingerprint
  is only a cache/lookup hint; define trusted management and configuration
  authorization before safety-critical configuration writes are released.

## Inventory registry population

Concrete resource, semantic, unit, value-type, transform, relation, parameter,
and constraint assignments remain undefined. Their canonical record-value
encodings and validation tables must be supplied before concrete inventory
manifests can be interoperable; implementations MUST NOT invent defaults for
those assignments.

## Safety, configuration, and maintenance

- Heartbeat identifier, payload, cadence, receive timeout, critical-node
  registry, and the Safety Watchdog's required fail-safe action.
- Parameter-catalogue locator and transfer, parameter read/write and
  synchronization messages, authorization, dive-state source, and
  surface-only enforcement for configuration mutation.
- Firmware image transport, complete-image cryptographic validation,
  authorization, target selection, update state machine, rollback, and
  surface-only enforcement for firmware dispatch.
- Operational-control identifiers and payloads, controller eligibility,
  sensor-validity inputs, deterministic multi-controller consensus, actuator
  command validation, and controller-failure fail-safe behavior.
- Telemetry-gateway forwarding, radio authorization, and the boundary between
  surface companion communication and the Rebus bus.

## Transport and validation

- CAN bus bit timing.
- Application-level retransmission, acknowledgement, timeout, and bus-error
  policy for operational control and other future traffic beyond node claims
  and telemetry control.
- Message-type discriminator for future payloads without assigned IDs.
- Reserved-bit handling for fields not already defined by a message document.
- Malformed-frame response beyond the defined discard-without-response rule.
- Authentication, integrity, and replay protection.

## Message semantics

- Sender and receiver filters, message periods, and timeouts for message
  fields or traffic not already defined by a message document.
- Behavior for unknown contexts, reserved codes, and context/unit mismatches in
  fields not already defined by a message document.
- Canonical unit and permitted numeric range for each scalar telemetry context.
