"""The HTTP API served by uvicorn: `uvicorn filingcheck.app.main:app`."""

from filingcheck.app.api import create_app

app = create_app()
