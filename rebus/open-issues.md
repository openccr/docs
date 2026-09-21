SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus open issues

These are protocol gaps, not safe defaults. They must be resolved before
interoperable or safety-critical implementations are released.

## Identifiers and discovery

- CAN identifiers and wire formats for claim rejection, session reset, session
  reclaim, safety, and operational-control messages.
- Session identifier/generation, stale-frame handling, and authentication or
  physical authorization for explicit session reset.
- Protocol-version negotiation policy beyond the fixed v0.1 profile.


## Transport and validation

- CAN bus bit timing.
- Application-level retransmission, acknowledgement, timeout, and bus-error
  policy beyond the defined profile frame gate and node-claim transmission
  rules.
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
