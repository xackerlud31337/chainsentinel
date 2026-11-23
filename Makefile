.PHONY: venv install dev test lint typecheck audit db-up db-down

venv:
	python3.12 -m venv .venv && echo "run: source .venv/bin/activate"

install:
	pip install --upgrade pip && pip install -e ".[dev]"

dev:
	uvicorn app.main:app --reload --port 8000

test:
	pytest

test-all:
	pytest -m ""

lint:
	ruff check . && ruff format --check .

fmt:
	ruff check --fix . && ruff format .

typecheck:
	mypy app

audit:
	pip-audit

db-up:
	docker compose up -d postgres

db-down:
	docker compose down
