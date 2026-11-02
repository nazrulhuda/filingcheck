"""Per-address limits, client addresses and the cached answer nearest to a question."""

import hashlib
import hmac
import re
import threading
import time
from collections.abc import Callable, Mapping

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


def client_ip(peer: str | None, headers: Mapping[str, str], hops: int) -> str:
    """The caller's address: the peer, or with `hops` trusted proxies the entry they added.

    Each proxy appends the address it saw to X-Forwarded-For, so the entry `hops` from the
    end was written by the outermost trusted proxy; entries before it can be forged.
    """
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
