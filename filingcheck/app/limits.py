"""Per-address limits, client addresses and the cached answer nearest to a question."""

import hashlib
import hmac
import re
import threading
import time
from collections.abc import Callable, Mapping

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from filingcheck.app.settings import MAX_BODY_BYTES
from filingcheck.app.store import ExampleAnswer

NEAREST_MIN_SHARE = 0.6  # share of the longer question's words the two must have in common
STOP_WORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "did",
        "do",
        "does",
        "for",
        "from",
        "had",
        "has",
        "have",
        "how",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "the",
        "their",
        "to",
        "was",
        "were",
        "what",
        "when",
        "which",
        "who",
        "whom",
        "why",
        "with",
    ]
)
WORD_RE = re.compile(r"[a-z0-9]+")


class TokenBucket:
    """`capacity` requests per `per_seconds` for each key, refilled continuously.

    Lives in memory, so it restarts with the process; the request log is the backstop.
    """

    def __init__(
        self,
        capacity: int,
        per_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.capacity = capacity
        self.rate = capacity / per_seconds
        self._clock = clock
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, time)
        self._lock = threading.Lock()

    def take(self, key: str) -> bool:
        """Use one token for `key`; False when none is left."""
        with self._lock:
            now = self._clock()
            tokens, then = self._buckets.get(key, (float(self.capacity), now))
            tokens = min(float(self.capacity), tokens + (now - then) * self.rate)
            if tokens < 1:
                self._buckets[key] = (tokens, now)
                return False
            self._buckets[key] = (tokens - 1, now)
            if len(self._buckets) > 10_000:  # forget addresses whose bucket is full again
                self._buckets = {
                    k: (t, s)
                    for k, (t, s) in self._buckets.items()
                    if t + (now - s) * self.rate < self.capacity
                }
            return True


def client_ip(
    peer: str | None, headers: Mapping[str, str], hops: int, header: str | None = None
) -> str:
    """The caller's address: the peer, or with `hops` trusted proxies the entry they added.

    Each proxy appends the address it saw to X-Forwarded-For, so the entry `hops` from the
    end was written by the outermost trusted proxy; entries before it can be forged. With
    `header` set (a header the platform overwrites, such as Cloudflare's CF-Connecting-IP on
    Render), that header alone is trusted, and the peer is used when it is missing.
    """
    if header is not None:
        return headers.get(header, "").strip() or peer or "unknown"
    forwarded = [p.strip() for p in headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if hops and len(forwarded) >= hops:
        return forwarded[-hops]
    return peer or "unknown"


def hash_ip(ip: str, salt: str) -> str:
    """A keyed hash of the address, so the log never holds the address itself."""
    return hmac.new(salt.encode(), ip.encode(), hashlib.sha256).hexdigest()


def words(text: str) -> set[str]:
    """The question's words, lower case, without possessives and stop words."""
    return set(WORD_RE.findall(text.lower().replace("'s", ""))) - STOP_WORDS


def nearest_example(question: str, examples: list[ExampleAnswer]) -> ExampleAnswer | None:
    """The example question sharing most words with this one, if they share enough."""
    asked = words(question)
    best: tuple[float, ExampleAnswer] | None = None
    for example in examples:
        theirs = words(example.question)
        if not asked or not theirs:
            continue
        share = len(asked & theirs) / max(len(asked), len(theirs))
        if share >= NEAREST_MIN_SHARE and (best is None or share > best[0]):
            best = (share, example)
    return best[1] if best else None


TOO_LARGE = f"The request is too large; the limit is {MAX_BODY_BYTES // 1024} KB."


class BodySizeLimit:
    """Refuse request bodies over `limit` bytes (HTTP 413) before they are read in full.

    A larger Content-Length is refused before any of the body is read; a body sent without one
    is counted as it arrives. Either way a stream of oversized posts cannot fill the memory.
    """

    def __init__(self, app: ASGIApp, limit: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.limit = limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass the request on, or answer 413 if its body is or becomes too large."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        length = dict(scope["headers"]).get(b"content-length")
        if length is not None and (not length.isdigit() or int(length) > self.limit):
            await JSONResponse({"detail": TOO_LARGE}, status_code=413)(scope, receive, send)
            return
        received = 0

        async def counted() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.limit:
                    # FastAPI re-raises an HTTPException met while reading the body.
                    raise HTTPException(413, TOO_LARGE)
            return message

        await self.app(scope, counted, send)
