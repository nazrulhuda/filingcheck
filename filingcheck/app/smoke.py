"""`make smoke-live URL=https://...`: the deployed API answers on every public path.

Calls /health, /companies, /examples and one /ask (one model call, counted against the daily
cap), and fails on any status other than 200, an empty list, or an answer with no citations.
"""

import argparse
import sys
from collections.abc import Callable
from typing import Any

import httpx

from filingcheck.console import use_utf8_output

# Answered with citations in every run so far; a question the baseline declines would fail.
QUESTION = {
    "question": "What does Netflix say about intellectual-property claims?",
    "ticker": "NFLX",
}
# The first request after Neon has suspended waits for it to wake, and an answer for the model.
TIMEOUT_SECONDS = 60.0

Check = tuple[bool, str]


def make_client() -> httpx.Client:
    """The HTTP client the smoke test uses (replaced in tests)."""
    return httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=False)


def _check(
    client: httpx.Client,
    method: str,
    url: str,
    path: str,
    describe: Callable[[Any], str | None],
    **kwargs: Any,
) -> Check:
    """One request; `describe` returns a failure reason for the JSON body, or None if fine."""
    label = f"{method} {path}"
    try:
        response = client.request(method, url + path, **kwargs)
    except httpx.HTTPError as exc:
        return False, f"FAIL {label}: {type(exc).__name__}: {exc}"
    if response.status_code != 200:
        return False, f"FAIL {label}: HTTP {response.status_code}"
    try:
        body = response.json()
    except ValueError:
        return False, f"FAIL {label}: the reply is not JSON"
    problem = describe(body)
    if problem is not None:
        return False, f"FAIL {label}: {problem}"
    return True, f"ok {label}: {summary(path, body)}"


def summary(path: str, body: Any) -> str:
    """A short description of a good reply."""
    if path == "/health":
        return f"status {body.get('status')}, model {body.get('model')}"
    if path == "/ask":
        count = len(body.get("citations") or [])
        return (
            f"{count} citation{'s' if count != 1 else ''}, model {body.get('model_used')}, "
            f"cached {body.get('cached')}, degraded {body.get('degraded')}"
        )
    return f"{len(body)} entries"


def non_empty(body: Any) -> str | None:
    """An empty list means the service started before the database was loaded."""
    return None if isinstance(body, list) and body else "empty list"


def cites(body: Any) -> str | None:
    """An answer must cite at least one passage."""
    return (
        None if isinstance(body, dict) and body.get("citations") else "the answer has no citations"
    )


def run_checks(base_url: str, client: httpx.Client) -> list[Check]:
    """Every check, in order; a failure does not stop the rest."""
    url = base_url.rstrip("/")
    return [
        _check(client, "GET", url, "/health", lambda b: None),
        _check(client, "GET", url, "/companies", non_empty),
        _check(client, "GET", url, "/examples", non_empty),
        _check(client, "POST", url, "/ask", cites, json=QUESTION),
    ]


def main(argv: list[str] | None = None) -> int:
    """Run the checks against URL; 0 if all pass, 1 if any fails, 2 for a bad URL."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.app.smoke")
    parser.add_argument("url", help="the deployed API, for example https://<service>.onrender.com")
    args = parser.parse_args(argv)
    if not args.url.startswith("https://"):
        print("give the API's https:// address: make smoke-live URL=https://...")
        return 2
    with make_client() as client:
        results = run_checks(args.url, client)
    for _, line in results:
        print(line)
    failed = sum(not ok for ok, _ in results)
    print("smoke test passed" if not failed else f"smoke test FAILED: {failed} of {len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
