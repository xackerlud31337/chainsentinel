"""
Application settings loaded from environment variables via pydantic-settings.

Why: configuration (RPC URL, DB URL, API keys) must never be hardcoded. Reading it
once into a validated Settings object means a typo in .env fails loudly at startup
instead of silently at request time.

Implemented in Phase 1, step 2 of docs/ROADMAP.md.
"""
