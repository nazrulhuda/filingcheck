"""`make examples`: the cached example answers, from a question file that can be swapped."""

import json
from pathlib import Path
from typing import Any

import pytest

from filingcheck.app.examples import (
    export_examples,
    load_example_questions,
    refresh_agent_examples,
    refresh_examples,
)
from filingcheck.app.store import ExampleAnswer, MemoryStore
from filingcheck.llm import FakeChat, scripted_tool_calls
from tests.agent.test_agent import cut_off
from tests.agent.test_agent_checks import checked_deps
from tests.answer.test_baseline import FakeRetriever, ask

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


TEXT_IDS = ["ret-008", "ret-024", "ret-040", "ret-016", "ret-010"]
NUMBER_IDS = ["fact-001", "fact-002"]


def test_the_page_examples_file_holds_five_text_and_two_number_questions() -> None:
    repo = Path(__file__).resolve().parents[2]
    questions = repo / "eval" / "questions"
    filings = json.loads((repo / "data" / "manifest.json").read_text(encoding="utf-8"))["filings"]
    pinned = {(f["ticker"], f["fiscal_year"]) for f in filings}
    companies = {f["ticker"] for f in filings}
    retrieval = {q["id"]: q for q in load_example_questions(questions / "retrieval.jsonl")}
    page = load_example_questions(questions / "page_examples.jsonl")
    assert [q["id"] for q in page] == TEXT_IDS + NUMBER_IDS
    for q in page:
        assert set(q) == {"id", "question", "ticker", "fiscal_year"}
        assert q["ticker"] in companies
        # A number question may leave the year open, so the page shows the check resolving it.
        assert q["fiscal_year"] is None or (q["ticker"], q["fiscal_year"]) in pinned
    # The five text questions are the retrieval set's, unchanged.
    for q in page[:5]:
        source = retrieval[q["id"]]
        assert (q["question"], q["ticker"], q["fiscal_year"]) == (
            source["question"],
            source["ticker"],
            source["fiscal_year"],
        )
    # The two number questions were written for the page and are in no evaluation set.
    evaluated = {
        json.loads(line)["question"]
        for path in questions.glob("*.jsonl")
        if path.name != "page_examples.jsonl"
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    plain, relative = page[5:]
    assert plain["question"] not in evaluated and relative["question"] not in evaluated
    assert plain["fiscal_year"] is not None
    assert "last year" in relative["question"] and relative["fiscal_year"] is None


# ---------------------------------------------------------------- make examples-export


def stored(text: str, chunk_ids: list[int], numbered: bool) -> ExampleAnswer:
    answer = ask(text).model_dump()
    answer["citations"] = [
        {"chunk_id": c, "ticker": "WMT", "fiscal_year": 2024, "item": "7A"}
        | {"source_url": "u", "quote": "q"}
        | ({"number": n} if numbered else {})
        for n, c in enumerate(chunk_ids, 1)
    ]
    return ExampleAnswer(question="Q?", ticker="WMT", fiscal_year=2024, answer=answer)


def test_the_export_writes_every_example_with_each_citations_number(tmp_path: Path) -> None:
    store = MemoryStore(examples=[stored("Swaps [3] and rates [1].", [103, 101], numbered=False)])
    path = tmp_path / "examples.json"
    export_examples(store, path)
    (example,) = json.loads(path.read_text(encoding="utf-8"))
    assert (example["question"], example["ticker"], example["fiscal_year"]) == ("Q?", "WMT", 2024)
    numbered = [(c["number"], c["chunk_id"]) for c in example["answer"]["citations"]]
    assert numbered == [(3, 103), (1, 101)]
    assert example["answer"]["text"] == "Swaps [3] and rates [1]."


def test_the_export_names_the_company_each_example_was_asked_with(tmp_path: Path) -> None:
    # The page shows the filters an example was asked with, and builds without the API.
    walmart = stored("Swaps [1].", [101], numbered=True)
    open_question = ExampleAnswer(question="Any?", answer=walmart.answer)
    store = MemoryStore(examples=[walmart, open_question])
    export_examples(store, tmp_path / "examples.json")
    saved = json.loads((tmp_path / "examples.json").read_text(encoding="utf-8"))
    assert [e["company_name"] for e in saved] == ["Walmart Inc.", None]


NET_INCOME = {
    "ticker": "AAPL",
    "fiscal_year": 2025,
    "metric": "net_income",
    "value": "112010000000",
    "unit": "USD",
    "period_start": "2024-09-29",
    "period_end": "2025-09-27",
    "instant": None,
    "concept": "us-gaap:NetIncomeLoss",
    "accession": "a",
    "source_url": "u",
    "decimals": "-6",
    "line_label": "Net income",
    "note": None,
}


def test_the_export_adds_the_number_labels_and_whether_each_line_label_is_standard(
    tmp_path: Path,
) -> None:
    answer = {
        "mode": "agent",
        "text": "Net income was $112,010 million [F1].",
        "citations": [],
        "facts_used": [NET_INCOME],
        "fact_citations": [{"number": 1, "concept": "us-gaap:NetIncomeLoss"}],
        "tool_calls": [],
    }
    store = MemoryStore(examples=[ExampleAnswer(question="Q?", ticker="AAPL", answer=answer)])
    seen: list[str] = []

    def label_answer(stored: dict[str, Any]) -> list[dict[str, Any]]:
        seen.append(stored["text"])
        return [{"figure": "$112,010 million", "label": "verified"}]

    export_examples(store, tmp_path / "examples.json", label_answer=label_answer)
    (example,) = json.loads((tmp_path / "examples.json").read_text(encoding="utf-8"))
    assert seen == [answer["text"]]
    assert example["answer"]["number_labels"] == [
        {"figure": "$112,010 million", "label": "verified"}
    ]
    # Apple prints no wording of its own for net income, so the chip shows the standard name.
    assert example["answer"]["fact_citations"][0]["standard_label"] is True
    assert example["answer"]["text"] == answer["text"]


def test_the_export_fills_each_citations_whole_passage_when_it_was_not_stored(
    tmp_path: Path,
) -> None:
    store = MemoryStore(examples=[stored("Swaps [1].", [101], numbered=True)])
    export_examples(
        store, tmp_path / "examples.json", passage_text=lambda ids: {i: f"text {i}" for i in ids}
    )
    (example,) = json.loads((tmp_path / "examples.json").read_text(encoding="utf-8"))
    assert example["answer"]["citations"][0]["text"] == "text 101"


def test_the_export_refuses_an_answer_whose_markers_do_not_match_its_citations(
    tmp_path: Path,
) -> None:
    store = MemoryStore(examples=[stored("Only one marker [1].", [101, 102], numbered=False)])
    with pytest.raises(ValueError, match="2 citations"):
        export_examples(store, tmp_path / "examples.json")
    assert not (tmp_path / "examples.json").exists()


def test_the_export_keeps_numbers_that_are_already_stored(tmp_path: Path) -> None:
    store = MemoryStore(examples=[stored("A [1] and B [2].", [101, 102], numbered=True)])
    export_examples(store, tmp_path / "examples.json")
    (example,) = json.loads((tmp_path / "examples.json").read_text(encoding="utf-8"))
    assert [c["number"] for c in example["answer"]["citations"]] == [1, 2]


APPLE_PAGE = {
    "id": "page-001",
    "question": "What were Apple's total net sales in fiscal 2025?",
    "ticker": "AAPL",
    "fiscal_year": 2025,
}
APPLE_FACT = {"ticker": "AAPL", "fiscal_year": 2025, "metric": "revenue"}


def test_the_page_examples_are_answered_by_the_agent_with_the_checks_on() -> None:
    old = ExampleAnswer(question="Old question?", answer={"text": "old"})
    store = MemoryStore(examples=[old])
    sales = "Sales were $416,161 million [F1]."
    model = FakeChat([scripted_tool_calls(("get_financial_fact", APPLE_FACT)), sales])
    printed: list[str] = []
    code = refresh_agent_examples(
        [APPLE_PAGE], deps=checked_deps(), model=model, store=store, out=printed.append
    )
    assert code == 0
    (saved,) = store.examples()
    assert (saved.question, saved.ticker, saved.fiscal_year) == (
        APPLE_PAGE["question"],
        "AAPL",
        2025,
    )
    answer = saved.answer
    assert answer["mode"] == "agent" and answer["checks"] is True
    assert [o["check"] for o in answer["overrides"]][:2] == ["company", "fiscal_year"]
    assert answer["fact_citations"][0]["number"] == 1
    # Stored as JSON: the fact's value is a string of digits, the dates are ISO strings.
    json.dumps(answer)
    assert "page-001" in "\n".join(printed)


def test_the_agent_examples_run_with_the_page_filters() -> None:
    store = MemoryStore()
    model = FakeChat(["Nothing to look up."])
    refresh_agent_examples([APPLE_PAGE], deps=checked_deps(), model=model, store=store, out=print)
    user = model.calls[0]["messages"][1]["content"]
    assert "AAPL" in user and "2025" in user


def test_a_cut_off_agent_answer_leaves_the_cached_answers_untouched() -> None:
    old = ExampleAnswer(question="Old question?", answer={"text": "old"})
    store = MemoryStore(examples=[old])
    model = FakeChat([cut_off()])
    printed: list[str] = []
    code = refresh_agent_examples(
        [APPLE_PAGE], deps=checked_deps(), model=model, store=store, out=printed.append
    )
    assert code == 1 and store.examples() == [old] and "page-001" in "\n".join(printed)
