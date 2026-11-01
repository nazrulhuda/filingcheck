"""Search over the chunks: vector, keyword and hybrid, all behind one `Retriever` protocol."""

from filingcheck.retrieval.models import (
    HYBRID_DEPTH,
    RRF_K,
    Hit,
    Retriever,
    SearchResult,
    collapse_duplicates,
    expand_items,
    rrf_merge,
)
from filingcheck.retrieval.search import HybridRetriever, KeywordRetriever, VectorRetriever

__all__ = [
    "HYBRID_DEPTH",
    "RRF_K",
    "Hit",
    "HybridRetriever",
    "KeywordRetriever",
    "Retriever",
    "SearchResult",
    "VectorRetriever",
    "collapse_duplicates",
    "expand_items",
    "rrf_merge",
]
