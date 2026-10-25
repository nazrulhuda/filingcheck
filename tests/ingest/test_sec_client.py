import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

from filingcheck.ingest.sec_client import (
    CacheMissError,
    RateLimiter,
    SecClient,
    SecRequestError,
    user_agent,
)

URL = "https://www.sec.gov/files/company_tickers.json"


class FakeClock:
    """A clock where sleeping moves time forward instantly."""

    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def make_client(
    tmp_path: Path,
    handler: httpx.MockTransport,
    clock: FakeClock,
    **kwargs: object,
) -> SecClient:
    limiter = RateLimiter(8.0, clock=clock.time, sleep=clock.sleep)
    return SecClient(
        cache_dir=tmp_path / "cache",
        transport=handler,
        limiter=limiter,
        sleep=clock.sleep,
        **kwargs,  # type: ignore[arg-type]
    )


# ---------------------------------------------------------------- rate limiter


def test_rate_limiter_never_exceeds_8_per_second_in_a_2_second_burst() -> None:
    clock = FakeClock()
    limiter = RateLimiter(8.0, clock=clock.time, sleep=clock.sleep)
    stamps: list[float] = []
    while clock.now < 2.0:
        limiter.acquire()
        stamps.append(clock.now)
    assert len(stamps) >= 16
    for start in stamps:
        in_window = [s for s in stamps if start <= s < start + 1.0]
        assert len(in_window) <= 8


def test_rate_limiter_does_not_wait_when_requests_are_spread_out() -> None:
    clock = FakeClock()
    limiter = RateLimiter(8.0, clock=clock.time, sleep=clock.sleep)
    limiter.acquire()
    clock.now += 1.0
    limiter.acquire()
    assert clock.sleeps == []


def test_rate_limiter_rejects_a_non_positive_rate() -> None:
    with pytest.raises(ValueError):
        RateLimiter(0)


# ---------------------------------------------------------------- headers and cache


def test_every_request_sends_the_contact_user_agent(tmp_path: Path) -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["User-Agent"])
        return httpx.Response(200, text="ok")

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock())
    client.get_text(URL)
    assert seen == ["FilingCheck/0.1 (Nazrul Huda Shanto; tests@example.com)"]
    assert user_agent("someone@example.com") == (
        "FilingCheck/0.1 (Nazrul Huda Shanto; someone@example.com)"
    )


def test_a_cached_url_does_not_touch_the_network_again(tmp_path: Path) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"0": {"cik_str": 320193, "ticker": "AAPL"}})

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock())
    first = client.get_json(URL)
    second = client.get_json(URL)
    assert first == second == {"0": {"cik_str": 320193, "ticker": "AAPL"}}
    assert calls == [URL]
    cached = tmp_path / "cache" / hashlib.sha1(URL.encode()).hexdigest()
    assert json.loads(cached.read_bytes()) == first


def test_cache_only_raises_on_a_miss_without_calling_the_network(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("cache_only must never send a request")

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock(), cache_only=True)
    with pytest.raises(CacheMissError):
        client.get_text(URL)


def test_cache_only_returns_a_cached_response(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / hashlib.sha1(URL.encode()).hexdigest()).write_bytes(b"cached body")

    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("must not be called")

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock(), cache_only=True)
    assert client.get_text(URL) == "cached body"


# ---------------------------------------------------------------- retries


def test_server_errors_are_retried_with_exponential_backoff(tmp_path: Path) -> None:
    statuses = iter([503, 429, 200])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(next(statuses), text="done")

    clock = FakeClock()
    client = make_client(tmp_path, httpx.MockTransport(handler), clock)
    assert client.get_text(URL) == "done"
    backoffs = [s for s in clock.sleeps if s >= 0.5]
    assert backoffs == [0.5, 1.0]


def test_gives_up_after_5_retries(tmp_path: Path) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(500)

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock())
    with pytest.raises(SecRequestError):
        client.get_text(URL)
    assert len(calls) == 6  # the first try plus 5 retries
    assert not (tmp_path / "cache").exists() or not any((tmp_path / "cache").iterdir())


def test_client_errors_other_than_429_are_not_retried(tmp_path: Path) -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(404)

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock())
    with pytest.raises(SecRequestError):
        client.get_text(URL)
    assert calls == [1]


def test_network_errors_are_retried(tmp_path: Path) -> None:
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) == 1:
            raise httpx.ConnectError("connection reset")
        return httpx.Response(200, text="ok")

    client = make_client(tmp_path, httpx.MockTransport(handler), FakeClock())
    assert client.get_text(URL) == "ok"
    assert len(attempts) == 2


def test_client_works_as_a_context_manager(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="ok"))
    with make_client(tmp_path, transport, FakeClock()) as client:
        assert client.get_text(URL) == "ok"


def test_network_downloads_are_counted_and_cache_hits_are_not(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text="ok"))
    client = make_client(tmp_path, transport, FakeClock())
    client.get_text(URL)
    client.get_text(URL)
    client.get_text(URL + "?page=2")
    assert client.downloads == 2


# ---------------------------------------------------------------- decoding documents


def body_client(tmp_path: Path, body: bytes) -> SecClient:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=body))
    return make_client(tmp_path, transport, FakeClock())


def test_utf8_documents_decode_normally(tmp_path: Path) -> None:
    text = "Nestl" + chr(0xE9) + chr(0x2019) + "s"  # an accented e and a curly apostrophe
    assert body_client(tmp_path, text.encode()).get_text(URL) == text


def test_a_declared_charset_is_used_when_the_document_is_not_utf8(tmp_path: Path) -> None:
    body = b'<html><head><meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">'
    body += b"</head><body>caf\xe9</body></html>"
    assert "café" in body_client(tmp_path, body).get_text(URL)


def test_undecodable_bytes_are_replaced_instead_of_crashing(tmp_path: Path) -> None:
    text = body_client(tmp_path, b"revenue \xff\xfe rose").get_text(URL)
    assert text.startswith("revenue ")
    assert text.endswith(" rose")
    assert "�" in text


def test_an_unknown_declared_charset_falls_back_to_replacement(tmp_path: Path) -> None:
    body = b'<meta charset="no-such-charset"><p>caf\xe9</p>'
    assert "caf�" in body_client(tmp_path, body).get_text(URL)


# ---------------------------------------------------------------- contact email check


def test_the_module_imports_without_a_contact_email() -> None:
    # The live app imports the package but never downloads, so it must not need the email.
    env = dict(os.environ, SEC_CONTACT_EMAIL="")
    result = subprocess.run(
        [sys.executable, "-c", "import filingcheck.ingest.sec_client"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_creating_a_client_without_a_contact_email_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="SEC_CONTACT_EMAIL"):
        SecClient(cache_dir=tmp_path, contact_email="  ")
