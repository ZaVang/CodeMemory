---
id: user/decisions/adopt-microservices
type: atom
summary: Decided to adopt a microservices architecture for the core platform
tags:
- architecture
- microservices
intensity: 9
status: active
version: 1
maturity: proven
schema: schemas/architectural-decision
created: 2025-06-15
imports:
  recommended:
  - user/facts/microservices-overhead
  - user/observations/team-distributed
  related:
  - user/preferences/simplicity-first
summary_hash: 7ff61a1
---


# Context
The product was growing beyond a single team's capacity. Multiple teams needed to ship independently without blocking each other. The existing monolith had become a bottleneck for deployment velocity.

# Decision
We will decompose the platform into ~12 independently deployable services, each owned by a single team. Services communicate via asynchronous messaging where possible, and synchronous HTTP/REST where latency requirements demand it.

# Consequences
- **Positive**: Teams can deploy independently. Technology choices can vary per service. Scaling is localized to hot services.
- **Negative**: Increased operational complexity (see user/facts/microservices-overhead). Distributed debugging is harder. Network latency and partial failure modes must be handled explicitly.
