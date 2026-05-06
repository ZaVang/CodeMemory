---
id: user/beliefs/correctness-over-speed
type: atom
summary: We believe that correctness is more valuable than development speed in the
  core domain; bugs in orders and payments are far more costly than a delayed release
tags:
- engineering-culture
- quality
- values
intensity: 9
status: active
version: 1
maturity: proven
created: 2025-05-01
summary_hash: 7d8cdec
---


# Correctness Over Speed

## Core Belief
In the core business domain (orders, payments, user accounts), a bug is not just a bug — it is a breach of trust. Customers do not forgive incorrect charges or lost orders. We prioritize correctness over velocity in these domains.

## What This Means in Practice
- **Code review is mandatory** for all changes touching the core domain. No exceptions for "trivial fixes."
- **Tests are required at multiple levels**: unit tests for business logic, integration tests for service boundaries, end-to-end tests for critical user journeys.
- **Property-based testing** for financial calculations (e.g., "the sum of all order line items, after discounts and tax, must equal the charged amount").
- **Deploy with confidence, not speed**: Canary deployments, feature flags, and gradual rollouts are standard practice.

## What This Does NOT Mean
- This belief does not apply uniformly. Experimental features, internal tools, and non-critical paths can and should move fast.
- It does not mean analysis paralysis. We decide, document, and move forward — but we verify our work rigorously.

## Relationship to Other Decisions
The adoption of event sourcing (user/decisions/event-sourcing) is partially motivated by this belief: an append-only event log provides a complete audit trail, which is invaluable for financial correctness verification.
