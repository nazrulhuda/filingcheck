"""`make smoke-live URL=https://...`: the deployed API answers on every public path.

Calls /health, /companies, /examples, one /ask with the baseline and one with the agent (two
questions counted against the daily cap), and fails on any status other than 200, an empty
list, or an answer with no citations (the agent's: no tool call or no fact citation).
It also fails on an answer that is cached, degraded or from a model other than the primary:
each means a key or setting on the server is wrong, which a cited answer would otherwise hide.
"""

import argparse
import sys
from collections.abc import Callable
from typing import Any

import httpx

from filingcheck.console import use_utf8_output
from filingcheck.llm.registry import DEFAULT_CHAT_MODEL

# Answered with citations in every run so far; a question the baseline declines would fail.
QUESTION = {
    "question": "What does Netflix say about intellectual-property claims?",
    "ticker": "NFLX",
}
# The agent must look this number up with get_financial_fact and cite it as [F1].
AGENT_QUESTION = {"question": "What were Apple's total net sales in fiscal 2025?", "mode": "agent"}
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
    *,
    label_suffix: str = "",
    **kwargs: Any,
) -> Check:
    """One request; `describe` returns a failure reason for the JSON body, or None if fine."""
    label = f"{method} {path}{label_suffix}"
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
    if path == "/ask" and body.get("mode") == "agent":
        tools = ", ".join(c.get("name", "?") for c in body.get("tool_calls") or [])
        facts = len(body.get("fact_citations") or [])
        return (
            f"tool calls {tools}, {facts} fact citation{'s' if facts != 1 else ''}, "
            f"model {body.get('model_used')}, cached {body.get('cached')}"
        )
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


def primary_is(model: str) -> Callable[[Any], str | None]:
    """/health must name the expected primary model."""

    def check(body: Any) -> str | None:
        named = body.get("model") if isinstance(body, dict) else None
        return None if named == model else f"the primary model is {named}, not {model}"

    return check


def a_new_cited_answer_from(model: str) -> Callable[[Any], str | None]:
    """The answer cites, is new, used vector search, and came from the primary model."""

    def check(body: Any) -> str | None:
        if not isinstance(body, dict):
            return "the reply is not an answer"
        problems = []
        if not body.get("citations"):
            problems.append("the answer has no citations")
        if body.get("cached"):
            problems.append("the answer is a saved example (cached), not a new model call")
        if body.get("degraded"):
            problems.append("degraded: keyword search only, so question embedding failed")
        if body.get("model_used") != model:
            problems.append(f"answered by {body.get('model_used')}, not the primary {model}")
        return "; ".join(problems) or None

    return check


def an_agent_answer_from(model: str) -> Callable[[Any], str | None]:
    """The agent answered: it called a tool, cited a fact, was new and used the primary."""

    def check(body: Any) -> str | None:
        if not isinstance(body, dict):
            return "the reply is not an answer"
        if body.get("mode") != "agent":
            return "the reply is not from the agent"
        problems = []
        if not body.get("tool_calls"):
            problems.append("the agent made no tool call")
        if not body.get("fact_citations"):
            problems.append("the agent's answer cites no fact")
        if body.get("restarts"):
            problems.append(f"the agent restarted with a fallback ({', '.join(body['restarts'])})")
        if body.get("cached"):
            problems.append("the answer is a saved example (cached), not a new model call")
        if body.get("model_used") != model:
            problems.append(f"answered by {body.get('model_used')}, not the primary {model}")
        return "; ".join(problems) or None

    return check


def run_checks(base_url: str, client: httpx.Client, model: str = DEFAULT_CHAT_MODEL) -> list[Check]:
    """Every check, in order; a failure does not stop the rest."""
    url = base_url.rstrip("/")
    return [
        _check(client, "GET", url, "/health", primary_is(model)),
        _check(client, "GET", url, "/companies", non_empty),
        _check(client, "GET", url, "/examples", non_empty),
        _check(client, "POST", url, "/ask", a_new_cited_answer_from(model), json=QUESTION),
        _check(
            client,
            "POST",
            url,
            "/ask",
            an_agent_answer_from(model),
            label_suffix=" (agent)",
            json=AGENT_QUESTION,
        ),
    ]


def main(argv: list[str] | None = None) -> int:
    """Run the checks against URL; 0 if all pass, 1 if any fails, 2 for a bad URL."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.app.smoke")
    parser.add_argument("url", help="the deployed API, for example https://<service>.onrender.com")
    parser.add_argument(
        "--model", default=DEFAULT_CHAT_MODEL, help="the primary model the API must answer with"
    )
    args = parser.parse_args(argv)
    if not args.url.startswith("https://"):
        print("give the API's https:// address: make smoke-live URL=https://...")
        return 2
    with make_client() as client:
        results = run_checks(args.url, client, args.model)
    for _, line in results:
        print(line)
    failed = sum(not ok for ok, _ in results)
    print("smoke test passed" if not failed else f"smoke test FAILED: {failed} of {len(results)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
