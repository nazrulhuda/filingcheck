"""The company check, on the real company list: mentions, lookalikes, the page filter, the
companies outside the dataset, and the override log's content for each outcome."""

from typing import Any

import pytest

from filingcheck.checks import CheckContext, CheckedCall
from filingcheck.checks.company import CompanyCheck, find_mentions
from filingcheck.ingest.companies import load_companies, load_not_covered
from filingcheck.paths import DATA_DIR

COMPANIES = load_companies(DATA_DIR / "companies.yaml")
NOT_COVERED = load_not_covered(DATA_DIR / "companies.yaml")
TICKERS = sorted(c.ticker for c in COMPANIES)
CHECK = CompanyCheck()


def run(question: str, ticker: str, page_filter: str | None = None) -> Any:
    call = CheckedCall(
        "get_financial_fact", {"ticker": ticker, "fiscal_year": 2025, "metric": "revenue"}
    )
    context = CheckContext(
        question=question,
        ticker=page_filter,
        fiscal_year=None,
        companies=COMPANIES,
        not_covered=NOT_COVERED,
    )
    return CHECK.run(call, context)


def mentions(question: str) -> list[tuple[str, frozenset[str]]]:
    return [(m.text, m.tickers) for m in find_mentions(question, COMPANIES)]


# ---------------------------------------------------------------- the data the check relies on


def test_morgan_is_a_lookalike_of_both_jpmorgan_and_morgan_stanley() -> None:
    by_ticker = {c.ticker: c for c in COMPANIES}
    assert "Morgan" in by_ticker["JPM"].lookalikes and "Morgan" in by_ticker["MS"].lookalikes


def test_the_spec_words_are_aliases_of_one_company_each() -> None:
    expected = {
        "Chase": "JPM",
        "Citi": "C",
        "Google": "GOOGL",
        "Facebook": "META",
        "Amex": "AXP",
        "Cap One": "COF",
        "JNJ": "JNJ",
        "Wal-Mart": "WMT",
        "NVIDIA": "NVDA",
        "Coke": "KO",
        "S&P": "SPGI",
        "Moody's": "MCO",
    }
    for word, ticker in expected.items():
        owners = [c.ticker for c in COMPANIES if word in c.aliases or word == c.ticker]
        assert owners == [ticker], word


def test_the_not_covered_list_holds_the_well_known_names_outside_the_dataset() -> None:
    for name in (
        "Tesla",
        "Bank of America",
        "Wells Fargo",
        "Berkshire Hathaway",
        "Visa",
        "PayPal",
        "Intel",
        "AMD",
        "Oracle",
        "Salesforce",
        "Adobe",
        "Cisco",
        "Broadcom",
        "Qualcomm",
        "Boeing",
        "Disney",
        "ExxonMobil",
        "Chevron",
        "Home Depot",
        "Target",
        "Procter & Gamble",
        "PepsiCo",
        "McDonald's",
        "Uber",
    ):
        assert name in NOT_COVERED, name


# ---------------------------------------------------------------- mentions


def test_names_tickers_and_aliases_are_found_whole_word_and_case_insensitive() -> None:
    assert mentions("What were Apple's total net sales?") == [("Apple", frozenset({"AAPL"}))]
    assert mentions("APPLE revenue") == [("APPLE", frozenset({"AAPL"}))]
    assert mentions("Revenue of Johnson & Johnson in 2025") == [
        ("Johnson & Johnson", frozenset({"JNJ"}))
    ]
    assert mentions("How did S&P Global's revenue grow?") == [("S&P Global", frozenset({"SPGI"}))]
    curly = "Moody" + chr(0x2019) + "s net income"  # the curly apostrophe people type
    assert mentions(curly) == [("Moody's", frozenset({"MCO"}))]
    assert mentions("coke's revenue") == [("coke", frozenset({"KO"}))]
    assert mentions("Pineapple revenue") == []  # not a whole word


def test_a_ticker_or_short_initialism_must_be_written_as_typed() -> None:
    assert mentions("What was MS's net revenue in 2025?") == [("MS", frozenset({"MS"}))]
    assert mentions("What did it cost in 2025?") == []  # COST is Costco only in capitals
    assert mentions("ms word") == []
    assert mentions("ma and pa") == []
    assert mentions("Costco's revenue") == [("Costco", frozenset({"COST"}))]


def test_the_longest_match_wins_so_morgan_stanley_and_jp_morgan_are_not_ambiguous() -> None:
    assert mentions("Morgan Stanley's net revenue") == [("Morgan Stanley", frozenset({"MS"}))]
    assert mentions("JP Morgan's net revenue") == [("JP Morgan", frozenset({"JPM"}))]
    assert mentions("JPMorgan's net revenue") == [("JPMorgan", frozenset({"JPM"}))]
    assert mentions("JPMorgan Chase net revenue") == [("JPMorgan Chase", frozenset({"JPM"}))]


def test_a_lookalike_word_alone_is_a_mention_of_every_company_it_names() -> None:
    assert mentions("How much net revenue did Morgan report last year?") == [
        ("Morgan", frozenset({"JPM", "MS"}))
    ]


# ---------------------------------------------------------------- the rules


def test_rule_a_one_company_named_and_the_argument_matches_passes() -> None:
    result = run("What were Apple's total net sales in fiscal 2025?", "AAPL")
    assert result.outcome == "pass"
    assert result.arguments["ticker"] == "AAPL"
    record = result.override
    assert (record.check, record.argument, record.sent, record.used) == (
        "company",
        "ticker",
        "AAPL",
        "AAPL",
    )
    assert "Apple Inc. (AAPL)" in record.reason


def test_rule_b_one_company_named_and_another_argument_is_repaired() -> None:
    result = run("What were Apple's total net sales in fiscal 2025?", "MSFT")
    assert result.outcome == "repair"
    assert result.arguments["ticker"] == "AAPL"
    assert result.arguments["metric"] == "revenue"  # the other arguments are untouched
    record = result.override
    assert (record.sent, record.used) == ("MSFT", "AAPL")
    assert "Apple Inc. (AAPL)" in record.reason and "MSFT" in record.reason


def test_rule_c_an_ambiguous_mention_is_rejected_with_the_options() -> None:
    for sent in ("MS", "JPM", "AAPL"):
        result = run("How much net revenue did Morgan report last year?", sent)
        assert result.outcome == "reject", sent
        assert result.override.options == ["JPM", "MS"]
        assert result.override.used is None and result.override.sent == sent
        assert "ambiguous" in result.override.reason
        assert "JPMorgan Chase & Co. (JPM)" in result.override.reason
        assert "Morgan Stanley (MS)" in result.override.reason
        assert "ask the user" in result.override.reason


def test_an_ambiguous_word_is_settled_by_an_unambiguous_mention_of_one_candidate() -> None:
    result = run("Compare JPMorgan with Morgan's results", "JPM")
    assert result.outcome == "pass"
    result = run("Compare JPMorgan with Morgan's results", "MS")
    assert result.outcome == "repair" and result.arguments["ticker"] == "JPM"


def test_morgan_stanley_is_not_ambiguous() -> None:
    assert run("What was Morgan Stanley's net revenue in 2025?", "MS").outcome == "pass"
    result = run("What was Morgan Stanley's net revenue in 2025?", "JPM")
    assert result.outcome == "repair" and result.arguments["ticker"] == "MS"


def test_a_typed_ticker_wins_so_ms_is_morgan_stanley() -> None:
    assert run("What was MS's revenue in 2025?", "MS").outcome == "pass"
    result = run("What was MS's revenue in 2025?", "MSFT")
    assert result.outcome == "repair" and result.arguments["ticker"] == "MS"


def test_rule_d_a_comparison_passes_either_named_company_and_rejects_a_third() -> None:
    question = "Compare Apple's and Microsoft's revenue in fiscal 2025."
    assert run(question, "AAPL").outcome == "pass"
    assert run(question, "MSFT").outcome == "pass"
    result = run(question, "WMT")
    assert result.outcome == "reject"
    assert result.override.options == ["AAPL", "MSFT"]
    assert "WMT" in result.override.reason


def test_a_clearly_named_company_passes_even_next_to_an_ambiguous_one() -> None:
    question = "Compare Apple with Morgan."
    assert run(question, "AAPL").outcome == "pass"
    result = run(question, "MS")
    assert result.outcome == "reject" and result.override.options == ["JPM", "MS"]


def test_rule_e_no_company_named_passes_with_a_log_line_or_follows_the_page_filter() -> None:
    result = run("What was revenue in 2025?", "WMT")
    assert result.outcome == "pass"
    assert "no company named" in result.override.reason
    assert run("What was revenue in 2025?", "WMT", page_filter="WMT").outcome == "pass"
    result = run("What was revenue in 2025?", "AAPL", page_filter="WMT")
    assert result.outcome == "repair" and result.arguments["ticker"] == "WMT"
    assert "selected WMT" in result.override.reason and "AAPL" in result.override.reason


def test_a_named_company_that_differs_from_the_page_filter_is_rejected_with_both() -> None:
    result = run("What was Apple's revenue in 2025?", "AAPL", page_filter="WMT")
    assert result.outcome == "reject"
    assert result.override.options == ["AAPL", "WMT"]
    assert "WMT" in result.override.reason and "Apple Inc. (AAPL)" in result.override.reason
    # The named company equal to the filter is simply rule (a).
    assert run("What was Apple's revenue in 2025?", "AAPL", page_filter="AAPL").outcome == "pass"


def test_a_company_outside_the_dataset_is_rejected_by_name_with_the_25_listed() -> None:
    result = run("What was Tesla's revenue in 2025?", "AAPL")
    assert result.outcome == "reject"
    assert result.override.reason.startswith("Tesla is not one of the 25 companies")
    assert result.override.options == TICKERS and len(TICKERS) == 25
    result = run("Compare Bank of America and Wells Fargo.", "JPM")
    assert result.outcome == "reject"
    assert "Bank of America" in result.override.reason and "Wells Fargo" in result.override.reason


def test_a_named_covered_company_passes_next_to_an_uncovered_one() -> None:
    result = run("Compare Apple's revenue with Tesla's.", "AAPL")
    assert result.outcome == "pass"
    assert "Tesla" in result.override.reason and "not" in result.override.reason
    assert run("Compare Apple's revenue with Tesla's.", "MSFT").outcome == "reject"


@pytest.mark.parametrize(
    "question",
    [
        "what were apple's net sales?",
        "What were APPLE's net sales?",
        "Apple: net sales?",
        "(Apple) net sales",
        "Net sales of Apple, fiscal 2025",
        "Apple Inc.'s net sales",
    ],
)
def test_case_and_punctuation_variants_name_the_same_company(question: str) -> None:
    assert run(question, "AAPL").outcome == "pass"
    assert run(question, "WMT").arguments["ticker"] == "AAPL"


def test_the_check_reads_only_the_ticker_argument_and_leaves_other_tools_alone() -> None:
    result = run("What were Apple's total net sales in fiscal 2025?", "AAPL")
    assert result.override.argument == "ticker"
    assert CHECK.name == "company"
