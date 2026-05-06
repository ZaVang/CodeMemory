---
id: user/facts/microservices-overhead
type: atom
summary: Microservices introduce significant operational overhead that must be accounted
  for in planning
tags:
- architecture
- microservices
- operations
intensity: 8
status: active
version: 1
maturity: proven
created: 2025-06-10
imports:
  related:
  - user/preferences/simplicity-first
summary_hash: a6b9b79
---


# Microservices Overhead

Adopting microservices trades code complexity for operational complexity. Key overhead areas include:

## Deployment Infrastructure
Each service needs its own CI/CD pipeline, container image, and deployment configuration. With 12 services, this means maintaining 12 pipelines rather than 1.

## Observability
Distributed tracing becomes mandatory. A single user request may touch 4-6 services. Without tools like OpenTelemetry or Jaeger, debugging is nearly impossible.

## Network Costs
Inter-service calls add latency. Serialization/deserialization of messages consumes CPU. Service meshes (e.g., Istio) add another layer of complexity.

## Data Consistency
Distributed transactions are not feasible at scale. Teams must design for eventual consistency and compensating transactions (sagas).

## Recommendation
The decision to go microservices (user/decisions/adopt-microservices) should be periodically re-evaluated. If the team size shrinks or the product scope narrows, consider merging services back into a modular monolith.
