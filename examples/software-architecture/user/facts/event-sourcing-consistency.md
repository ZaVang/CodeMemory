---
id: user/facts/event-sourcing-consistency
type: atom
summary: Event sourcing systems are eventually consistent by nature; read models lag
  behind the event log
tags:
- event-sourcing
- consistency
- data
intensity: 7
status: active
version: 1
maturity: proven
created: 2025-07-15
summary_hash: 85cd8e9
---


# Eventual Consistency in Event Sourcing

## The Core Trade-off
Event sourcing decouples writes (events) from reads (projections). The write is a simple append to the event log. The read model is rebuilt asynchronously. This means:

- A write may succeed but the corresponding read model update is not yet visible.
- The duration of this inconsistency depends on projection rebuild time.

## Real-World Impact
For an order processing system (see user/decisions/event-sourcing):

- After placing an order, the customer might not see it in their order history for 200-500ms.
- Payment confirmation callbacks must tolerate this window — they cannot assume the order projection is up to date.

## Mitigation Strategies
- **Read-your-writes**: Return the event log position to the client, use it as a consistency token on subsequent reads.
- **Optimistic UI**: Show the expected state immediately, reconcile when the projection catches up.
- **Strongly consistent reads for critical paths**: Bypass projections for payment confirmation; read directly from the event log.
