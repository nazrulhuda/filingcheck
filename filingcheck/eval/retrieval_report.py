"""`make retrieval-eval`: score vector, keyword and hybrid search and write the report.

Each retriever runs every question twice, without filters and filtered to the question's
company and fiscal year, and every ranking is scored as "text found" and "right year" (see
`filingcheck.eval.retrieval`). The question vectors are saved to
`eval/results/retrieval_queries.parquet`, so a re-run makes no API call.
"""

import statistics
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import psycopg

from filingcheck.eval.retrieval import (
    RetrievalQuestion,
    load_retrieval_questions,
    longest_shared_run,
    recall_at,
    reciprocal_rank,
)
from filingcheck.retrieval import HYBRID_DEPTH, RRF_K, Retriever
from filingcheck.retrieval.query import QueryEmbedder

K = 10
QUESTIONS_FILE = Path("eval/questions/retrieval.jsonl")
QUERIES_FILE = Path("eval/results/retrieval_queries.parquet")
REPORT_FILE = Path("docs/retrieval_report.md")


@dataclass(frozen=True)
class QuestionRun:
    """One question through one retriever with one filter setting."""

    question_id: str
    retriever: str
    filtered: bool
    latency_ms: float
    collapsed: int
    rr_text: float
    rr_year: float
    r5_text: float
    r5_year: float
    r10_text: float
    r10_year: float


@dataclass(frozen=True)
class Row:
    """The averages for one retriever and one filter setting."""

    retriever: str
    filtered: bool
    questions: int
    recall5_text: float
    recall5_year: float
    recall10_text: float
    recall10_year: float
    mrr_text: float
    mrr_year: float
    median_latency_ms: float
    collapsed: int


def aggregate(runs: list[QuestionRun]) -> list[Row]:
    """Average the per-question scores for each retriever and filter setting."""
    groups: dict[tuple[str, bool], list[QuestionRun]] = {}
    for r in runs:
        groups.setdefault((r.retriever, r.filtered), []).append(r)

    def mean(values: list[float]) -> float:
        return sum(values) / len(values)

    return [
        Row(
            retriever=retriever,
            filtered=filtered,
            questions=len(g),
            recall5_text=mean([r.r5_text for r in g]),
            recall5_year=mean([r.r5_year for r in g]),
            recall10_text=mean([r.r10_text for r in g]),
            recall10_year=mean([r.r10_year for r in g]),
            mrr_text=mean([r.rr_text for r in g]),
            mrr_year=mean([r.rr_year for r in g]),
            median_latency_ms=statistics.median(r.latency_ms for r in g),
            collapsed=sum(r.collapsed for r in g),
        )
        for (retriever, filtered), g in groups.items()
    ]


def render_report(
    rows: list[Row],
    questions: list[tuple[str, str, int, str, int, str]],
    settings: dict[str, str],
    notes: list[str],
) -> str:
    """The report as Markdown: settings, the score table, notes, and the question list."""
    lines = [
        "# Retrieval report",
        "",
        "Written by `make retrieval-eval`; do not edit by hand.",
        "",
        "## Settings",
        "",
        *[f"- {name}: {value}" for name, value in settings.items()],
        "",
        "## Scores",
        "",
        f"Each question is searched once per row; the top {K} hits are scored two ways. "
        "**Text found**: a hit from the question's company that is the expected chunk or "
        "contains its `must_contain` phrase, in any fiscal year. **Right year**: the same, and "
        "the fiscal year matches too. With the company + year filter the two coincide.",
        "",
        "| Retriever | Filter | Recall@5 text found | Recall@5 right year | Recall@10 text found "
        "| Recall@10 right year | MRR text found | MRR right year | Median latency (ms) "
        "| Near-duplicates collapsed |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    order = {"vector": 0, "keyword": 1, "hybrid": 2}
    for r in sorted(rows, key=lambda r: (r.filtered, order.get(r.retriever, 9))):
        lines.append(
            f"| {r.retriever} | {'company + year' if r.filtered else 'none'} "
            f"| {r.recall5_text:.2f} | {r.recall5_year:.2f} | {r.recall10_text:.2f} "
            f"| {r.recall10_year:.2f} | {r.mrr_text:.3f} | {r.mrr_year:.3f} "
            f"| {r.median_latency_ms:.0f} | {r.collapsed} |"
        )
    lines += ["", "## Notes", "", *[f"- {note}" for note in notes], ""]
    lines += [
        "## Questions",
        "",
        "Longest run: the longest run of consecutive words a question shares with its source "
        "chunk (questions are written in a user's words; the limit is 3).",
        "",
        "| Id | Company | Fiscal year | Item | Longest run | Question |",
        "|---|---|---:|---|---:|---|",
        *[f"| {qid} | {t} | {y} | {item} | {run} | {q} |" for qid, t, y, item, run, q in questions],
    ]
    return "\n".join(lines).rstrip("\n") + "\n"


def evaluate(
    questions: list[RetrievalQuestion],
    expected: dict[str, int],
    retrievers: dict[str, Retriever],
) -> list[QuestionRun]:
    """Run every question through every retriever, without and with the company + year filter."""
    runs = []
    for name, retriever in retrievers.items():
        for filtered in (False, True):
            for q in questions:
                filters = {"ticker": q.ticker, "fiscal_year": q.fiscal_year} if filtered else {}
                start = time.perf_counter()
                result = retriever.search(q.question, k=K, **filters)  # type: ignore[arg-type]
                ms = (time.perf_counter() - start) * 1000
                hits, eid = result.hits, expected[q.id]
                runs.append(
                    QuestionRun(
                        question_id=q.id,
                        retriever=name,
                        filtered=filtered,
                        latency_ms=ms,
                        collapsed=result.duplicates_collapsed,
                        rr_text=reciprocal_rank(hits, q, eid, right_year=False),
                        rr_year=reciprocal_rank(hits, q, eid, right_year=True),
                        r5_text=recall_at(hits, q, eid, 5, right_year=False),
                        r5_year=recall_at(hits, q, eid, 5, right_year=True),
                        r10_text=recall_at(hits, q, eid, 10, right_year=False),
                        r10_year=recall_at(hits, q, eid, 10, right_year=True),
                    )
                )
    return runs


def _expected(
    conn: psycopg.Connection, questions: list[RetrievalQuestion]
) -> dict[str, tuple[int, str]]:
    found = {}
    for q in questions:
        row = conn.execute(
            "SELECT c.id, c.text FROM chunks c JOIN filings f ON f.id = c.filing_id "
            "WHERE f.accession = %s AND c.item = %s AND c.chunk_index = %s",
            (q.accession, q.item, q.chunk_index),
        ).fetchone()
        if row is None:
            raise LookupError(f"{q.id}: no chunk {q.accession} Item {q.item} #{q.chunk_index}")
        found[q.id] = (int(row[0]), str(row[1]))
    return found


def _prime_or_embed(
    embedder: QueryEmbedder, questions: list[RetrievalQuestion], path: Path
) -> tuple[int, bool]:
    """Fill the query cache from the saved vectors, or embed and save them.

    Returns the tokens billed and whether the saved vectors were used.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    if path.exists():
        table = pq.read_table(path)
        saved = dict(
            zip(table.column("id").to_pylist(), table.column("vector").to_pylist(), strict=True)
        )
        if all(q.id in saved for q in questions):
            for q in questions:
                embedder.prime(q.question, [float(x) for x in saved[q.id]])
            return 0, True
    before = embedder.tokens_used
    vectors = [embedder.embed(q.question) for q in questions]
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.table(
            {
                "id": pa.array([q.id for q in questions], pa.string()),
                "vector": pa.array(vectors, pa.list_(pa.float32())),
            }
        ),
        path,
    )
    return embedder.tokens_used - before, False


def main(root: Path = Path(".")) -> int:
    """Run the eval against the local database and write docs/retrieval_report.md."""
    from dotenv import load_dotenv

    from filingcheck.db import connect
    from filingcheck.db.load import current_model
    from filingcheck.embeddings.openai_client import OpenAIEmbeddings
    from filingcheck.ingest.companies import load_companies
    from filingcheck.llm.pricing import cost_usd
    from filingcheck.retrieval import HybridRetriever, KeywordRetriever, VectorRetriever

    load_dotenv(root / ".env")
    tickers = {c.ticker for c in load_companies(root / "data" / "companies.yaml")}
    questions = load_retrieval_questions(root / QUESTIONS_FILE, tickers)
    embedder = QueryEmbedder(OpenAIEmbeddings())
    with connect() as conn:
        found = _expected(conn, questions)
        tokens, reused = _prime_or_embed(embedder, questions, root / QUERIES_FILE)
        vector = VectorRetriever(conn, embedder)
        keyword = KeywordRetriever(conn)
        retrievers: dict[str, Retriever] = {
            "vector": vector,
            "keyword": keyword,
            "hybrid": HybridRetriever(vector, keyword),
        }
        runs = evaluate(questions, {qid: cid for qid, (cid, _) in found.items()}, retrievers)
        model = current_model(conn) or "none"
    rows = aggregate(runs)
    unfiltered = {r.retriever: r for r in rows if not r.filtered}
    gaps = ", ".join(
        f"{name} {unfiltered[name].recall10_text - unfiltered[name].recall10_year:+.2f}"
        for name in ("vector", "keyword", "hybrid")
        if name in unfiltered
    )
    cost = cost_usd(embedder.model_name, tokens)
    notes = [
        "Unfiltered rows: the gap between recall@10 text found and right year "
        f"({gaps}) is how often search alone cannot pick the fiscal year. About a quarter of "
        "the chunks have an identical copy in another year's filing, and identical texts tie "
        "in an unfiltered search (same vector, same keyword score). This is the measured "
        "reason for the fiscal-year check in week 4.",
        "Latency is the search alone: the question vectors were embedded beforehand "
        f"({'loaded from' if reused else 'and saved to'} {QUERIES_FILE}).",
        f"Query embeddings this run: {len(questions)} questions, {tokens:,} tokens, ${cost:.6f}"
        + (" (vectors reused, no API call)" if reused else "")
        + ".",
    ]
    settings = {
        "date": date.today().isoformat(),
        "questions": f"{len(questions)} ({QUESTIONS_FILE})",
        "embedding model": model,
        "hits scored per search (k)": str(K),
        "RRF": f"score = sum of 1 / ({RRF_K} + rank) over the vector and keyword rankings; "
        f"top {HYBRID_DEPTH} taken from each",
        "vector search": "cosine distance; HNSW (m = 16, ef_construction = 64) with "
        "ef_search = 100 and iterative scan (relaxed order) when unfiltered; an exact scan "
        "when filtered to one company and year",
        "keyword search": "Postgres websearch_to_tsquery('english') on the chunk text, "
        "ranked by ts_rank_cd",
        "near-duplicates": "a hit whose first 300 characters equal an earlier hit's from the "
        "same filing is dropped before the cut to k",
    }
    question_rows = [
        (
            q.id,
            q.ticker,
            q.fiscal_year,
            q.item,
            longest_shared_run(q.question, found[q.id][1]),
            q.question,
        )
        for q in questions
    ]
    report = render_report(rows, question_rows, settings, notes)
    (root / REPORT_FILE).write_text(report, encoding="utf-8", newline="\n")
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
