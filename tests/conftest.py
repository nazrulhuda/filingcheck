"""Shared test setup.

The SEC client refuses to import without a contact email, so tests set a placeholder
before any `filingcheck.ingest` module is imported. Tests never reach the network.
"""

import os

os.environ.setdefault("SEC_CONTACT_EMAIL", "tests@example.com")
