---
id: user/decisions/use-graphql
type: atom
summary: Selected GraphQL as the primary API layer between frontend and backend services
tags:
- api
- graphql
- frontend
status: active
version: 1
maturity: verified
schema: schemas/architectural-decision
created: 2025-07-01
imports:
  required:
  - user/facts/graphql-n-plus-one
  recommended:
  - user/decisions/adopt-microservices
summary_hash: 8986cb4
---


# Context
With multiple backend microservices, the frontend team faced the challenge of aggregating data from disparate sources. REST endpoints were proliferating, and over-fetching or under-fetching data was common.

# Decision
We introduced a GraphQL gateway that sits between the frontend and backend services. This gateway federates queries across services and provides a single, typed API surface.

# Consequences
- **Positive**: Frontend teams can fetch exactly the data they need in a single request. Strong typing via the GraphQL schema reduces integration errors.
- **Negative**: The N+1 query problem (see user/facts/graphql-n-plus-one) requires careful use of DataLoader. The gateway adds a single point of failure and an additional hop. Caching is more nuanced than REST.
