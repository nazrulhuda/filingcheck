# The API: python:3.12-slim, dependencies from uv.lock, runs as a non-root user.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PORT=8000

WORKDIR /app
RUN useradd --create-home --uid 10001 app

# Dependencies first, so code changes reuse the cached layer. The app needs neither the dev
# tools nor the ingest group (edgartools, pyarrow).
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-group ingest --no-install-project
COPY filingcheck ./filingcheck
# The checks read the company list and the manifest; the rest of data/ stays out.
COPY data/companies.yaml data/manifest.json ./data/
RUN uv sync --locked --no-dev --no-group ingest

USER app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn filingcheck.app.main:app --host 0.0.0.0 --port ${PORT}"]
