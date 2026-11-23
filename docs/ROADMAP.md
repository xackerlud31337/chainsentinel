# ROADMAP - how to build ChainSentinel, in order

Rule: each step ends with passing tests and something you can demo with `curl`.
Never start a step before the previous one is green. Write a learning note after each phase.

---

## Phase 0 - Environment (today)

- [ ] `python3.12 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
- [ ] `cp .env.example .env`; get a free RPC key (Alchemy/Infura) or keep the public node
- [ ] `git init && git add -A && git commit -m "Project skeleton"`
- [ ] `pre-commit install`
- [ ] Read: ethereum.org "Accounts", "Transactions", "Blocks", "JSON-RPC API" (about 1 hour)
- Learning note: `docs/learning-notes/ethereum-account-model.md`

## Phase 1 - Blockchain connectivity (Module 1) ~1 week

Goal: `GET /api/v1/blockchain/status` returns chain id + latest block from a real node, with tests.

1. **Pure functions first** (`services/blockchain/validation.py`, `units.py`)
   - `is_valid_address(s) -> bool`, `normalize_address(s) -> ChecksumAddress` (EIP-55),
     `is_valid_tx_hash(s) -> bool`, `wei_to_ether(int) -> Decimal`, `ether_to_wei(Decimal) -> int`
   - Tests in `tests/unit/test_validation.py`: lowercase, uppercase, mixed, wrong length,
     non-hex, bad checksum, `0x` prefix missing. Use `Decimal`, never `float` - write a test
     proving why (`0.1 + 0.2`).
   - Concept: why does EIP-55 exist? What attack does a checksum prevent?

2. **Settings** (`core/config.py`)
   - `class Settings(BaseSettings)` with `eth_rpc_url: HttpUrl`, `eth_expected_chain_id: int`,
     `rpc_timeout_seconds: int`, `app_env: Literal["development","test","production"]`.
   - `@lru_cache get_settings()`. Test that a missing `ETH_RPC_URL` raises at import of settings.
   - Concept: 12-factor config; why secrets never go in code.

3. **RPC client wrapper** (`services/blockchain/client.py`)
   - Before web3.py: do ONE raw request yourself with `httpx` to understand the shape:
     `{"jsonrpc":"2.0","id":1,"method":"eth_blockNumber","params":[]}`. Put it in
     `scripts/raw_rpc_demo.py`. Decode the hex result. Now you know what web3.py hides.
   - Then `class BlockchainClient` wrapping `AsyncWeb3(AsyncHTTPProvider(url))` with methods:
     `chain_id()`, `block_number()`, `get_balance(addr)`, `get_transaction(tx_hash)`,
     `get_receipt(tx_hash)`, `get_block(number)`, `get_code(addr)`, `is_contract(addr)`.
   - Translate provider exceptions into your own `RpcError`, `NotFoundError`, `RpcTimeout`.
   - Define a `Protocol` for the client so tests can pass a `FakeBlockchainClient`.
   - Concept: async/await - why one worker can serve many slow RPC calls at once.

4. **Schemas + routers + app** (`schemas/blockchain.py`, `api/v1/blockchain.py`, `main.py`)
   - Response models with explicit types (`block_number: int`, `balance_wei: int`,
     `balance_ether: Decimal` serialised as string, `is_contract: bool`).
   - Path params validated with a custom `Annotated[str, AfterValidator(normalize_address)]`.
   - `lifespan` creates one client and stores it on `app.state`; a dependency `get_client()` yields it.
   - Error handler mapping `NotFoundError -> 404`, `RpcError -> 502`, with safe messages
     (never echo the provider's raw error or URL to the user).
   - Concept: FastAPI dependency injection; why 502 and not 500.

5. **Logging** (`core/logging.py`)
   - structlog JSON output, request id middleware, log method + path + status + duration.
   - Test: an exception containing the RPC URL (which may contain an API key) is redacted.

6. **Tests**
   - `tests/conftest.py`: `settings` override fixture, `fake_client` fixture, `TestClient(app)`.
   - Unit: every endpoint against the fake client. Security: oversized path, SQL-ish garbage,
     unicode confusables in address.
   - Integration (marked): one real `eth_blockNumber` against `ETH_RPC_URL`.
   - Learning notes: `json-rpc.md`, `async-python.md`, `wei-and-decimal.md`

7. **Stretch:** `eth_getLogs` for one block + decode an ERC-20 `Transfer` event with its ABI.
   This is the seed of Module 4.

## Phase 2 - Persistence, wallet investigation, risk engine (Modules 2 & 5) ~2-3 weeks

1. **Transaction history problem.** Write `docs/decisions/0002-transaction-history-source.md`
   comparing: explorer API (Etherscan), indexed RPC (Alchemy `alchemy_getAssetTransfers`),
   own indexer (scan blocks, filter by address). Choose explorer API now, note the own-indexer path.
   Implement `services/wallet_analysis/history.py` behind a `HistorySource` Protocol.
2. **Database.** `docker compose up -d`, `database/session.py`, first models:
   `Address`, `Transaction` (cache), `Analysis`, `Finding`. `alembic init`, first migration.
   Concept: why migrations instead of `create_all`; least-privilege DB user.
3. **Heuristics as pure functions** over `list[Transaction]`:
   `tx_frequency`, `top_counterparties`, `concentration_ratio` (Gini / top-N share),
   `activity_bursts` (rolling window), `known_bad_interactions` (local, documented list).
   Each returns `Finding | None`. Unit test every one with synthetic data, including the
   false-positive cases (an exchange hot wallet is high-frequency and NOT malicious).
4. **Risk engine.** `risk_engine/scoring.py`: `score(findings, weights) -> RiskAssessment`
   with per-finding contribution, severity, confidence, and `limitations` list.
   Weights come from a YAML/TOML file so they are reviewable.
5. **Endpoint** `POST /api/v1/analysis/wallet` orchestrating 1-4, storing the result.
6. **API security.** API-key dependency, per-key rate limit, request size limit, analysis timeout.

## Phase 3 - Contract scanner + approvals (Modules 3 & 4) ~3 weeks

1. Local chain: Anvil (Foundry). Deploy intentionally vulnerable contracts
   (reentrancy, missing access control, unprotected delegatecall) into `tests/fixtures/contracts/`.
2. Bytecode analysis: function selectors via 4-byte scan, proxy detection (EIP-1967 slots,
   `delegatecall` opcode), `owner()` / `pause()` / `mint()` selectors present?
3. Verified source retrieval + Slither in a resource-limited Docker container (`--network none`,
   memory and CPU caps, timeout). Treat source as hostile.
4. Finding taxonomy: `VERIFIED_VULNERABILITY` vs `STATIC_ANALYSIS_WARNING` vs `HEURISTIC`.
5. Approvals: `allowance()` reads, `Approval` event discovery via `eth_getLogs` in block ranges,
   unlimited-allowance detection (`2**256-1`, `> total_supply`).

## Phase 4 - Relationship graph (Module 6) ~1-2 weeks

NetworkX graph built from cached transactions. Hard caps on depth and node count from settings.
Centrality, shortest paths, star / fan-out patterns. JSON export (node-link format).

## Phase 5 - Monitoring (Module 7) ~2-3 weeks

Polling worker (`workers/poller.py`): track `last_processed_block`, wait N confirmations
before treating a block as final (reorg handling), idempotent alert keys
`(rule, tx_hash, log_index)`, retry with backoff on RPC failure. Then WebSockets. Then Celery
if and only if a single process is not enough - write the ADR.

## Phase 6 - Hardening & polish

Dockerfile (non-root, read-only FS), `pip-audit` in CI, GitHub Actions (lint, type, test),
OpenAPI docs review, threat model document, README demo GIF.
