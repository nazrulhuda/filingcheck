"""The only way this project talks to sec.gov.

Every request carries the SEC's required contact User-Agent, waits for the shared rate
limiter, is retried on 429 and 5xx responses, and is cached on disk so re-runs never
download the same URL twice.
"""

import hashlib
import json
import os
import re
import threading
import time
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import httpx
from dotenv import load_dotenv

from filingcheck.paths import CACHE_DIR

load_dotenv()

REQUESTS_PER_SECOND = 8.0  # the SEC allows 10; staying under it leaves a margin
MAX_RETRIES = 5
BACKOFF_SECONDS = 0.5
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


CHARSET_RE = re.compile(rb"""charset\s*=\s*["']?([A-Za-z0-9._:-]+)""", re.IGNORECASE)


def user_agent(email: str) -> str:
    """The User-Agent the SEC asks every automated client to send."""
    return f"FilingCheck/0.1 (Nazrul Huda Shanto; {email})"


def decode_document(body: bytes) -> str:
    """Decode a downloaded document without ever failing.

    Tries UTF-8, then the charset the document declares in its first 4 KB, and finally
    UTF-8 with undecodable bytes replaced by U+FFFD. Older EDGAR HTML is often not UTF-8.
    """
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError:
        pass
    declared = CHARSET_RE.search(body[:4096])
    if declared:
        try:
            return body.decode(declared.group(1).decode("ascii"), errors="replace")
        except LookupError:
            pass  # a charset name Python does not know
    return body.decode("utf-8", errors="replace")


class CacheMissError(LookupError):
    """Raised in cache-only mode when a URL has not been downloaded yet."""


class SecRequestError(RuntimeError):
    """Raised when sec.gov refuses a request or keeps failing after all retries."""


class RateLimiter:
    """Spaces requests at least 1/rate seconds apart, shared by every caller.

    A plain token bucket would let a burst through, then refill, and so could pass more
    than `rate` requests inside one second. Fixed spacing keeps any one-second window at
    or under `rate`.
    """

    def __init__(
        self,
        rate: float,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a limiter allowing `rate` requests per second."""
        if rate <= 0:
            raise ValueError("rate must be positive")
        self._interval = 1.0 / rate
        self._clock = clock
        self._sleep = sleep
        self._next_free = clock()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until the next request is allowed."""
        with self._lock:
            now = self._clock()
            if self._next_free > now:
                self._sleep(self._next_free - now)
                now = self._next_free
            self._next_free = now + self._interval


SEC_RATE_LIMITER = RateLimiter(REQUESTS_PER_SECOND)


class SecClient:
    """Cached, rate-limited HTTP client for sec.gov.

    With `cache_only=True` it never opens a connection and raises `CacheMissError` for
    any URL that is not on disk. Tests and the live app use that mode.
    """

    def __init__(
        self,
        *,
        cache_dir: Path = CACHE_DIR,
        cache_only: bool = False,
        contact_email: str | None = None,
        limiter: RateLimiter = SEC_RATE_LIMITER,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Create a client; the defaults are the real cache, email and shared limiter.

        Raises ValueError when there is no contact email: the SEC requires one in the
        User-Agent of every request. The check is here, not at import, so code that
        only reads the cache (such as the live app) can import this module without it.
        """
        email = (
            contact_email if contact_email is not None else os.environ.get("SEC_CONTACT_EMAIL", "")
        ).strip()
        if not email:
            raise ValueError(
                "SEC_CONTACT_EMAIL is empty. Copy .env.example to .env and set it: the SEC "
                "requires a contact email in the User-Agent header of every request."
            )
        self._cache_dir = cache_dir
        self._cache_only = cache_only
        self._limiter = limiter
        self._sleep = sleep
        self._http = httpx.Client(
            headers={"User-Agent": user_agent(email)},
            timeout=30.0,
            follow_redirects=True,
            transport=transport,
        )

    def get_bytes(self, url: str) -> bytes:
        """Return the body of `url`, from the disk cache when present."""
        path = self._cache_path(url)
        if path.exists():
            return path.read_bytes()
        if self._cache_only:
            raise CacheMissError(f"not cached: {url}")
        body = self._download(url)
        self._write_cache(path, body)
        return body

    def get_text(self, url: str) -> str:
        """Return the body of `url` as text; see `decode_document` for the encoding rules."""
        return decode_document(self.get_bytes(url))

    def get_json(self, url: str) -> Any:
        """Return the body of `url` parsed as JSON."""
        return json.loads(self.get_bytes(url))

    def close(self) -> None:
        """Close the underlying connection pool."""
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _cache_path(self, url: str) -> Path:
        return self._cache_dir / hashlib.sha1(url.encode("utf-8")).hexdigest()

    def _write_cache(self, path: Path, body: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_bytes(body)
        tmp.replace(path)  # atomic, so an interrupted run never leaves half a file

    def _download(self, url: str) -> bytes:
        last_problem = ""
        for attempt in range(MAX_RETRIES + 1):
            if attempt:
                self._sleep(BACKOFF_SECONDS * 2 ** (attempt - 1))
            self._limiter.acquire()
            try:
                response = self._http.get(url)
            except httpx.TransportError as exc:
                last_problem = f"{type(exc).__name__}: {exc}"
                continue
            if response.status_code in RETRY_STATUSES:
                last_problem = f"HTTP {response.status_code}"
                continue
            if response.is_error:
                raise SecRequestError(f"HTTP {response.status_code} for {url}")
            return response.content
        raise SecRequestError(f"gave up on {url} after {MAX_RETRIES} retries ({last_problem})")
