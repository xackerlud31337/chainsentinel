"""
FastAPI application factory.

Responsibilities (and nothing more):
  - build the FastAPI instance
  - register routers from app/api/v1
  - wire startup/shutdown (lifespan) for shared resources such as the RPC client

Implemented in Phase 1, step 4 of docs/ROADMAP.md.
"""
