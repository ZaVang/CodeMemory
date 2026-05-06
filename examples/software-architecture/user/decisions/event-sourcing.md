---
id: user/decisions/event-sourcing
type: atom
summary: Adopted event sourcing for the core domain (orders and payments)
tags:
- architecture
- event-sourcing
- data
intensity: 8
status: active
version: 1
maturity: verified
schema: schemas/architectural-decision
created: 2025-08-01
imports:
  required:
  - user/facts/event-sourcing-consistency
  - user/decisions/adopt-microservices
summary_hash: f2fc23e
---


# Context
The core domain (order processing and payments) required a complete, auditable history of all state transitions. CRUD-style persistence was losing critical business information about *why* and *when* state changed.

# Decision
We adopted event sourcing for order and payment aggregates. State is derived from an append-only event log. Projections are rebuilt as needed for query optimization.

# Consequences
- **Positive**: Full audit trail of every business event. Temporal queries ("what was the state at time T?") become trivial. Events serve as a natural integration mechanism between services.
- **Negative**: Eventual consistency (see user/facts/event-sourcing-consistency) means data may be briefly stale. Schema evolution of events requires versioning strategy. The learning curve for the team is significant.
