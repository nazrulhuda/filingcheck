"""Vector, keyword and hybrid search over the chunks in Postgres."""

from typing import Any

import httpx
import psycopg

from filingcheck.db.load import current_model
from filingcheck.embeddings.openai_client import EmbeddingAPIError, MissingAPIKeyError
from filingcheck.embeddings.runner import ModelMismatchError
from filingcheck.retrieval.models import (
    HYBRID_DEPTH,
    RRF_K,
    Hit,
    SearchResult,
    collapse_duplicates,
    expand_items,
    rrf_merge,
)
from filingcheck.retrieval.query import QueryEmbedder

EF_SEARCH = 100  # HNSW candidates examined per query
OVERFETCH = 3  # fetch k * 3 + 10 rows so k remain after duplicates are dropped
COLUMNS = (
    "c.id, f.ticker, f.fiscal_year, c.item, c.text, c.also_in, c.boundary, "
    "COALESCE(s.source_url, f.primary_url) AS source_url, f.period_of_report"
)
FROM = (
    "FROM chunks c JOIN filings f ON f.id = c.filing_id "
    "LEFT JOIN section_sources s ON s.filing_id = c.filing_id AND s.item = c.item"
)
# The keyword queries for a question %(q)s. query_any quotes each lexeme so that one with a
# hyphen ("drug-pric") stays a single term; it is NULL, matching nothing, when the question
# has no lexemes at all.
QUERIES_SQL = (
    "SELECT websearch_to_tsquery('english', %(q)s) AS query_all, "
    "NULLIF(array_to_string(ARRAY("
    "SELECT '''' || replace(lexeme, '''', '''''') || '''' "
    "FROM unnest(tsvector_to_array(to_tsvector('english', %(q)s))) AS lexeme"
    "), ' | '), '')::tsquery AS query_any"
)
# Failures of the embeddings API that should not take search down: keyword search stands in.
EMBEDDING_FAILURES = (EmbeddingAPIError, MissingAPIKeyError, httpx.HTTPError, OSError)


def _filters(
    ticker: str | None, fiscal_year: int | None, items: list[str] | None
) -> tuple[str, dict[str, Any]]:
    clauses: list[str] = ["TRUE"]
    params: dict[str, Any] = {}
    if ticker is not None:
        clauses.append("f.ticker = %(ticker)s")
        params["ticker"] = ticker
    if fiscal_year is not None:
        clauses.append("f.fiscal_year = %(fiscal_year)s")
        params["fiscal_year"] = fiscal_year
    expanded = expand_items(items)
    if expanded is not None:
        clauses.append("c.item = ANY(%(items)s)")
        params["items"] = expanded
    return " AND ".join(clauses), params


def _hit(row: tuple[Any, ...], score: float) -> Hit:
    chunk_id, ticker, year, item, text, also_in, boundary, url, period_end = row[:9]
    return Hit(
        chunk_id=chunk_id,
        ticker=ticker,
        fiscal_year=year,
        period_end=period_end,
        item=item,
        text=text,
        score=score,
        source_url=url,
        also_in=list(also_in),
        boundary=boundary,
    )


def _ranked(hits: list[Hit], k: int, field: str) -> tuple[list[Hit], int]:
    kept, collapsed = collapse_duplicates(hits, k)
    return [h.model_copy(update={field: rank}) for rank, h in enumerate(kept, 1)], collapsed


class VectorRetriever:
    """Nearest chunks by cosine distance between the question's vector and each chunk's.

    An HNSW scan finds candidates first and filters after, so a narrow filter could return
    fewer than k hits. With both a company and a year the search is an exact scan over that
    filing's few hundred rows; otherwise pgvector's iterative scan keeps looking until k
    rows pass the filter.
    """

    name = "vector"

    def __init__(self, conn: psycopg.Connection, embedder: QueryEmbedder) -> None:
        self.conn = conn
        self.embedder = embedder
        self._checked = False

    def search(
        self,
        query: str,
        *,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        items: list[str] | None = None,
        k: int = 10,
    ) -> SearchResult:
        """The k nearest chunks within the filters."""
        self._check_model()
        vector = "[" + ",".join(f"{x:.7g}" for x in self.embedder.embed(query)) + "]"
        where, params = _filters(ticker, fiscal_year, items)
        params |= {"q": vector, "n": k * OVERFETCH + 10}
        if ticker is not None and fiscal_year is not None:
            sql = (
                f"WITH pool AS MATERIALIZED (SELECT {COLUMNS}, "
                f"c.embedding <=> %(q)s::halfvec AS distance {FROM} WHERE {where}) "
                "SELECT * FROM pool ORDER BY distance, id LIMIT %(n)s"
            )
        else:
            self.conn.execute(f"SET hnsw.ef_search = {EF_SEARCH}")
            self.conn.execute("SET hnsw.iterative_scan = relaxed_order")
            sql = (
                f"SELECT {COLUMNS}, c.embedding <=> %(q)s::halfvec AS distance {FROM} "
                f"WHERE {where} ORDER BY c.embedding <=> %(q)s::halfvec LIMIT %(n)s"
            )
        rows = self.conn.execute(sql, params).fetchall()
        rows.sort(key=lambda r: (r[9], r[0]))  # relaxed order: put the nearest first again
        hits, collapsed = _ranked([_hit(r, 1.0 - float(r[9])) for r in rows], k, "vector_rank")
        return SearchResult(hits=hits, retriever=self.name, duplicates_collapsed=collapsed)

    def _check_model(self) -> None:
        if self._checked:
            return
        stored = current_model(self.conn)
        if stored is not None and stored != self.embedder.model_name:
            raise ModelMismatchError(
                f"the chunks were embedded with {stored}; refusing to search with "
                f"{self.embedder.model_name} question vectors"
            )
        self._checked = True


class KeywordRetriever:
    """Full-text search on the chunk text: any word may match, all-word matches come first.

    Two queries are built from the question: `query_all` (websearch_to_tsquery, every word
    required) and `query_any` (the question's lexemes joined with OR; stop words are already
    gone). Candidates match `query_any`; they are ordered by whether they match `query_all`,
    then by ts_rank_cd. A question of stop words only has no lexemes and gets no hits.
    Requiring every word alone matched no chunk for any of the 40 sentence-length eval
    questions; short exact-term queries still put the chunks with every word first.
    """

    name = "keyword"

    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def search(
        self,
        query: str,
        *,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        items: list[str] | None = None,
        k: int = 10,
    ) -> SearchResult:
        """The k best keyword matches within the filters."""
        where, params = _filters(ticker, fiscal_year, items)
        params |= {"q": query, "n": k * OVERFETCH + 10}
        rows = self.conn.execute(
            f"WITH q AS ({QUERIES_SQL}) "
            f"SELECT {COLUMNS}, ts_rank_cd(c.tsv, q.query_any) AS rank {FROM} CROSS JOIN q "
            f"WHERE c.tsv @@ q.query_any AND {where} "
            "ORDER BY (c.tsv @@ q.query_all) DESC, rank DESC, c.id LIMIT %(n)s",
            params,
        ).fetchall()
        hits, collapsed = _ranked([_hit(r, float(r[9])) for r in rows], k, "keyword_rank")
        return SearchResult(hits=hits, retriever=self.name, duplicates_collapsed=collapsed)


class HybridRetriever:
    """The top 50 of vector and of keyword search, merged with Reciprocal Rank Fusion.

    If the question cannot be embedded (the embeddings API is down), keyword search alone
    answers and the result is marked degraded, so the live demo keeps working.
    """

    name = "hybrid"

    def __init__(
        self,
        vector: VectorRetriever,
        keyword: KeywordRetriever,
        rrf_k: int = RRF_K,
        depth: int = HYBRID_DEPTH,
    ) -> None:
        self.vector = vector
        self.keyword = keyword
        self.rrf_k = rrf_k
        self.depth = depth

    def search(
        self,
        query: str,
        *,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        items: list[str] | None = None,
        k: int = 10,
    ) -> SearchResult:
        """The top k after fusing both rankings."""
        filters: dict[str, Any] = {"ticker": ticker, "fiscal_year": fiscal_year, "items": items}
        keyword = self.keyword.search(query, k=self.depth, **filters)
        try:
            vector = self.vector.search(query, k=self.depth, **filters)
        except EMBEDDING_FAILURES:
            return SearchResult(
                hits=keyword.hits[:k],
                retriever=self.name,
                degraded=True,
                duplicates_collapsed=keyword.duplicates_collapsed,
            )
        fused = rrf_merge(vector.hits, keyword.hits, self.rrf_k)
        hits, collapsed = collapse_duplicates(fused, k)
        return SearchResult(hits=hits, retriever=self.name, duplicates_collapsed=collapsed)
