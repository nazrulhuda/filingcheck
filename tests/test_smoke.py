"""Smoke test: proves the package imports and the test pipeline runs in CI."""

import filingcheck


def test_package_version() -> None:
    assert filingcheck.__version__ == "0.1.0"
