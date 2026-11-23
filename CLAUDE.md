# ChainSentinel - working agreement

Learning project. The owner is a CS student who wants to write the code themselves.

- Explain the purpose and the security reasoning of a component before adding it.
- Prefer guiding (what to write, why, what to test) over writing large amounts of code.
- Follow `docs/ROADMAP.md` phases in order; do not introduce later-phase tech early.
- Layering: api -> services -> repositories/blockchain client. Never upwards.
- All blockchain data is untrusted input. Validate at the boundary, handle defensively inside.
- Never request, store or log private keys / seed phrases. Read-only RPC only.
- Every finding has severity, confidence, evidence and limitations. Heuristic != proof.
- Tests: `pytest` (unit, offline). Integration tests are marked and opt-in.
- Tooling: ruff (lint+format), mypy strict, pre-commit, pip-audit.
