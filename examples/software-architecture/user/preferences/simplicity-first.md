---
id: user/preferences/simplicity-first
type: atom
summary: Prefer the simplest solution that meets requirements, deferring complexity
  until it is demonstrably necessary
tags:
- engineering-culture
- decision-making
intensity: 9
status: active
version: 1
maturity: proven
created: 2025-05-01
imports:
  related:
  - user/beliefs/correctness-over-speed
summary_hash: 4d5fe7c
---


# Simplicity First

## Principle
Complexity is a liability, not an asset. Every abstraction, every new technology, every architectural pattern has a carrying cost. We only pay that cost when the benefit clearly outweighs it.

## Decision Heuristic
When evaluating a technical choice, ask:
1. What is the simplest thing that could possibly work?
2. What concrete problem does the more complex solution solve?
3. Can we defer the complex solution to a later iteration without painting ourselves into a corner?

## Concrete Examples
- **Monolith before microservices**: Start with a well-structured modular monolith. Extract services only when team scaling or independent deployability becomes a bottleneck.
- **REST before GraphQL**: REST is simpler to implement, cache, and debug. Add GraphQL when frontend teams are demonstrably impaired by over-fetching.
- **Single database before CQRS**: Start with a single PostgreSQL instance. Add read replicas or event sourcing when read/write patterns diverge measurably.

## Counterpoint
Simplicity should not be confused with negligence. We must design extension points so that future complexity can be added surgically, not through a rewrite.
