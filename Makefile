# FilingCheck developer commands. Run these from Git Bash on Windows or any shell on Linux/macOS.
# Tools run as `python -m <tool>`: Windows can block the small .exe launchers that uv creates.

.PHONY: setup lint format test test-integration verify-data verify-facts db-up db-down db-reset ingest validate-questions eval-smoke eval run

setup:
	uv python install 3.12
	uv sync
	uv run python -m pre_commit install

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run python -m mypy

format:
	uv run ruff check --fix .
	uv run ruff format .

test:
	uv run python -m pytest -m "not integration and not slow" --cov=filingcheck --cov-report=term-missing --cov-report=xml --cov-report=html

test-integration:  # needs the database from `make db-up`
	uv run python -m pytest -m integration

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
	uv run python -m filingcheck.ingest companyfacts
	uv run python -m filingcheck.ingest sections
	uv run python -m filingcheck.ingest chunks
	uv run python -m filingcheck.ingest load
	uv run python -m filingcheck.ingest report

verify-data:  # independent check of the ingest outputs; writes docs/spot_check.md, section_bounds.md, table_sample.md
	uv run python -m filingcheck.ingest.verify

verify-facts:  # which candidate XBRL tags have 10-K facts per filing; writes docs/facts_coverage.md
	uv run python -m filingcheck.ingest.facts_coverage

validate-questions:
	uv run python -m filingcheck.eval.questions validate

eval-smoke:
	@echo "not built yet (week 3)"

eval:
	@echo "not built yet (week 5)"

run:
	@echo "not built yet (week 2)"
