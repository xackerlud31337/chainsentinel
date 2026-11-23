# Architecture

## The layering rule

```
HTTP request
   │
   ▼
api/v1/*.py        parse + validate (Pydantic)  → call a service → serialise response
   │
   ▼
services/*         pure business logic. Knows nothing about HTTP or SQL.
   │          ╲
   ▼           ╲
repositories/*   services/blockchain/client.py
(SQLAlchemy)     (web3 / JSON-RPC)
```

Dependencies point **downwards only**. A service never imports from `api/`.
A repository never imports from `services/`. `core/` is imported by all, imports none.

Why this matters for *this* project specifically:

- **Testability.** Detection heuristics (Module 2, 5) are the intellectually valuable part.
  They must be testable with a hand-built list of transactions, no network, in milliseconds.
  That is only possible if they are plain functions that receive data, not functions that fetch data.
- **Untrusted input everywhere.** Blockchain data (contract names, token symbols, metadata, source code)
  is attacker-controlled. Validation at the API boundary (Pydantic) plus defensive handling in
  services gives two independent layers.
- **Swap-ability.** RPC providers go down and rate-limit. Keeping all RPC access behind
  `services/blockchain/client.py` means retries, caching and provider failover live in one file.

## Component purposes

| Path | Purpose | Introduced |
|---|---|---|
| `app/main.py` | Build the app, mount routers, manage lifespan (open/close RPC client) | Phase 1 |
| `app/core/config.py` | `Settings` from env vars. Fail fast on bad config. | Phase 1 |
| `app/core/logging.py` | Structured logs; redaction of secrets | Phase 1 |
| `app/core/security.py` | API-key auth dependency, rate limiting | Phase 2 |
| `app/schemas/` | API contract. Changing these = changing the public API. | Phase 1 |
| `app/services/blockchain/` | Validation, units, RPC wrapper, ABI decoding | Phase 1 |
| `app/models/`, `app/database/`, `app/repositories/`, `alembic/` | Persistence for cached tx history, findings, watchlists, alerts | Phase 2 |
| `app/services/wallet_analysis/` | Heuristics over transaction lists | Phase 2 |
| `app/services/risk_engine/` | Weighted, explainable scoring | Phase 2 |
| `app/services/contract_analysis/` | Bytecode + source + Slither | Phase 3 |
| `app/services/approval_analysis/` | ERC-20 allowances and Approval logs | Phase 3 |
| `app/services/graph/` | NetworkX graph with limits | Phase 4 |
| `app/services/monitoring/`, `app/workers/` | Polling loop, alert rules, idempotency | Phase 5 |

## Schemas vs models

`schemas/` (Pydantic) describe what goes over the wire. `models/` (SQLAlchemy) describe what is in
the database. They often look similar and the temptation is to merge them. Do not: the DB will grow
internal columns (created_at, raw payloads, indexes) that must never leak into API responses, and
the API will grow computed fields that are never stored.

## Things deliberately NOT here yet

Redis, Celery, WebSockets, Neo4j, React. Each is added only when a concrete problem demands it,
and the ADR in `docs/decisions/` records that problem.
