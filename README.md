# ChainSentinel

Blockchain threat intelligence and security analysis platform for Ethereum.
Read-only. Never asks for private keys or seed phrases.

> Status: Phase 1 (blockchain connectivity) in progress. See `docs/ROADMAP.md`.

## What it does (target)

| Module | Capability | Endpoint |
|---|---|---|
| 1 Connectivity | Chain status, balances, transactions, receipts, blocks | `GET /api/v1/blockchain/status` ... |
| 2 Wallet investigation | Transaction-history heuristics, counterparties, findings | `POST /api/v1/analysis/wallet` |
| 3 Contract scanner | Privileges, proxies, Slither findings | `POST /api/v1/analysis/contract` |
| 4 Approval analyzer | ERC-20 allowance risk | `POST /api/v1/analysis/approvals` |
| 5 Risk engine | Explainable 0-100 score | (used by 2-4) |
| 6 Relationship graph | Address interaction graph | `GET /api/v1/graph/{address}` |
| 7 Monitoring | Watchlists, alerts | `POST /api/v1/monitoring/watchlist` |

Every finding carries a severity, a confidence, evidence, and explicit limitations.
A heuristic score is never presented as proof of malicious behaviour.

## Quick start

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env            # edit ETH_RPC_URL if you have a provider key
make db-up                      # Postgres (needed from Phase 2)
make dev                        # http://127.0.0.1:8000/docs
make test
```

## Layout

```
app/
  main.py          FastAPI app factory
  api/v1/          routers (HTTP in, HTTP out - no logic)
  core/            settings, logging, security
  schemas/         Pydantic request/response models
  models/          SQLAlchemy tables
  services/        business logic, one package per module
  repositories/    database queries
  database/        engine + session
  workers/         background jobs
tests/             unit / integration / security
docs/              roadmap, architecture, ADRs, learning notes
alembic/           migrations
```

`docs/architecture.md` explains why each layer exists.
