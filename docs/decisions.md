# Decisions

One row per real choice. Newest at the bottom.

| Date | Decision | Alternatives | Why | Evidence |
|---|---|---|---|---|
| 2026-10-25 | `uv` manages Python, dependencies and the lock file | pip + venv; Poetry; PDM | One tool installs Python 3.12, resolves and locks dependencies, and runs commands. Fast in CI. | `uv.lock`, `make setup` |
| 2026-10-25 | `ruff` for lint and format, `mypy` in strict mode for types | flake8 + black + isort; pyright | ruff replaces three tools and runs in well under a second. Strict mypy catches wrong types in the checks before the tests do. | `make lint`, `pyproject.toml` |
| 2026-10-25 | One Postgres with pgvector for text, vectors, keyword search, XBRL facts and eval results | Postgres plus a separate vector store (Chroma, Pinecone); SQLite + FAISS | One database keeps joins, transactions and backups simple and fits Neon's free 1 GB plan. pgvector covers vector search; `tsvector` covers keyword search. | `docker-compose.yml` |
| 2026-10-25 | `edgartools` for EDGAR access (filing lists, documents, 10-K Items) | `sec-edgar-downloader`; hand-written parsing of the EDGAR indexes | It already handles filing indexes and Item extraction. Our own rate-limited, cached client stays in front of every raw download. Version pinned on day 3. | `filingcheck/ingest/filings.py` (day 3) |
| 2026-10-25 | The SEC contact email lives only in `.env` (`SEC_CONTACT_EMAIL`), never in a committed file | Writing the email into the code or a committed config file | The repo is public. The SEC needs the email in the User-Agent header at request time, not in the source. | `.env.example` |
