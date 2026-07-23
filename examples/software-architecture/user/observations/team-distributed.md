---
id: user/observations/team-distributed
type: atom
summary: The engineering team is distributed across three time zones (UTC-8, UTC+1,
  UTC+8), making asynchronous communication the default
tags:
- team
- communication
- process
status: active
version: 1
maturity: verified
created: 2025-05-15
summary_hash: 1173d89
---


# Distributed Team Observation

## Current State
As of mid-2025, the engineering team of 18 is split across:
- San Francisco (UTC-8): 8 engineers
- London (UTC+1): 5 engineers  
- Singapore (UTC+8): 5 engineers

Synchronous meeting windows are limited to approximately 2 hours per day (UTC 16:00-18:00).

## Implications
- **Async-first culture**: Design documents, RFCs, and written decision records are essential. Verbal decisions that are not written down are effectively lost.
- **Microservices alignment**: Independent deployability (see user/decisions/adopt-microservices) is more valuable for a distributed team because it eliminates deployment coordination across time zones.
- **On-call rotation**: Follow-the-sun on-call is feasible but requires well-documented runbooks and consistent observability tooling.

## Risks
- Knowledge silos can form within time zone clusters. We mitigate through:
  - Cross-time-zone pair programming sessions (scheduled during overlap windows).
  - All-hands demo every two weeks with recordings for those who cannot attend live.
  - Architecture decisions are documented in this very memory system.
