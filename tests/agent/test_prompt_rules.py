"""The prompt-rules arm: the checks' rules written into the system prompt, built from their data."""

import inspect
import re
from typing import Any

import pytest

from filingcheck.agent import SYSTEM_PROMPT, run_agent
from filingcheck.agent.prompt_rules import RULE_LINES, expand, rules_block, system_prompt
from filingcheck.checks import CHECKS_BY_TOOL, SEARCH_CHECKS, reference_data
from filingcheck.checks import company as company_module
from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult
from filingcheck.checks.fiscal_year import (
    MONTH_NAMES,
    RELATIVE,
    FiscalYearCheck,
    SearchYearCheck,
)
from filingcheck.checks.metric import QUARTER_RE, SUPPORTED, UNSUPPORTED_RE
from filingcheck.checks.segment import EXCLUDED_BEFORE_RE, INCLUDE_RE
from filingcheck.checks.units import SCALES
from filingcheck.facts.metrics import METRICS
from filingcheck.llm import FakeChat
from tests.agent.test_agent import apple_deps

DATA = reference_data()
BLOCK = rules_block(**DATA)
COMPANIES = DATA["companies"]
MANIFEST = DATA["manifest"]


def line_with(text: str) -> str:
    [line] = [line for line in BLOCK.splitlines() if text in line]
    return line


def company_line(name: str, ticker: str) -> str:
    [line] = [line for line in BLOCK.splitlines() if line.startswith(f"- {name} ({ticker}):")]
    return line


# ---------------------------------------------------------------- one instruction per check


def test_every_check_in_the_chain_has_its_instruction_in_the_block() -> None:
    """Keyed on the tool and the class: the search-year check shares the name fiscal_year."""
    chain = {(tool, type(check)) for tool, checks in CHECKS_BY_TOOL.items() for check in checks}
    assert set(RULE_LINES) == chain  # an instruction for every check, and none for no check
    for key in chain:
        assert RULE_LINES[key] in BLOCK, key
    assert len(chain) == 6


def test_the_search_year_check_has_its_own_instruction() -> None:
    fact_year = RULE_LINES[("get_financial_fact", FiscalYearCheck)]
    search_year = RULE_LINES[("search_filings", SearchYearCheck)]
    assert fact_year != search_year
    assert "search_filings" in search_year and "latest fiscal year" in search_year


def test_a_check_added_later_without_an_instruction_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class NewCheck:
        name = "fiscal_year"  # an existing name: the block must key on the class

        def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
            raise NotImplementedError

    monkeypatch.setitem(CHECKS_BY_TOOL, "search_filings", (*SEARCH_CHECKS, NewCheck()))
    with pytest.raises(ValueError, match="NewCheck"):
        rules_block(**DATA)


# ---------------------------------------------------------------- the checks' data, all of it


def test_every_company_with_its_names_segments_year_end_and_years() -> None:
    assert len(COMPANIES) == 25
    assert "The 25 companies in the dataset" in BLOCK
    for company in COMPANIES:
        line = company_line(company.name, company.ticker)
        for name in company.aliases:
            assert name in line, (company.ticker, name)
        for segment in company.segments:
            assert segment in line, (company.ticker, segment)
        assert f"fiscal year ends in {MONTH_NAMES[company.fiscal_year_end - 1]}" in line
        years = sorted(f.fiscal_year for f in MANIFEST.filings if f.ticker == company.ticker)
        assert len(years) == 3
        for year in years:
            assert f"fiscal {year} (" in line, (company.ticker, year)
        assert line.count("the latest") == 1
        assert re.search(rf"fiscal {years[-1]} \([^)]*; the latest\)", line), company.ticker


def test_the_periods_are_the_checks_own() -> None:
    line = company_line("Walmart Inc.", "WMT")
    assert "fiscal 2024 (year ended Jan 31, 2024)" in line
    assert "fiscal 2025 (Feb 1, 2024 to Jan 31, 2025)" in line
    assert "fiscal 2026 (Feb 1, 2025 to Jan 31, 2026; the latest)" in line


def test_every_name_that_fits_two_companies() -> None:
    lookalikes: dict[str, list[str]] = {}
    for company in COMPANIES:
        for word in company.lookalikes:
            lookalikes.setdefault(word, []).append(company.ticker)
    assert lookalikes == {"Morgan": ["JPM", "MS"]}
    line = line_with("fit two or more companies")
    for word, tickers in lookalikes.items():
        assert f'"{word}"' in line
        for ticker in tickers:
            assert f"({ticker})" in line


def test_every_company_the_check_knows_is_not_covered() -> None:
    line = line_with("not in the dataset:")
    assert DATA["not_covered"]
    for name in DATA["not_covered"]:
        assert name in line, name


def test_the_13_metrics_and_the_words_the_metric_check_maps() -> None:
    line = line_with("The 13 metrics")
    for metric in METRICS:
        assert metric in line
    assert "annual figures only" in line and "company totals only" in line
    for pattern, metric in SUPPORTED:
        words = ", ".join(f'"{w}"' for w in expand(pattern))
        assert f"- {words}: {metric}" in BLOCK, pattern
    assert '"earnings per share"' in BLOCK


def test_the_quarter_and_unsupported_words_are_in_the_metric_instruction() -> None:
    from filingcheck.checks.metric import MetricCheck

    line = RULE_LINES[("get_financial_fact", MetricCheck)]
    for word in expand(QUARTER_RE.pattern) + expand(UNSUPPORTED_RE.pattern):
        assert f'"{word}"' in line, word
    assert "the dataset has annual figures only (10-K); no quarterly periods" in line
    assert "is not one of the 13 metrics the data holds" in line


def test_the_relative_words_are_in_the_fiscal_year_instruction() -> None:
    line = RULE_LINES[("get_financial_fact", FiscalYearCheck)]
    for pattern, _, _ in RELATIVE:
        for word in expand(pattern):
            assert f'"{word}"' in line, word
    assert "ask the user which fiscal year" in line
    assert "has no 10-K for fiscal" in line


def test_the_units_instruction_names_every_scale() -> None:
    from filingcheck.checks.units import UnitsCheck

    line = RULE_LINES[("get_financial_fact", UnitsCheck)]
    for scale in SCALES.values():
        assert scale in line
    assert "goes next to the raw value" in line


def test_the_segment_instruction_has_the_include_and_exclude_words() -> None:
    from filingcheck.checks.segment import SegmentCheck

    line = RULE_LINES[("get_financial_fact", SegmentCheck)]
    assert "the fact tool returns company totals only" in line
    assert "use search_filings for the text or say so" in line
    for word in expand(INCLUDE_RE.pattern):
        assert f'"{word}"' in line, word
    for word in ("excluding", "without", "not counting", "minus", "other than", "except", "ex-"):
        assert f'"{word}"' in line, word
    assert '"excluding the"' not in line  # "the" after the word is not a word of its own
    assert EXCLUDED_BEFORE_RE.search("excluding ")


def test_the_company_instruction_is_in_the_checks_words() -> None:
    from filingcheck.checks.company import CompanyCheck

    line = RULE_LINES[("get_financial_fact", CompanyCheck)]
    assert "ask the user which one" in line
    # The company check's reject reason ("X is not one of the 25 companies in the dataset").
    # Block version 2 reworded this line on a wrong premise and was withdrawn at the Day 39
    # review: the final run uses version 1, the block as the rule built it.
    assert "say it is not one of the 25 companies in the dataset" in line
    assert '{verb} the 25 companies in the dataset"' in inspect.getsource(company_module)


def test_the_block_is_version_1_byte_for_byte() -> None:
    """The block the final run uses is version 1, as run on the development sets."""
    import hashlib
    from pathlib import Path

    v1 = Path("eval/results/2026-11-14_agent-prompt-rules_block.txt").read_bytes()
    assert hashlib.sha256(v1).hexdigest() == (
        "5af14ef8bb31de6c9f0f8f064c2abfe479c88cc96d23c86c318d6e626d8bc806"
    )
    assert (BLOCK + "\n").encode("utf-8") == v1


def test_the_block_ends_with_the_fiscal_year_and_period_rule() -> None:
    assert BLOCK.splitlines()[-1] == (
        "- State the fiscal year and the period for every figure, as in fiscal 2025 "
        "(Feb 1, 2024 to Jan 31, 2025)."
    )


def test_the_block_is_the_same_every_time() -> None:
    assert rules_block(**reference_data()) == BLOCK


# ---------------------------------------------------------------- the phrases a pattern matches


@pytest.mark.parametrize(
    ("pattern", "phrases"),
    [
        ("(?:net )?revenues?", ["revenue", "revenues", "net revenue", "net revenues"]),
        ("Q[1-4]", ["Q1", "Q2", "Q3", "Q4"]),
        ("H[12]", ["H1", "H2"]),
        ("half[- ]year", ["half-year", "half year"]),
        ("market cap(?:italization)?", ["market cap", "market capitalization"]),
        (r"\b(?:a|b c)\b", ["a", "b c"]),
        (r"not\s+counting", ["not counting"]),
        (r"ex-\s*$", ["ex-"]),
    ],
)
def test_expand(pattern: str, phrases: list[str]) -> None:
    assert expand(pattern) == phrases


@pytest.mark.parametrize("pattern", ["a{2}", "a.b", r"\d", "(a)"])
def test_expand_refuses_what_it_cannot_list(pattern: str) -> None:
    with pytest.raises(ValueError):
        expand(pattern)


def test_every_listed_phrase_is_matched_by_its_checks_pattern() -> None:
    patterns: list[Any] = [QUARTER_RE, UNSUPPORTED_RE, INCLUDE_RE]
    patterns += [re.compile(rf"\b(?:{p})\b", re.IGNORECASE) for p, _ in SUPPORTED]
    patterns += [re.compile(rf"\b(?:{p})\b", re.IGNORECASE) for p, _, _ in RELATIVE]
    for regex in patterns:
        phrases = expand(regex.pattern)
        assert phrases
        for phrase in phrases:
            assert regex.fullmatch(phrase), (regex.pattern, phrase)


# ---------------------------------------------------------------- the prompt the agent sends


def test_without_rules_the_prompt_is_byte_identical_to_the_frozen_one() -> None:
    assert system_prompt(None) == SYSTEM_PROMPT
    chat = FakeChat(["I can't find that in the filings."])
    run_agent("What were Apple's risk factors?", model=chat, deps=apple_deps())
    assert chat.calls[0]["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert chat.calls[0]["messages"][0]["content"].encode() == SYSTEM_PROMPT.encode()


def test_with_rules_the_block_goes_after_the_frozen_prompt() -> None:
    assert system_prompt(BLOCK) == SYSTEM_PROMPT + "\n\n" + BLOCK
    chat = FakeChat(["I can't find that in the filings."])
    answer = run_agent(
        "What were Apple's risk factors?", model=chat, deps=apple_deps(), rules=BLOCK
    )
    assert chat.calls[0]["messages"][0] == {
        "role": "system",
        "content": SYSTEM_PROMPT + "\n\n" + BLOCK,
    }
    assert answer.checks is False and answer.overrides == []
