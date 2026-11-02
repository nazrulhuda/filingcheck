"""`make examples`: the cached example answers, from a question file that can be swapped."""

import json
from pathlib import Path

from filingcheck.app.examples import load_example_questions, refresh_examples
from filingcheck.app.store import ExampleAnswer, MemoryStore
from filingcheck.llm import FakeChat
from tests.answer.test_baseline import FakeRetriever

QUESTIONS = [
    {"id": "demo-001", "question": "What are Walmart's main risks in Mexico?"},
    {"id": "demo-002", "question": "Who audits Apple?"},
]


def refresh(store: MemoryStore, model: FakeChat, degraded: bool = False) -> tuple[int, str]:
    printed: list[str] = []
    code = refresh_examples(
        QUESTIONS,
        retriever=FakeRetriever(degraded=degraded),
        model=model,
        store=store,
        out=printed.append,
    )
    return code, "\n".join(printed)


def test_the_examples_replace_the_cached_answers() -> None:
    old = ExampleAnswer(question="Old question?", answer={"text": "old"})
    store = MemoryStore(examples=[old])
    code, _ = refresh(store, FakeChat(["Peso swings [1].", "Deloitte? [2]."]))
    assert code == 0
    saved = store.examples()
    assert [e.question for e in saved] == [q["question"] for q in QUESTIONS]
    assert saved[0].answer["text"] == "Peso swings [1]." and saved[0].answer["citations"]


def test_a_degraded_answer_leaves_the_cached_answers_untouched(tmp_path: Path) -> None:
    old = ExampleAnswer(question="Old question?", answer={"text": "old"})
    store = MemoryStore(examples=[old])
    code, printed = refresh(store, FakeChat(["Peso swings [1]."]), degraded=True)
    assert code == 1 and store.examples() == [old] and "demo-001" in printed


def test_the_question_file_is_read_from_any_path(tmp_path: Path) -> None:
    path = tmp_path / "demo.jsonl"
    path.write_text("".join(json.dumps(q) + "\n\n" for q in QUESTIONS), encoding="utf-8")
    assert load_example_questions(path) == QUESTIONS


def test_page_examples_are_searched_with_their_ticker_and_fiscal_year() -> None:
    retriever = FakeRetriever()
    store = MemoryStore()
    page = {"id": "page-001", "question": "Risks in Mexico?", "ticker": "WMT", "fiscal_year": 2026}
    model = FakeChat(["Peso [1]."])
    refresh_examples([page], retriever=retriever, model=model, store=store, out=print)
    assert (retriever.calls[0]["ticker"], retriever.calls[0]["fiscal_year"]) == ("WMT", 2026)
    (saved,) = store.examples()
    assert (saved.ticker, saved.fiscal_year) == ("WMT", 2026)


def test_the_page_examples_file_holds_six_questions_with_a_pinned_filing_each() -> None:
    repo = Path(__file__).resolve().parents[2]
    pinned = {
        (f["ticker"], f["fiscal_year"])
        for f in json.loads((repo / "data" / "manifest.json").read_text(encoding="utf-8"))[
            "filings"
        ]
    }
    retrieval = {
        q["id"]: q for q in load_example_questions(repo / "eval" / "questions" / "retrieval.jsonl")
    }
    page = load_example_questions(repo / "eval" / "questions" / "page_examples.jsonl")
    assert [q["id"] for q in page] == [
        "ret-008",
        "ret-024",
        "ret-025",
        "ret-040",
        "ret-016",
        "ret-010",
    ]
    for q in page:
        assert set(q) == {"id", "question", "ticker", "fiscal_year"}
        assert (q["ticker"], q["fiscal_year"]) in pinned
        source = retrieval[q["id"]]
        assert (q["question"], q["ticker"], q["fiscal_year"]) == (
            source["question"],
            source["ticker"],
            source["fiscal_year"],
        )
