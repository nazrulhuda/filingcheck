"""The retrieval report: averaging per-question scores and rendering the table."""

import pytest

from filingcheck.eval.retrieval_report import QuestionRun, aggregate, render_report


def run(retriever: str, filtered: bool, rr_text: float, rr_year: float, ms: float) -> QuestionRun:
    return QuestionRun(
        question_id="ret-001",
        retriever=retriever,
        filtered=filtered,
        latency_ms=ms,
        collapsed=1,
        rr_text=rr_text,
        rr_year=rr_year,
        r5_text=1.0 if rr_text >= 0.2 else 0.0,
        r5_year=1.0 if rr_year >= 0.2 else 0.0,
        r10_text=1.0 if rr_text > 0 else 0.0,
        r10_year=1.0 if rr_year > 0 else 0.0,
    )


def test_rows_average_each_retriever_and_filter_setting() -> None:
    runs = [
        run("vector", False, 1.0, 0.5, 10.0),
        run("vector", False, 0.0, 0.0, 30.0),
        run("vector", True, 1.0, 1.0, 20.0),
    ]
    rows = {(r.retriever, r.filtered): r for r in aggregate(runs)}
    unfiltered = rows[("vector", False)]
    assert unfiltered.questions == 2
    assert unfiltered.mrr_text == pytest.approx(0.5) and unfiltered.mrr_year == pytest.approx(0.25)
    assert unfiltered.recall10_text == pytest.approx(0.5)
    assert unfiltered.median_latency_ms == pytest.approx(20.0)
    assert unfiltered.collapsed == 2
    assert rows[("vector", True)].mrr_year == pytest.approx(1.0)


def test_the_report_has_both_scores_settings_and_the_question_table() -> None:
    rows = aggregate([run("hybrid", False, 1.0, 0.5, 12.0), run("hybrid", True, 1.0, 1.0, 9.0)])
    text = render_report(
        rows,
        questions=[("ret-001", "AAPL", 2025, "7", 2, "How did Apple's phone revenue change?")],
        settings={"embedding model": "text-embedding-3-small", "RRF constant": "60"},
        notes=["Query embeddings: 40 questions, 600 tokens, $0.000012."],
    )
    assert "| hybrid | none |" in text and "| hybrid | company + year |" in text
    assert "text found" in text and "right year" in text
    assert "RRF constant" in text and "$0.000012" in text
    assert "| ret-001 | AAPL | 2025 | 7 | 2 |" in text
