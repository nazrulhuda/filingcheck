# FilingCheck developer commands. Run these from Git Bash on Windows or any shell on Linux/macOS.

.PHONY: setup lint format test db-up db-down db-reset ingest validate-questions eval-smoke eval run

setup:
	uv python install 3.12
	uv sync
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run pytest -m "not integration and not slow" --cov=filingcheck --cov-report=term-missing --cov-report=xml --cov-report=html

db-up:
	docker compose up -d --wait db

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d --wait db

ingest:
	@echo "not built yet (week 1, day 2 onward)"

validate-questions:
	@echo "not built yet (week 1, day 6)"

eval-smoke:
	@echo "not built yet (week 3)"

eval:
	@echo "not built yet (week 5)"

run:
	@echo "not built yet (week 2)"
