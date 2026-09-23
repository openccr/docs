SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Subscription lifecycle
**COMMON**


Rebus v0.1 assigns no telemetry-subscribe or telemetry-unsubscribe CAN
identifier, payload, acknowledgement, or flow-control mechanism. A telemetry
subscription is receiver-local: it never changes a publisher's role
announcement, telemetry cadence, frame contents, or bus traffic. Local
subscriptions do not change source cadence, message contents, publisher roles,
or shared sequence state.

An active subscription selects exactly one current stream context:
`(source_node_id, publisher_id, context)` and is bound locally to the current
source UUID and [identity generation](../../discovery/identity.md) for that
source node ID. `source_node_id` MUST be in `0x01–0x7F`, and `context` MUST be
valid under the [telemetry registry](registries.md). A consumer that needs
several streams or contexts registers one subscription per exact selector.

## Subscribe process

1. Validate the source node-ID range and selected context.
2. Resolve the source node ID to its current source UUID and identity generation,
   then store the exact selector with both bindings. This creates no CAN frame
   and does not alter shared capability or sequence state.
3. Apply the selected [profile frame gate](../../profile.md), telemetry payload
   validation, and per-stream sequence processing before evaluating any
   subscription. The subscription does not select or infer a physical profile.
   For each accepted frame, deliver its value and status only to active
   selectors that exactly match its stream, context, source UUID, and current
   identity generation.

The receiver processes sequence state once per accepted stream, not once per
subscriber. A subscription begins with future accepted frames only; it neither
replays an earlier value nor makes a missing source publish.

## Unsubscribe process

1. Remove the exact local selector.
2. Stop deliveries for that selector immediately, without changing shared
   capability or sequence state.
3. Send no CAN frame and make no request to the source.

An active subscription remains in effect until it is removed or discovery
changes the UUID bound to its source node ID. A UUID remap removes the
subscription and its associated requester-bound state; the replacement node
must be subscribed explicitly. Address reuse therefore cannot inherit or
recreate the prior selector.
