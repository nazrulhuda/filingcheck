"""Vector, keyword and hybrid search against Postgres with 30 fixture chunks (integration)."""

from datetime import date
from pathlib import Path

import psycopg
import pytest

from filingcheck.db.load import load_all
from filingcheck.db.migrate import migrate
from filingcheck.embeddings.fake import FakeEmbeddings
from filingcheck.embeddings.openai_client import EmbeddingAPIError
from filingcheck.embeddings.runner import ModelMismatchError, run
from filingcheck.ingest.chunking import Chunk
from filingcheck.ingest.filings import ExtraDocument, Filing, Manifest
from filingcheck.ingest.sections import ItemSummary, SectionSummary, write_summary
from filingcheck.retrieval import HybridRetriever, KeywordRetriever, VectorRetriever
from filingcheck.retrieval.query import QueryEmbedder
from tests.db.test_load import APPLE, FILING, write_jsonl

pytestmark = pytest.mark.integration

IBM = APPLE.model_copy(update={"ticker": "IBM", "name": "IBM", "cik": "0000051143"})
JPM = APPLE.model_copy(
    update={"ticker": "JPM", "name": "JPMorgan", "cik": "0000019617", "revenue_rule": "bank"}
)
AAPL_2024 = FILING.model_copy(
    update={
        "fiscal_year": 2024,
        "accession": "0000320193-24-000123",
        "period_of_report": date(2024, 9, 28),
    }
)
IBM_EXHIBIT = "https://www.sec.gov/Archives/edgar/data/51143/000005114326000010/ibm-20251231_d2.htm"
IBM_2025 = FILING.model_copy(
    update={
        "ticker": "IBM",
        "cik": "0000051143",
        "accession": "0000051143-26-000010",
        "period_of_report": date(2025, 12, 31),
        "primary_document_url": "https://www.sec.gov/Archives/edgar/data/51143/x/ibm-20251231.htm",
        "extra_documents": [ExtraDocument(type="EX-13", url=IBM_EXHIBIT, document_path="x")],
    }
)
JPM_2025 = FILING.model_copy(
    update={
        "ticker": "JPM",
        "cik": "0000019617",
        "accession": "0001628280-26-008131",
        "period_of_report": date(2025, 12, 31),
        "primary_document_url": "https://www.sec.gov/Archives/edgar/data/19617/x/jpm-20251231.htm",
    }
)
FILINGS = [FILING, AAPL_2024, IBM_2025, JPM_2025]

DUPLICATE = (
    "Citi's maximum potential contingent liability related to bank card merchant processing "
    "services is estimated to be the total volume of credit card transactions that meet the "
    "requirements to be valid charge-back transactions at any given time, and the company "
    "believes the exposure is not representative of the actual potential loss exposure. "
)
TOPICS = [
    "iPhone net sales increased because of higher demand for the Pro models in every region",
    "Services revenue grew on advertising, cloud storage and payments across the installed base",
    "Mac net sales fell as customers waited for laptops with the new processors",
    "Wearables and accessories revenue declined on weaker demand for smartwatches",
    "Gross margin improved because of a better product mix and lower component costs",
    "Research and development expense rose with headcount and infrastructure spending",
    "Foreign currency changes reduced net sales in Europe and Greater China",
    "Share repurchases and dividends returned cash to shareholders during the year",
]


def chunk(filing: Filing, item: str, index: int, text: str) -> Chunk:
    return Chunk(
        ticker=filing.ticker,
        cik=filing.cik,
        fiscal_year=filing.fiscal_year,
        accession=filing.accession,
        item=item,
        chunk_index=index,
        char_start=0,
        char_end=len(text),
        text=text,
    )


def fixture_chunks() -> list[Chunk]:
    rows = [chunk(FILING, "7", i, f"{t}. ({i})") for i, t in enumerate(TOPICS)]
    rows += [
        chunk(FILING, "1A", i, f"Risk {i}: supply chain disruption in Asia ({i}).")
        for i in range(4)
    ]
    rows += [chunk(AAPL_2024, "7", i, f"{t}. Fiscal 2024 ({i}).") for i, t in enumerate(TOPICS[:4])]
    rows += [
        chunk(IBM_2025, "7", i, f"IBM software and consulting revenue, hybrid cloud ({i}).")
        for i in range(3)
    ]
    rows += [
        chunk(
            JPM_2025, "1-7A", i, f"Net interest income at the bank rose on deposit margins ({i})."
        )
        for i in range(3)
    ]
    rows += [
        chunk(JPM_2025, "1A", i, f"JPMorgan risk: capital rules and liquidity stress ({i}).")
        for i in range(2)
    ]
    rows += [
        chunk(FILING, "7", 20, DUPLICATE + "End of the MD&A copy."),
        chunk(FILING, "8", 0, DUPLICATE + "End of the notes copy, which differs."),
    ]
    rows += [chunk(FILING, "8", 1, "The xyzzyplex arrangement is disclosed in note nine.")]
    rows += [
        chunk(FILING, "8", 2 + i, f"Note {i}: accounting policies for leases ({i}).")
        for i in range(3)
    ]
    return rows


def summaries() -> list[SectionSummary]:
    def row(f: Filing, items: dict[str, str]) -> SectionSummary:
        return SectionSummary(
            ticker=f.ticker,
            fiscal_year=f.fiscal_year,
            accession=f.accession,
            short=[],
            gaps=[],
            items={i: ItemSummary(chars=1000, method=m) for i, m in items.items()},  # type: ignore[arg-type]
        )

    return [
        row(FILING, {"1A": "edgartools", "7": "edgartools", "8": "edgartools"}),
        row(AAPL_2024, {"7": "edgartools"}),
        row(IBM_2025, {"7": "exhibit"}),
        row(JPM_2025, {"1A": "edgartools", "1-7A": "edgartools"}),
    ]


@pytest.fixture
def searchable(db: psycopg.Connection, tmp_path: Path) -> psycopg.Connection:
    migrate(db)
    rows = fixture_chunks()
    assert len(rows) == 30
    summary = tmp_path / "summary.json"
    write_summary(summary, summaries())
    load_all(
        db,
        [APPLE, IBM, JPM],
        Manifest(filings=FILINGS),
        write_jsonl(tmp_path / "c.jsonl", rows),
        summary_path=summary,
    )
    run(db, FakeEmbeddings(), tmp_path / "m.parquet", log=lambda m: None)
    return db


def vector(db: psycopg.Connection, client: object | None = None) -> VectorRetriever:
    return VectorRetriever(db, QueryEmbedder(client or FakeEmbeddings()))  # type: ignore[arg-type]


class PointsAt(FakeEmbeddings):
    """Embeds every query as one fixed text, so vector search ignores the query's words."""

    def __init__(self, target: str) -> None:
        super().__init__()
        self.target = target

    def embed(self, texts: list[str]) -> list[list[float]]:
        return super().embed([self.target for _ in texts])


class Down(FakeEmbeddings):
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingAPIError("the embeddings API kept failing (HTTP 503); gave up")


def test_vector_search_returns_the_nearest_chunk(searchable: psycopg.Connection) -> None:
    result = vector(searchable).search(TOPICS[1], k=3)
    assert result.retriever == "vector" and not result.degraded
    assert result.hits[0].text.startswith(TOPICS[1]) and result.hits[0].vector_rank == 1


def test_keyword_search_finds_a_rare_term_that_vectors_miss(searchable: psycopg.Connection) -> None:
    vec = vector(searchable, PointsAt(TOPICS[5]))
    kw = KeywordRetriever(searchable)
    rare = "xyzzyplex"
    assert not any(rare in h.text for h in vec.search(rare, k=3).hits)
    keyword_hits = kw.search(rare, k=3).hits
    assert keyword_hits[0].text.startswith("The xyzzyplex") and keyword_hits[0].keyword_rank == 1
    hybrid = HybridRetriever(vec, kw).search(rare, k=5).hits
    assert any(rare in h.text for h in hybrid) and any(h.text.startswith(TOPICS[5]) for h in hybrid)


def test_filters_exclude_other_companies(searchable: psycopg.Connection) -> None:
    for retriever in (
        vector(searchable),
        HybridRetriever(vector(searchable), KeywordRetriever(searchable)),
    ):
        hits = retriever.search("revenue", ticker="IBM", k=5).hits
        assert hits and {h.ticker for h in hits} == {"IBM"}


def test_one_company_and_year_still_returns_k_hits(searchable: psycopg.Connection) -> None:
    for retriever in (
        vector(searchable),
        HybridRetriever(vector(searchable), KeywordRetriever(searchable)),
    ):
        hits = retriever.search("sales", ticker="AAPL", fiscal_year=2024, k=4).hits
        assert len(hits) == 4 and {(h.ticker, h.fiscal_year) for h in hits} == {("AAPL", 2024)}


def test_asking_for_item_7_includes_the_merged_bank_section(searchable: psycopg.Connection) -> None:
    hits = vector(searchable).search("net interest income", ticker="JPM", items=["7"], k=5).hits
    assert hits and {h.item for h in hits} == {"1-7A"}


def test_a_passage_stored_twice_appears_once(searchable: psycopg.Connection) -> None:
    for retriever in (vector(searchable), KeywordRetriever(searchable)):
        result = retriever.search("merchant processing charge-back transactions", k=5)
        copies = [h for h in result.hits if h.text.startswith(DUPLICATE[:60])]
        assert len(copies) == 1 and result.duplicates_collapsed >= 1


def test_citation_links_point_at_the_document_that_holds_the_text(
    searchable: psycopg.Connection,
) -> None:
    ibm = vector(searchable).search("software consulting hybrid cloud", ticker="IBM", k=1).hits[0]
    assert ibm.source_url == IBM_EXHIBIT and ibm.source_url.endswith("_d2.htm")
    apple = vector(searchable).search(TOPICS[0], ticker="AAPL", k=1).hits[0]
    assert apple.source_url == FILING.primary_document_url
    rows = searchable.execute("SELECT count(*) FROM section_sources").fetchone()
    assert rows == (7,)


def test_an_embedding_failure_falls_back_to_keyword_search(searchable: psycopg.Connection) -> None:
    hybrid = HybridRetriever(vector(searchable, Down()), KeywordRetriever(searchable))
    result = hybrid.search("xyzzyplex", k=3)
    assert result.degraded and result.hits[0].text.startswith("The xyzzyplex")
    assert all(h.vector_rank is None for h in result.hits)


def test_a_query_model_other_than_the_stored_one_is_refused(searchable: psycopg.Connection) -> None:
    with pytest.raises(ModelMismatchError, match="fake-embeddings"):
        vector(searchable, FakeEmbeddings(model_name="another-model")).search("revenue")


def test_a_sentence_length_question_with_words_spread_over_chunks_returns_hits(
    searchable: psycopg.Connection,
) -> None:
    question = "Which products drove the gains in gross margin, iPhone sales and services revenue?"
    hits = KeywordRetriever(searchable).search(question, k=5).hits
    assert len(hits) == 5
    assert all(h.keyword_rank is not None for h in hits)


def test_a_chunk_with_both_words_ranks_above_one_repeating_a_single_word(
    searchable: psycopg.Connection,
) -> None:
    from filingcheck.embeddings import content_hash

    filing_id = searchable.execute(
        "SELECT id FROM filings WHERE accession = %s", (FILING.accession,)
    ).fetchone()
    assert filing_id is not None
    texts = {
        90: "Zebra zebra zebra zebra zebra zebra stripes appear in the zebra herd again.",
        91: "A quokka was seen near one zebra at the reserve.",
    }
    for index, text in texts.items():
        searchable.execute(
            "INSERT INTO chunks (filing_id, item, chunk_index, char_start, char_end, text, "
            "content_hash) VALUES (%s, '7', %s, 0, %s, %s, %s)",
            (filing_id[0], index, len(text), text, content_hash(text)),
        )
    searchable.commit()
    hits = KeywordRetriever(searchable).search("zebra quokka", k=5).hits
    assert [h.text for h in hits[:2]] == [texts[91], texts[90]]


def test_a_question_of_only_stop_words_has_no_keyword_hits(searchable: psycopg.Connection) -> None:
    assert KeywordRetriever(searchable).search("what is the", k=5).hits == []


def test_every_hit_carries_the_date_its_fiscal_year_ended(searchable: psycopg.Connection) -> None:
    ends = {(f.ticker, f.fiscal_year): f.period_of_report for f in FILINGS}
    for retriever in (
        vector(searchable),
        KeywordRetriever(searchable),
        HybridRetriever(vector(searchable), KeywordRetriever(searchable)),
    ):
        hits = retriever.search("revenue sales risk", k=10).hits
        assert hits and all(h.period_end == ends[(h.ticker, h.fiscal_year)] for h in hits)
    assert ends[("AAPL", 2024)] == date(2024, 9, 28)
