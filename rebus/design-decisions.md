SPDX-License-Identifier: CC-BY-4.0
Copyright (c) 2026 openCCR contributors

# Rebus design decisions

This document records implementation and product choices that support the
normative Rebus specifications without adding their rationale to wire-format
documents.

## Persist node assignment across reboot

**Decision:** A node must persist its assigned node claim locally during a
formal network power-on/power-off session. At minimum, persistent state stores
its stable `hardware_uuid`, assigned node ID, discovery session identifier, and
whether the assignment was confirmed.

A reboot is not a new address-allocation event. When the node returns during
the same session, it first attempts to reclaim the persisted UUID-to-node-ID
assignment. It must not silently replace that assignment with a new free
preferred ID. It sends no addressed traffic until reclaim is confirmed.

Peers retain a tombstone for the confirmed UUID-to-node-ID association. A
reclaim announcement containing the same UUID, node ID, and session identifier
restores the assignment without running a new UUID election. A different claim
from the rebooted node is treated as an unadmitted claim until the old
assignment is explicitly released or a new discovery session begins.

### Why local persistence is primary

The network can remember that an address belonged to a UUID, but it cannot
reliably tell a rebooted node which address to use without another control
exchange, a query/reply protocol, and protection against stale responses. The
local record is cheaper, deterministic, and available before the node sends
anything. It also prevents a reboot from creating unnecessary address churn.

### Recovery when persistent state is unavailable

Loss or corruption of the local record is an exceptional recovery case. The
node must remain unadmitted and must not claim a new free address during the
active session. A future reclaim/query mechanism may recover the old mapping;
until then, recovery requires an explicit network reset or authorized service
operation. Implementations must not infer that a free address is safe merely
because no current claim is visible.

### Formal power cycle

A formal power-off ends the discovery session only when the deployment's
session-reset procedure says so. A full network power-on starts a new session,
clears old tombstones, and permits fresh claims. A single-node reboot does not
clear the session or its assignment.

## Consequences

- Node identity and address stability depend on non-volatile local storage.
- A permanently failed node can reserve its address until an explicit reset.
- Reboot recovery is fast and does not require a coordinator.
- Reclaim, session reset, and stale-session handling need control-frame
  definitions in the wire profile.
