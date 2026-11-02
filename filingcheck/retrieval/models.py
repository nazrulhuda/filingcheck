"""What a search returns, and the rules every retriever shares."""

import math
from datetime import date
from typing import Protocol

from pydantic import BaseModel, Field

RRF_K = 60  # Reciprocal Rank Fusion constant: score = sum of 1 / (RRF_K + rank)
HYBRID_DEPTH = 50  # how many hits the hybrid retriever takes from each of the other two
DUPLICATE_PREFIX = 300  # two hits from one filing with these many equal first characters are one
MERGED_ITEMS = ("1", "1A", "7", "7A")  # asking for any of these also asks for "1-7A"


class Hit(BaseModel):
    """One retrieved chunk, with where it came from and how each retriever ranked it."""

    chunk_id: int
    ticker: str
    fiscal_year: int
    period_end: date | None = None  # the day the fiscal year ended
    item: str
    text: str
    score: float
    vector_rank: int | None = None
    keyword_rank: int | None = None
    source_url: str
    also_in: list[str] = Field(default_factory=list)
    boundary: str = "exact"


class SearchResult(BaseModel):
    """The hits of one search; `degraded` when vector search failed and keyword search stood in."""

    hits: list[Hit]
    retriever: str
    degraded: bool = False
    duplicates_collapsed: int = 0  # near-duplicate hits dropped while filling the top k


class Retriever(Protocol):
    """Everything later (the agent tool, the API) searches through this, never a store directly."""

    def search(
        self,
        query: str,
        *,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        items: list[str] | None = None,
        k: int = 10,
    ) -> SearchResult:
        """The top k hits for the query within the filters."""
        ...


def expand_items(items: list[str] | None) -> list[str] | None:
    """Add the merged bank section "1-7A" when any of Items 1, 1A, 7 or 7A is asked for."""
    if items is None:
        return None
    if any(item in MERGED_ITEMS for item in items) and "1-7A" not in items:
        return [*items, "1-7A"]
    return list(items)


def collapse_duplicates(hits: list[Hit], k: int | None = None) -> tuple[list[Hit], int]:
    """Drop a hit whose first characters equal an earlier hit's from the same filing.

    About 90 passages are stored under two Items of one filing; this keeps one passage from
    taking two of the k slots. Returns the kept hits (at most k) and how many were dropped
    before the k-th was kept.
    """
    seen: set[tuple[str, int, str]] = set()
    kept: list[Hit] = []
    collapsed = 0
    for hit in hits:
        if k is not None and len(kept) == k:
            break
        key = (hit.ticker, hit.fiscal_year, hit.text[:DUPLICATE_PREFIX])
        if key in seen:
            collapsed += 1
            continue
        seen.add(key)
        kept.append(hit)
    return kept, collapsed


def rrf_merge(vector_hits: list[Hit], keyword_hits: list[Hit], k: int = RRF_K) -> list[Hit]:
    """Merge two ranked lists with Reciprocal Rank Fusion, keeping each list's rank."""
    merged: dict[int, Hit] = {}
    scores: dict[int, float] = {}
    for field, hits in (("vector_rank", vector_hits), ("keyword_rank", keyword_hits)):
        for rank, hit in enumerate(hits, start=1):
            base = merged.get(hit.chunk_id, hit)
            merged[hit.chunk_id] = base.model_copy(update={field: rank})
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1 / (k + rank)
    fused = [hit.model_copy(update={"score": scores[cid]}) for cid, hit in merged.items()]
    return sorted(
        fused,
        key=lambda h: (
            -h.score,
            h.vector_rank if h.vector_rank is not None else math.inf,
            h.keyword_rank if h.keyword_rank is not None else math.inf,
            h.chunk_id,
        ),
    )
