"""Retrieval pieces that need no database: fusion, duplicates, filters, the query cache, scoring."""

import pytest

from filingcheck.embeddings.fake import FakeEmbeddings
from filingcheck.eval.retrieval import (
    RetrievalQuestion,
    is_hit,
    longest_shared_run,
    recall_at,
    reciprocal_rank,
)
from filingcheck.retrieval import (
    RRF_K,
    Hit,
    collapse_duplicates,
    expand_items,
    rrf_merge,
)
from filingcheck.retrieval.query import QueryEmbedder


def hit(chunk_id: int, text: str = "", ticker: str = "AAPL", year: int = 2025) -> Hit:
    return Hit(
        chunk_id=chunk_id,
        ticker=ticker,
        fiscal_year=year,
        item="7",
        text=text or f"passage {chunk_id}",
        score=0.0,
        source_url="https://www.sec.gov/x.htm",
    )


# ---------------------------------------------------------------- reciprocal rank fusion


def test_rrf_adds_one_over_k_plus_rank_from_each_list_and_keeps_both_ranks() -> None:
    vector = [hit(1), hit(2), hit(3)]
    keyword = [hit(3), hit(4)]
    merged = rrf_merge(vector, keyword, k=60)
    by_id = {h.chunk_id: h for h in merged}
    assert by_id[3].score == pytest.approx(1 / 63 + 1 / 61)
    assert by_id[1].score == pytest.approx(1 / 61)
    assert by_id[4].score == pytest.approx(1 / 62)
    assert (by_id[3].vector_rank, by_id[3].keyword_rank) == (3, 1)
    assert (by_id[1].vector_rank, by_id[1].keyword_rank) == (1, None)
    assert [h.chunk_id for h in merged] == [3, 1, 2, 4]
    assert RRF_K == 60


def test_rrf_breaks_ties_by_the_vector_rank_then_the_chunk_id() -> None:
    merged = rrf_merge([hit(5), hit(6)], [hit(6), hit(5)], k=60)
    assert [h.chunk_id for h in merged] == [5, 6]


# ---------------------------------------------------------------- near-duplicate hits


def test_a_passage_stored_under_two_items_takes_one_slot() -> None:
    same = "Citi's maximum potential contingent liability related to merchant processing. " * 5
    hits = [hit(1, same), hit(2, "something else"), hit(3, same[:300] + " but a different end")]
    kept, collapsed = collapse_duplicates(hits)
    assert [h.chunk_id for h in kept] == [1, 2] and collapsed == 1


def test_the_same_passage_in_another_filing_is_kept() -> None:
    same = "Risk factors repeated word for word from one year to the next. " * 6
    kept, collapsed = collapse_duplicates([hit(1, same, year=2024), hit(2, same, year=2025)])
    assert len(kept) == 2 and collapsed == 0


# ---------------------------------------------------------------- the 1-7A rule


def test_asking_for_items_1_to_7a_also_asks_for_the_merged_bank_sections() -> None:
    assert expand_items(["7"]) == ["7", "1-7A"]
    assert expand_items(["1A", "8"]) == ["1A", "8", "1-7A"]
    assert expand_items(["8"]) == ["8"]
    assert expand_items(None) is None


# ---------------------------------------------------------------- the query cache


def test_the_same_question_twice_is_embedded_once() -> None:
    fake = FakeEmbeddings()
    embedder = QueryEmbedder(fake)
    first = embedder.embed("What are Walmart's main risks in Mexico?")
    second = embedder.embed("What are Walmart's main risks in Mexico?")
    assert first == second and fake.calls == 1
    embedder.embed("Another question")
    assert fake.calls == 2
    assert embedder.model_name == "fake-embeddings" and embedder.tokens_used > 0


# ---------------------------------------------------------------- scoring the retrieval eval

QUESTION = RetrievalQuestion(
    id="ret-001",
    source="synthetic",
    question="How did Apple's iPhone sales change this year?",
    ticker="AAPL",
    fiscal_year=2025,
    item="7",
    accession="0000320193-25-000079",
    chunk_index=12,
    must_contain="iPhone net sales increased",
)


def test_a_hit_counts_if_it_is_the_expected_chunk_or_contains_the_phrase() -> None:
    assert is_hit(hit(42), QUESTION, expected_id=42)
    assert is_hit(hit(7, "Overall, iPhone net sales increased during 2025."), QUESTION, 42)
    assert not is_hit(hit(7, "Mac net sales were flat."), QUESTION, 42)


def test_a_hit_from_another_year_or_company_never_counts() -> None:
    text = "iPhone net sales increased during the year."
    assert not is_hit(hit(42, text, year=2024), QUESTION, expected_id=42)
    assert not is_hit(hit(42, text, ticker="MSFT"), QUESTION, expected_id=42)


def test_recall_and_reciprocal_rank() -> None:
    hits = [hit(1), hit(2), hit(42), hit(4)]
    assert recall_at(hits, QUESTION, 42, k=5) == 1.0
    assert recall_at(hits, QUESTION, 42, k=2) == 0.0
    assert reciprocal_rank(hits, QUESTION, 42) == pytest.approx(1 / 3)
    assert reciprocal_rank([hit(1)], QUESTION, 42) == 0.0


def test_the_longest_run_of_words_shared_with_the_chunk() -> None:
    chunk = "Net sales of iPhone increased during 2025 due to higher sales of Pro models."
    assert longest_shared_run("How did Apple's phone revenue change?", chunk) == 0
    assert longest_shared_run("Why did sales of iPhone go up?", chunk) == 3  # "sales of iphone"
    assert longest_shared_run("What were net sales?", chunk) == 2


def test_a_retrieval_question_needs_a_phrase_and_a_known_source() -> None:
    with pytest.raises(ValueError):
        RetrievalQuestion.model_validate(QUESTION.model_dump() | {"must_contain": ""})
    with pytest.raises(ValueError):
        RetrievalQuestion.model_validate(QUESTION.model_dump() | {"source": "made-up"})
