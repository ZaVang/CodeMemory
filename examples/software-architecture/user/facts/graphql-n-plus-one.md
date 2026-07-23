---
id: user/facts/graphql-n-plus-one
type: atom
summary: GraphQL resolvers are susceptible to the N+1 query problem, requiring explicit
  mitigation with DataLoader or similar batching strategies
tags:
- graphql
- performance
- backend
status: active
version: 1
maturity: proven
created: 2025-06-20
summary_hash: d79afec
---


# GraphQL N+1 Problem

## The Problem
In a naive GraphQL implementation, a query like:

```graphql
{
  orders { id customer { name } }
}
```

Causes one query for `orders` (1 query), then for each order, one query for its `customer` (N queries). Total: N+1 queries.

## Mitigations
- **DataLoader**: Facebook's batching library. Collects keys during a single event loop tick, then issues one batch query. Essential for any production GraphQL server.
- **Look-ahead optimization**: Parse the query AST before execution to detect nested relationships and pre-fetch related data.
- **Persisted queries**: Pre-define allowed queries, enabling server-side optimization and caching.
- **Query complexity analysis**: Reject queries that exceed a complexity budget.

## Interaction with Microservices
When the GraphQL gateway federates across microservices (see user/decisions/use-graphql), the N+1 problem compounds: a single field resolution may trigger a network call to a downstream service. DataLoader must be used at the gateway level to batch these calls.
