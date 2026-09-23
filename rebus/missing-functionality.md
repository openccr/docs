SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus functionality awaiting definition

This is a deny-list, not a source of implicit defaults. The linked completed
rules describe the dependency or boundary, not the missing contract. Do not
transmit unassigned messages or invent wire values, authorization, policy, or
profile applicability. [Issues in already specified rules](open-issues.md) are
tracked separately. Items retained as **future scope** are not prerequisites
for implementing the assigned v0.1 traffic.

## Dependencies of specified functionality

### Identity, admission, and security

- **Authentication, integrity, replay protection, and manifest trust:**
  [Manifest transport](messages/inventory/transport.md#manifest-advertisement)
  calls the fingerprint a cache hint, not a credential; the
  [inventory boundary](messages/inventory/README.md#scope) does not authorize
  writes. A [targeted claim rejection](discovery/lifecycle.md#active-owner-rejection-and-recovery)
  can force candidate loss without sender authentication, and a
  [collision diagnostic](discovery/identity.md#duplicate-uuid-detection) can
  force terminal `IDENTITY_FAULT` without a freshness or origin proof. Define
  message trust and replay/freshness policy, plus trusted management and
  configuration authorization, before these frames or a manifest can serve as
  safety-critical authority. Hash-prefix validation alone does not do so.
- **Deployment commissioning values:** [Admission](profile.md#commissioned-bootstrap-admission)
  requires a selected profile, nominal bit rate, BRS policy, calculated
  `N_max`, its timing inputs and, for FD, a data bit rate; the
  [capacity proof](profile.md#discovery-capacity) requires reproducible frame
  costs. Choose actual values for each deployment. Timing segments, sample
  points, oscillator tolerance, topology and termination still need physical
  engineering limits, but the current profile does not prescribe their
  numeric values or explicitly require those fields in the admission record.

### Discovery and identity integration

- **Ordinary claim-to-binding handoff:** [Five-claim activation](discovery/lifecycle.md#cooperative-claim-procedure)
  precedes [manifest advertisement](discovery/lifecycle.md#inventory-manifest),
  but [identity binding](discovery/identity.md#identity-binding-and-generation)
  only defines what happens *when* discovery establishes a binding; the
  [identity-query path](discovery/identity.md#identity-query) explicitly binds
  a correlated reminder. Define when a receiver observing ordinary valid
  claims establishes/refreshes `(node_id, UUID, identity_generation)`, or
  require an explicit query before UUID-bound manifest activation. Otherwise
  a receiver that sees all five claims cannot necessarily accept the first
  advertisement and subsequent telemetry.
- **Identity-query correlation and freshness:** [WHO_ARE_YOU](messages/who-are-you.md#payload)
  carries a requester ID but no request instance token;
  [identity reminders](discovery/identity.md#identity-query) reuse the
  undifferentiated node-claim frame. Define the correlation window, duplicate
  query identity, late response treatment and stale-claim rejection so a
  delayed claim cannot replace a live UUID binding or revoke source-bound
  state after an unrelated query. A local timer alone does not prove sender
  identity.
- **Claim receive-origin and self-view:** [Duplicate UUID detection](discovery/identity.md#duplicate-uuid-detection)
  exempts only the node's own locally submitted claim; define how loopback and
  delayed local transmission are identified across driver recovery so a node
  neither faults on itself nor filters a foreign duplicate. Qualify the
  persisted `(UUID, last_active_node_id)` identity-reminder exemption when the
  node is no longer ACTIVE at that ID; otherwise a stale correlated reminder
  can be mistaken for its own returning identity.

### Inventory and telemetry semantics

- **Concrete inventory registry population:** [Inventory registries](messages/inventory/registries.md#registry-population-contract)
  define the table format and already assign some origins, endpoint values and
  delivery classes, but not every resource, semantic, unit, value type, shape,
  transform, relation, parameter, or constraint. Supply stable numeric values,
  canonical record-value encodings, validation and relation/constraint tables
  for concrete interoperable manifests; do not treat illustrative names in
  [authoring guidance](messages/inventory/authoring.md) as assignments.
- **Scalar context units and ranges:** [Telemetry registries](messages/telemetry/registries.md#unit-vocabulary)
  assign context representations but not a canonical unit and permitted numeric
  range per scalar context. Specify each mapping and invalid range before
  interpreting, converting, or safety-qualifying received measurements.
- **Structured-output selector context:** [Output descriptors](messages/inventory/model.md#resource-model),
  [telemetry control](messages/telemetry/control.md#frames-and-payload), and
  [local subscriptions](messages/telemetry/subscriptions.md) require a valid
  context, whereas [structured chunks](messages/telemetry/structured.md#snapshot-chunks)
  have no context field. Assign an interoperable structured selector context
  and descriptor validation rule before claiming cross-node structured requests
  or subscriptions work. Do not invent a context code.
  When assigning that context, also define the delivery event: local
  subscriptions describe per-frame value/status delivery, while a structured
  value exists only after all chunks commit. Decide whether subscribers
  receive complete snapshots or separate chunk events, without exposing an
  incomplete snapshot as current state.
- **Absent request-policy fields:** [Output descriptors](messages/inventory/model.md#resource-model)
  make `delivery_class` and `minimum_request_interval_ms` optional, but
  [telemetry control](messages/telemetry/control.md#snapshot-request) requires
  source scheduling according to both. Define the meaning of absence for each
  field and its interaction with rate leases; permission to ignore a request is
  not a default request policy.

- **Unique manifest identities:** [Resource IDs](messages/inventory/model.md#resource-model)
  must not be reused for different resources, while output records bind a
  node-local `publisher_id`; there is no explicit duplicate-record rule.
  Define uniqueness/rejection for resource IDs, publisher IDs across a node's
  manifest, and parameter IDs within their resource. Two descriptors for one
  publisher with different context or unit must not make telemetry validation
  depend on record traversal order.
- **Property TLV validation:** [Top-level framing](messages/inventory/envelope.md#top-level-records)
  and [relation endpoints](messages/inventory/model.md#resource-model) have
  validation rules, but resource/output/property nested TLVs need assigned
  tags, required/optional presence, ordering, unknown-tag and duplicate-tag
  behavior. In particular, duplicate `gas_species` or shape properties must
  not yield different output descriptors in different decoders.
- **Manifest chunk index relative to declared length:** The
  [wire ceiling](messages/inventory/transport.md#manifest-transfer-start-and-chunks)
  permits chunk indexes based on 65,535 bytes, while the manifest header
  supplies a possibly smaller `total_length` and completion requires exactly
  `ceil(total_length / D)` chunks. Define whether/how chunks at indexes beyond
  that count are rejected, including chunks buffered before the 24-byte
  header was available; otherwise two receivers can retain or ignore extra
  data differently under the same start context.
- **Top-level reserved/private record admission:** The
  [envelope](messages/inventory/envelope.md#top-level-records) permits skipping
  unknown kinds but marks `0x05–0x7F` reserved and `0x80–0xFF` private. Define
  receiver behavior for a reserved kind versus a deployment-private kind
  without treating either as an assigned interoperable resource.

## Future protocol surfaces referenced by the specified boundary

- **Explicit session reset:** [Discovery lifecycle](discovery/lifecycle.md) defines
  reboot and bus-off recovery, while [the assigned identifier map](profile.md#standard-identifier-classes)
  excludes a session-reset message. Define its identifier, physical forms,
  payload, session identifier/generation, stale-frame invalidation, and who may
  invoke it (authenticated or physically authorized) before enabling an explicit
  remote reset. Existing discovery recovery is not that operation.
- **Safety heartbeat and watchdog:** [The safety identifier class](profile.md#standard-identifier-classes)
  has no assigned payload. Define heartbeat identifier, payload, cadence,
  receive timeout, critical-node registry and the Safety Watchdog's required
  fail-safe action before treating bus presence as a safety guarantee.
- **Configuration operations:** [Parameter records](messages/inventory/model.md#resource-model)
  describe an interface, not read/write messages. Define catalogue locator and
  transfer, parameter reads/writes and synchronization, authorization,
  dive-state source and surface-only mutation enforcement before configuration
  can be changed over Rebus.
- **Firmware update:** [The manifest boundary](messages/inventory/README.md#scope)
  explicitly does not prove firmware integrity. Define target selection, image
  transport, complete-image cryptographic validation, authorization, update
  state machine, rollback and surface-only dispatch enforcement before using
  Rebus for firmware distribution.
- **Operational control:** [The reserved identifier map](profile.md#standard-identifier-classes)
  provides no operational-control payload. Define assigned identifiers and
  layouts, eligible controllers, sensor-validity inputs, deterministic
  multi-controller consensus, actuator-command validation and controller-failure
  fail-safe behavior before any actuation depends on these messages.
- **Telemetry gateway and radio boundary:** The
  [telemetry scope](messages/telemetry/README.md#scope) only specifies Rebus
  delivery and local subscriptions. Define gateway forwarding, radio
  authorization and the boundary with surface-companion communication before
  relying on off-bus delivery; no gateway frame is assigned here.

## Future extension policy; no v0.1 default

- **Protocol-version negotiation:** [Profile selection](profile.md#commissioned-physical-profiles)
  fixes v0.1 and rejects wrong-profile frames. Define version identifiers,
  compatibility and negotiation/failure policy for any future version; receiving
  different traffic must not silently select a version or physical profile.
- **Reliability beyond assigned traffic:** [Claims](discovery/lifecycle.md) and
  [telemetry requests](messages/telemetry/control.md) have their own rules.
  Define application acknowledgements, retransmission, timeouts and bus-error
  policy for future operational control or other traffic; do not extrapolate
  the claim one-shot or telemetry current-state-request behavior.
- **Future message discrimination and reserved fields:**
  [Assigned identifiers](profile.md#standard-identifier-classes) and
  [wire encoding](encoding.md#declared-layout) cover current payloads. Assign a
  message-type discriminator for any future shared identifier and define its
  reserved-bit handling before adding a payload; current message-specific
  reserved-field validation remains authoritative.
- **Future malformed-frame response:** [The physical gate](profile.md#commissioned-physical-profiles)
  requires discard without a protocol response. Any future diagnostic or
  response policy beyond that rule needs an explicit message contract and must
  not retroactively turn rejected frames into responses.
- **Future traffic filters and semantic code handling:** Current
  [identifier rules](profile.md#standard-identifier-classes) and
  [telemetry registry](messages/telemetry/registries.md#contexts) already
  assign validation for their covered traffic. Future fields need sender and
  receiver filters, periods/timeouts, unknown-context and reserved-code rules,
  and context/unit mismatch behavior in their own owners; do not generalize
  from unrelated current message types.
