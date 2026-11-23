"""
Thin wrapper around web3.py's AsyncWeb3.

Why wrap it: every other module depends on this one. A wrapper lets us
  - inject a fake client in unit tests
  - add retries / timeouts / error translation in one place
  - swap providers without touching callers

Phase 1, step 3.
"""
