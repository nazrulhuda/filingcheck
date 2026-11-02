# FilingCheck developer commands. Run these from Git Bash on Windows or any shell on Linux/macOS.
# Tools run as `python -m <tool>`: Windows can block the small .exe launchers that uv creates.
# Python's UTF-8 mode makes Windows read, write and print text as UTF-8, the same as Linux CI.
export PYTHONUTF8 = 1

.PHONY: setup lint format test test-integration verify-data verify-facts snapshot embed embed-dry-run retrieval-eval ask baseline-examples db-up db-down db-reset ingest validate-questions eval-smoke eval run

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

# The filings are pinned in data/manifest.json, and re-runs reuse them; SEC downloads are cached
# forever. The manifest is re-pinned once, in November 2026, to add Apple's FY2026 10-K:
#   uv run python -m filingcheck.ingest filings --reselect     (downloads the filing lists again)
#   uv run python -m filingcheck.ingest companyfacts --refresh (downloads the XBRL facts again)
#   then the rest of `make ingest` (sections, chunks, load, report) and `make snapshot`.
# The same PR updates tests/expected_manifest.json, data/section_snapshot.json and
# data/chunk_snapshot.json, and its description lists the sections that changed and why.
# After that the manifest stays frozen for the evaluation.
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

embed:  # embed every chunk without a vector (prints the plan and asks first; costs money)
	uv run python -m filingcheck.embeddings

# `make embed --dry-run` would be make's own dry run (print, don't run), so the plan has its own target.
embed-dry-run:  # print what `make embed` would restore, embed and cost; no API call, no writes
	uv run python -m filingcheck.embeddings --dry-run

retrieval-eval:  # score vector, keyword and hybrid search; writes docs/retrieval_report.md
	uv run python -m filingcheck.eval.retrieval_report

# Calls the chat model (costs money). Batch mode: waits out rate limits and never falls back.
# LIVE=1 uses live mode: short waits, then the fallback models answer.
ask:  # answer one question with the plain-RAG baseline: make ask Q="..." [TICKER=WMT YEAR=2025] [LIVE=1] [MAX_TOKENS=700]
	uv run python -m filingcheck.answer "$(Q)" $(if $(TICKER),--ticker $(TICKER)) $(if $(YEAR),--year $(YEAR)) $(if $(LIVE),--live) $(if $(MAX_TOKENS),--max-tokens $(MAX_TOKENS))

baseline-examples:  # the 6 example questions, batch mode, no filters; writes docs/baseline_examples.md (costs money)
	uv run python -m filingcheck.answer.examples

snapshot:  # rewrite data/section_snapshot.json and data/chunk_snapshot.json after an intended change
	uv run python -m filingcheck.ingest.verify --write-snapshots

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
