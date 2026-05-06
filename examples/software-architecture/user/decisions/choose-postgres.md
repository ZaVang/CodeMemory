---
id: user/decisions/choose-postgres
type: atom
summary: PostgreSQL selected as the primary relational database
tags:
- database
- infrastructure
intensity: 7
status: active
version: 1
maturity: proven
schema: schemas/architectural-decision
created: 2025-06-01
imports:
  recommended:
  - user/decisions/event-sourcing
summary_hash: bbed85a
---


# Context
We needed a reliable, well-understood relational database for the majority of our services. The team already had significant PostgreSQL experience.

# Decision
PostgreSQL is the default choice for all services that need relational persistence. Service-specific read replicas are provisioned for read-heavy workloads.

# Consequences
- **Positive**: Excellent ecosystem, strong documentation, rich feature set (JSONB, full-text search, window functions). Team already proficient.
- **Negative**: Event sourcing append-only workloads benefit from PostgreSQL tuning (see user/decisions/event-sourcing). Horizontal scaling requires sharding or read replicas, which adds complexity.
