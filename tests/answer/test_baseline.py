"""The plain-RAG baseline: prompt, citations, abstaining, uncited figures (all fakes)."""

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from filingcheck.answer.baseline import (
    ABSTAIN,
    MAX_TOKENS,
    Answer,
    answer_question,
    is_abstain,
    passage_header,
    stream_answer,
)
from filingcheck.answer.citations import (
    cited_numbers,
    has_uncited_claims,
    normalize_text,
    parse_citations,
)
from filingcheck.answer.examples import HEADER, render_examples, run_examples
from filingcheck.answer.run import format_answer, settings_line
from filingcheck.llm import Completion, FakeChat, IncompleteAnswer, describe_settings
from filingcheck.retrieval import Hit, SearchResult


def hit(n: int, ticker: str = "WMT", year: int = 2025, item: str = "1A") -> Hit:
    return Hit(
        chunk_id=100 + n,
        ticker=ticker,
        fiscal_year=year,
        period_end=date(2025, 1, 31),
        item=item,
        text=f"Passage {n}: " + "x" * 300,
        score=1.0 / n,
        source_url=f"https://www.sec.gov/doc{n}.htm",
    )


HITS = [hit(1), hit(2), hit(3), hit(4, item="7")]


class FakeRetriever:
    name = "hybrid"

    def __init__(self, hits: list[Hit] = HITS, degraded: bool = False) -> None:
        self.hits = hits
        self.degraded = degraded
        self.calls: list[dict[str, Any]] = []

    def search(
        self,
        query: str,
        *,
        ticker: str | None = None,
        fiscal_year: int | None = None,
        items: list[str] | None = None,
        k: int = 10,
    ) -> SearchResult:
        self.calls.append({"query": query, "ticker": ticker, "fiscal_year": fiscal_year, "k": k})
        return SearchResult(hits=self.hits[:k], retriever=self.name, degraded=self.degraded)


def ask(reply: str, retriever: FakeRetriever | None = None, **filters: Any) -> Answer:
    return answer_question(
        "What are Walmart's main risks in Mexico?",
        retriever=retriever or FakeRetriever(),
        model=FakeChat([reply]),
        **filters,
    )


# ---------------------------------------------------------------- the prompt


def test_the_passage_header_names_the_company_fiscal_year_its_end_date_and_item() -> None:
    assert passage_header(hit(1)) == "WMT, fiscal year 2025 (ended 2025-01-31), Item 1A"
    undated = hit(1).model_copy(update={"period_end": None})
    assert passage_header(undated) == "WMT, fiscal year 2025, Item 1A"


def test_the_model_sees_numbered_passages_with_headers_and_the_question() -> None:
    model = FakeChat(["Peso swings [1]."])
    answer_question("Risks in Mexico?", retriever=FakeRetriever(), model=model)
    call = model.calls[0]
    system, user = call["messages"]
    assert system["role"] == "system" and ABSTAIN in system["content"]
    assert "[n]" in system["content"] and "fiscal year" in system["content"]
    assert user["role"] == "user"
    assert "[1] WMT, fiscal year 2025 (ended 2025-01-31), Item 1A\nPassage 1:" in user["content"]
    assert "[4] WMT, fiscal year 2025 (ended 2025-01-31), Item 7\n" in user["content"]
    assert user["content"].rstrip().endswith("Question: Risks in Mexico?")
    assert call["max_tokens"] == MAX_TOKENS == 700 and call["temperature"] is None


def test_filters_and_k_reach_the_retriever() -> None:
    retriever = FakeRetriever()
    ask("Peso swings [1].", retriever, ticker="WMT", fiscal_year=2025, k=3)
    assert retriever.calls == [
        {
            "query": "What are Walmart's main risks in Mexico?",
            "ticker": "WMT",
            "fiscal_year": 2025,
            "k": 3,
        }
    ]
    default = FakeRetriever()
    ask("Peso swings [1].", default)
    assert default.calls[0]["k"] == 8 and default.calls[0]["ticker"] is None


# ---------------------------------------------------------------- citations


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Peso swings are a risk [2].", [102]),
        ("Two risks [1, 3].", [101, 103]),
        ("Two risks [1][3].", [101, 103]),
        ("Three risks [1-3].", [101, 102, 103]),
        ("Three risks [1–3].", [101, 102, 103]),  # noqa: RUF001 (an en dash, as models write it)
        ("Risks [3] and more risks [1] and again [3].", [103, 101]),
        ("A passage that does not exist [9], and one that does [4].", [104]),
        ("No citation at all.", []),
    ],
)
def test_citations_are_parsed_in_every_form_and_unknown_numbers_are_dropped(
    text: str, expected: list[int]
) -> None:
    assert [c.chunk_id for c in parse_citations(text, HITS)] == expected


def test_a_citation_carries_where_the_passage_came_from_and_a_short_quote() -> None:
    (citation,) = parse_citations("Risk [4].", HITS)
    assert (citation.ticker, citation.fiscal_year, citation.item) == ("WMT", 2025, "7")
    assert citation.source_url == "https://www.sec.gov/doc4.htm"
    assert citation.quote == HITS[3].text[:200] and len(citation.quote) == 200


# ---------------------------------------------------------------- abstaining


@pytest.mark.parametrize(
    "text",
    [
        "I can't find this in the filings I have.",
        "I can\u2019t find this in the filings I have.",  # a curly apostrophe
        "**I can't find this in the filings I have.**",
        "  i can't find this in the filings i have  ",
        "_I can't find this in the filings I have_!",
        "`I can't find this in the filings I have.`",
    ],
)
def test_the_abstain_sentence_is_recognised_through_formatting(text: str) -> None:
    assert is_abstain(text)
    answer = ask(text)
    assert answer.abstained and answer.citations == [] and not answer.has_uncited_claims


def test_an_abstain_sentence_followed_by_more_text_is_not_an_abstain() -> None:
    text = "I can't find this in the filings I have. Revenue was $5 billion [1]."
    assert not is_abstain(text)
    answer = ask(text)
    assert not answer.abstained and [c.chunk_id for c in answer.citations] == [101]


# ---------------------------------------------------------------- uncited figures


@pytest.mark.parametrize(
    "text",
    [
        "Walmart's fiscal year 2025 ended on January 31, 2025.",
        "In fiscal 2025 Walmart listed currency risk in Mexico.",
        "The period ended 2025-01-31, as the FY 2025 report says.",
        "See Item 7 and Note 8 of the 10-K; the 10-Q and 8-K say more.",
        "Walmart filed its FY2025 10-K; COVID-19 affected Q3.",
        "Revenue was $2.1 billion [3].",
        "Revenue was $2.1 billion. [3]",
        "Main risks:\n1. Peso swings cut sales by 5% [1].\n2) Regulation costs $40 million [2].",
        "(a) Peso swings cut sales by 2% [1].\n(b) Tariffs [2].",
        "Net sales of $121.9 billion came from outside the U.S. Walmart International segment [2].",
        "Walmart Inc. reported $648.1 billion of revenue, i.e. approx. most of it [1].",
        "Items 1A and 7A cover this.",
    ],
)
def test_years_dates_forms_labels_and_cited_figures_are_not_flagged(text: str) -> None:
    assert not has_uncited_claims(text)


@pytest.mark.parametrize(
    "text",
    [
        "$2.1 billion of revenue came from Mexico.",
        "Mexico was 13% of net sales.",
        "Peso swings are a risk [1]. Sales in Mexico fell by $3 billion.",
        "Main risks:\n1. Peso swings cut sales by 5% [1].\n2. Sales fell 3% in Mexico.",
        "Revenue grew to 2,025 million dollars.",
    ],
)
def test_a_figure_without_a_citation_in_its_sentence_is_flagged(text: str) -> None:
    assert has_uncited_claims(text)


def test_an_answer_reports_whether_it_has_uncited_figures() -> None:
    assert ask("Mexico was 13% of net sales.").has_uncited_claims
    assert not ask("Mexico was 13% of net sales [1].").has_uncited_claims


# ---------------------------------------------------------------- the answer record


def test_the_answer_records_model_retriever_usage_cost_and_degraded() -> None:
    reply = Completion(
        text="Peso swings [1].",
        prompt_tokens=1200,
        completion_tokens=80,
        model="groq:openai/gpt-oss-20b",
        latency_ms=850.0,
        cost_usd=0.000114,
        finish_reason="stop",
    )
    answer = answer_question("Q?", retriever=FakeRetriever(degraded=True), model=FakeChat([reply]))
    assert answer.text == "Peso swings [1]." and answer.model_used == "groq:openai/gpt-oss-20b"
    assert answer.retriever_name == "hybrid" and answer.degraded
    assert answer.usage == {"prompt_tokens": 1200, "completion_tokens": 80}
    assert answer.cost_usd == 0.000114 and answer.finish_reason == "stop"
    assert answer.latency_ms >= 0 and not answer.abstained


def test_a_normal_search_gives_an_answer_that_is_not_degraded() -> None:
    assert not ask("Peso swings [1].").degraded


# ---------------------------------------------------------------- docs/baseline_examples.md


def test_the_examples_file_opens_with_the_warning_then_the_date_and_settings() -> None:
    answer = ask("Peso swings are a risk [1].")
    text = render_examples(
        [("trap-002", "What was Walmart's revenue for 2025?", answer)],
        settings="model groq:openai/gpt-oss-20b, temperature 0.6",
        run_date=date(2026, 11, 2),
    )
    lines = text.splitlines()
    assert lines[0] == HEADER
    assert HEADER == (
        "Week 2 baseline: plain RAG, no agent, no checks. "
        "These answers are not graded and may be wrong."
    )
    assert "2026-11-02" in text and "model groq:openai/gpt-oss-20b, temperature 0.6" in text
    assert "What was Walmart's revenue for 2025?" in text
    assert "Peso swings are a risk [1]." in text
    assert "https://www.sec.gov/doc1.htm" in text and "fake:chat" in text


# ---------------------------------------------------------------- settings line and printout


def test_the_settings_line_names_every_model_setting() -> None:
    assert settings_line("groq:openai/gpt-oss-20b", filters="no filters") == (
        "model groq:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, "
        "max_completion_tokens 700; retriever hybrid, k 8, no filters"
    )
    assert describe_settings("openrouter:openai/gpt-oss-20b", 700) == (
        "model openrouter:openai/gpt-oss-20b, temperature 0.6, reasoning effort low, max_tokens 700"
    )
    assert describe_settings("gemini:gemini-3.5-flash-lite", 700) == (
        "model gemini:gemini-3.5-flash-lite, temperature provider default, "
        "reasoning effort provider default, max_tokens 700"
    )


def test_the_printout_shows_cost_degraded_and_the_rate_limit_headers() -> None:
    reply = Completion(
        text="Peso swings [1].",
        prompt_tokens=None,
        completion_tokens=None,
        model="fake:chat",
        latency_ms=1.0,
        cost_usd=None,
        finish_reason="stop",
        rate_limits={"x-ratelimit-limit-tokens": "8000"},
    )
    answer = answer_question("Q?", retriever=FakeRetriever(), model=FakeChat([reply]))
    text = format_answer(answer, reply)
    assert "cost: unknown" in text and "degraded: false" in text
    assert "x-ratelimit-limit-tokens: 8000" in text
    assert "WMT FY2025 Item 1A (chunk 101): https://www.sec.gov/doc1.htm" in text


# ---------------------------------------------------------------- the examples run

EXAMPLES = [
    {"id": "trap-001", "question": "How much net revenue did Morgan report last year?"},
    {"id": "trap-002", "question": "What was Walmart's revenue for 2025?"},
]


def run(tmp_path: Any, retriever: FakeRetriever, model: FakeChat) -> tuple[int, str, Any]:
    printed: list[str] = []
    output = tmp_path / "baseline_examples.md"
    code = run_examples(
        EXAMPLES,
        retriever=retriever,
        model=model,
        settings="model fake:chat",
        output=output,
        run_date=date(2026, 11, 2),
        out=printed.append,
    )
    return code, "\n".join(printed), output


def test_the_examples_run_writes_the_file_when_every_answer_is_normal(tmp_path: Any) -> None:
    code, _, output = run(tmp_path, FakeRetriever(), FakeChat(["A [1].", "B [2]."]))
    assert code == 0 and output.read_text(encoding="utf-8").startswith(HEADER)


def test_a_degraded_answer_stops_the_examples_run_without_writing(tmp_path: Any) -> None:
    code, printed, output = run(tmp_path, FakeRetriever(degraded=True), FakeChat(["A [1]."]))
    assert code == 1 and not output.exists()
    assert "trap-001" in printed and "degraded" in printed


def test_an_incomplete_answer_stops_the_examples_run_and_is_printed(tmp_path: Any) -> None:
    reply = Completion(
        text="Walmart's rev",
        prompt_tokens=1500,
        completion_tokens=700,
        model="groq:openai/gpt-oss-20b",
        latency_ms=900.0,
        cost_usd=0.000323,
        finish_reason="length",
    )
    model = FakeChat(["A [1].", IncompleteAnswer("incomplete answer", reply)])
    code, printed, output = run(tmp_path, FakeRetriever(), model)
    assert code == 1 and not output.exists()
    assert "trap-002" in printed and "finish_reason: length" in printed
    assert "completion 700" in printed and "$0.000323" in printed
    assert "Walmart's rev" in printed


# ---------------------------------------------------------------- dashes and spaces models write

DASHES = (0x2010, 0x2011, 0x2012, 0x2013, 0x2212)
HYPHEN, NB_HYPHEN, FIGURE_DASH, EN_DASH, MINUS = (chr(c) for c in DASHES)
EM_DASH = chr(0x2014)
NBSP, FIGURE_SPACE, THIN_SPACE, NARROW_NBSP = (chr(c) for c in (0x00A0, 0x2007, 0x2009, 0x202F))


def test_unicode_dashes_and_spaces_are_normalized_for_parsing_only() -> None:
    dashes = "".join([HYPHEN, NB_HYPHEN, FIGURE_DASH, EN_DASH, MINUS])
    spaces = "".join([NBSP, FIGURE_SPACE, THIN_SPACE, NARROW_NBSP])
    assert normalize_text(f"a{dashes}b{EM_DASH}c{spaces}d") == "a-----b c    d"
    text = f"Walmart{NB_HYPHEN}Mexico grew{EM_DASH}12%{NARROW_NBSP}[1]."
    answer = ask(text)
    assert answer.text == text and [c.chunk_id for c in answer.citations] == [101]


@pytest.mark.parametrize(
    "text",
    [
        f"Walmart filed its 10{NB_HYPHEN}K.",
        f"COVID{NB_HYPHEN}19 hurt sales.",
        f"Sales grew{EM_DASH}12% in fiscal 2025 [2].",
        f"Sales rose in fiscal 2023{EN_DASH}2025 [1].",
    ],
)
def test_normalized_labels_and_cited_figures_are_not_flagged(text: str) -> None:
    assert not has_uncited_claims(text)


@pytest.mark.parametrize(
    "text",
    [
        f"Sales grew{EM_DASH}12% in fiscal 2025.",
        f"Sales in Mexico changed by {MINUS}3%.",
        f"Mexico was 9.4{NARROW_NBSP}% of net sales.",
    ],
)
def test_normalized_uncited_figures_are_flagged(text: str) -> None:
    assert has_uncited_claims(text)


def test_a_range_written_with_a_non_breaking_hyphen_cites_every_passage() -> None:
    assert [c.chunk_id for c in parse_citations(f"Risks [1{NB_HYPHEN}3].", HITS)] == [101, 102, 103]


# ---------------------------------------------------------------- streaming


def test_a_streamed_answer_yields_text_then_the_full_answer() -> None:
    items = list(
        stream_answer(
            "Q?", retriever=FakeRetriever(degraded=True), model=FakeChat(["Peso swings [1]."])
        )
    )
    texts, final = items[:-1], items[-1]
    assert isinstance(final, Answer) and all(isinstance(t, str) for t in texts)
    assert "".join(str(t) for t in texts) == final.text == "Peso swings [1]."
    assert [c.chunk_id for c in final.citations] == [101] and final.degraded


def test_the_baseline_examples_ignore_the_question_files_company_and_year(tmp_path: Any) -> None:
    retriever = FakeRetriever()
    trap = [{"id": "trap-002", "question": "Walmart 2025?", "company": "WMT", "fiscal_year": 2025}]
    run_examples(
        trap,
        retriever=retriever,
        model=FakeChat(["A [1]."]),
        settings="s",
        output=tmp_path / "out.md",
        run_date=date(2026, 11, 2),
        out=lambda _: None,
    )
    assert (retriever.calls[0]["ticker"], retriever.calls[0]["fiscal_year"]) == (None, None)


# ---------------------------------------------------------------- lenticular brackets

OPEN, CLOSE = chr(0x3010), chr(0x3011)  # the citation brackets gpt-oss sometimes writes


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (f"Peso swings are a risk {OPEN}1{CLOSE}", [101]),
        (f"Two risks {OPEN}1{CLOSE}{OPEN}3{CLOSE}.", [101, 103]),
        (f"Two risks {OPEN}1, 3{CLOSE}.", [101, 103]),
    ],
)
def test_lenticular_bracket_citations_are_read_like_square_ones(
    text: str, expected: list[int]
) -> None:
    assert [c.chunk_id for c in parse_citations(text, HITS)] == expected


def test_a_figure_cited_with_lenticular_brackets_is_not_flagged_and_the_text_is_kept() -> None:
    text = f"Amortization will be $235 million in fiscal 2026{OPEN}1{CLOSE}"
    assert not has_uncited_claims(text)
    answer = ask(text)
    assert answer.text == text and [c.chunk_id for c in answer.citations] == [101]
    assert not answer.has_uncited_claims


# ---------------------------------------------------------------- the rule the page shares

MARKERS = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "citation_markers.json").read_text(
        encoding="utf-8"
    )
)["cases"]


@pytest.mark.parametrize("case", MARKERS, ids=[c["text"] for c in MARKERS])
def test_the_shared_citation_cases_give_the_same_numbers(case: dict[str, Any]) -> None:
    assert cited_numbers(case["text"], case["passages"]) == case["numbers"]


def test_each_citation_carries_the_number_it_has_in_the_answer() -> None:
    citations = parse_citations(f"Risk [4] and [2] and {OPEN}4{CLOSE}.", HITS)
    assert [(c.number, c.chunk_id) for c in citations] == [(4, 104), (2, 102)]


def test_a_citation_that_points_to_no_passage_leaves_the_figure_uncited() -> None:
    assert has_uncited_claims("Sales were $416.2 billion [9].", passages=4)
    assert not has_uncited_claims("Sales were $416.2 billion [4].", passages=4)
    assert has_uncited_claims("Sales were $416.2 billion [F3].", facts=1)
    assert not has_uncited_claims("Sales were $416.2 billion [F1].", facts=1)
    assert not has_uncited_claims("Sales were $416.2 billion [9].")  # without counts: as before
    answer = ask("Peso swings cost $1.3 billion [9].")
    assert answer.citations == [] and answer.has_uncited_claims
