# FilingCheck developer commands. Run these from Git Bash on Windows or any shell on Linux/macOS.

.PHONY: setup lint format test test-integration db-up db-down db-reset ingest validate-questions eval-smoke eval run

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

test-integration:  # needs the database from `make db-up`
	uv run pytest -m integration

db-up:
	docker compose up -d --wait db

db-down:
	docker compose down

db-reset:
	docker compose down -v
	docker compose up -d --wait db
	uv run python -m filingcheck.db migrate

# The filings are pinned in data/manifest.json, and re-runs reuse them. The manifest is re-pinned
# once, in early November 2026, to add Apple's FY2026 10-K:
#   uv run python -m filingcheck.ingest filings --reselect
# and then frozen for the evaluation.
ingest:
	uv run python -m filingcheck.ingest companies
	uv run python -m filingcheck.ingest filings
	uv run python -m filingcheck.ingest sections
	uv run python -m filingcheck.ingest chunks
	uv run python -m filingcheck.ingest load

validate-questions:
	@echo "not built yet (week 1, day 6)"

eval-smoke:
	@echo "not built yet (week 3)"

eval:
	@echo "not built yet (week 5)"

run:
	@echo "not built yet (week 2)"
