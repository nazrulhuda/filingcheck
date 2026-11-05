"""The metric map and the lookup rules, with an in-memory facts source."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from typing import get_args

import pytest

from filingcheck.facts.lookup import FactResult, FilingRef, TotalFact, lookup
from filingcheck.facts.metrics import METRICS, Metric, candidate_tags

ACC = "0000999999-26-000001"
URL = "https://www.sec.gov/Archives/edgar/data/999999/x/exmp-20251231.htm"
YEAR = (date(2025, 1, 1), date(2025, 12, 31))


class FakeFacts:
    def __init__(
        self,
        facts: list[TotalFact],
        revenue_rule: str = "standard",
        filing: FilingRef | None = None,
    ) -> None:
        self._facts = facts
        self._filing = filing or FilingRef(
            ticker="EXMP",
            fiscal_year=2025,
            accession=ACC,
            period_of_report=date(2025, 12, 31),
            source_url=URL,
            revenue_rule=revenue_rule,
        )
        self.asked: list[tuple[str, tuple[str, ...]]] = []

    def filing(self, ticker: str, fiscal_year: int) -> FilingRef | None:
        if (ticker, fiscal_year) == (self._filing.ticker, self._filing.fiscal_year):
            return self._filing
        return None

    def facts(self, accession: str, concepts: Sequence[str]) -> list[TotalFact]:
        self.asked.append((accession, tuple(concepts)))
        return [f for f in self._facts if f.concept in concepts]


def duration(
    concept: str, value: str, start: date = YEAR[0], end: date = YEAR[1], **over: object
) -> TotalFact:
    fields: dict[str, object] = {
        "concept": concept,
        "value": Decimal(value),
        "unit": "USD",
        "period_start": start,
        "period_end": end,
        "instant": None,
        "decimals": "-6",
        "dimensions": {},
    }
    fields.update(over)
    return TotalFact(**fields)  # type: ignore[arg-type]


def instant(concept: str, value: str, on: date = YEAR[1], **over: object) -> TotalFact:
    fields: dict[str, object] = {
        "concept": concept,
        "value": Decimal(value),
        "unit": "USD",
        "period_start": None,
        "period_end": None,
        "instant": on,
        "decimals": "-6",
        "dimensions": {},
    }
    fields.update(over)
    return TotalFact(**fields)  # type: ignore[arg-type]


# ---------------------------------------------------------------- the metric map


def test_there_are_13_metrics_and_the_question_format_uses_the_same_names() -> None:
    from filingcheck.eval.questions import METRICS as QUESTION_METRICS

    assert len(get_args(Metric)) == 13
    assert set(METRICS) == set(get_args(Metric)) == set(QUESTION_METRICS)
    assert "pretax_income" in METRICS


def test_the_bank_revenue_rule_never_uses_the_contract_revenue_tag() -> None:
    assert candidate_tags("revenue", "bank") == (
        "us-gaap:RevenuesNetOfInterestExpense",
        "us-gaap:Revenues",
    )
    assert candidate_tags("revenue", "standard")[:2] == (
        "us-gaap:Revenues",
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
    )


def test_pretax_income_has_the_two_tags_in_order() -> None:
    assert candidate_tags("pretax_income", "standard") == (
        "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "us-gaap:IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
    )


# ---------------------------------------------------------------- the lookup rules


def test_a_fact_is_returned_with_its_value_unit_period_tag_and_source() -> None:
    source = FakeFacts([duration("us-gaap:Revenues", "1234000000")])
    result = lookup(source, "EXMP", 2025, "revenue")
    assert result == FactResult(
        ticker="EXMP",
        fiscal_year=2025,
        metric="revenue",
        value=Decimal("1234000000"),
        unit="USD",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        instant=None,
        concept="us-gaap:Revenues",
        accession=ACC,
        source_url=URL,
        decimals="-6",
        line_label="Revenues",
        note=None,
    )


def test_a_year_that_is_not_pinned_is_unavailable() -> None:
    source = FakeFacts([duration("us-gaap:Revenues", "1")])
    assert lookup(source, "EXMP", 2024, "revenue") is None
    assert lookup(source, "OTHER", 2025, "revenue") is None
    assert source.asked == []  # nothing else is ever read


def test_the_first_candidate_with_a_fact_wins() -> None:
    source = FakeFacts(
        [
            duration("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "900"),
            duration("us-gaap:Revenues", "1000"),
        ]
    )
    result = lookup(source, "EXMP", 2025, "revenue")
    assert result is not None and (result.concept, result.value) == (
        "us-gaap:Revenues",
        Decimal(1000),
    )
    only_second = FakeFacts(
        [duration("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "900")]
    )
    result = lookup(only_second, "EXMP", 2025, "revenue")
    assert result is not None and result.concept.endswith(
        "RevenueFromContractWithCustomerExcludingAssessedTax"
    )


def test_banks_take_revenue_net_of_interest_expense_and_never_contract_revenue() -> None:
    facts = [
        duration("us-gaap:Revenues", "158104000000"),
        duration("us-gaap:RevenuesNetOfInterestExpense", "158104000001"),
        duration("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", "37218000000"),
    ]
    result = lookup(FakeFacts(facts, "bank"), "EXMP", 2025, "revenue")
    assert result is not None and result.concept == "us-gaap:RevenuesNetOfInterestExpense"
    result = lookup(FakeFacts(facts[:1] + facts[2:], "bank"), "EXMP", 2025, "revenue")
    assert result is not None and result.concept == "us-gaap:Revenues"
    assert lookup(FakeFacts(facts[2:], "bank"), "EXMP", 2025, "revenue") is None


def test_a_quarter_ending_on_the_same_day_is_not_the_year() -> None:
    quarter = duration("us-gaap:Revenues", "300", start=date(2025, 10, 1))
    assert lookup(FakeFacts([quarter]), "EXMP", 2025, "revenue") is None
    year = duration("us-gaap:Revenues", "1200")
    result = lookup(FakeFacts([quarter, year]), "EXMP", 2025, "revenue")
    assert result is not None and result.value == 1200


def test_a_53_week_year_is_a_whole_year_and_an_earlier_year_is_not() -> None:
    long_year = duration("us-gaap:Revenues", "5", start=date(2024, 12, 27))  # 369 days
    assert lookup(FakeFacts([long_year]), "EXMP", 2025, "revenue") is not None
    earlier = duration("us-gaap:Revenues", "4", start=date(2024, 1, 1), end=date(2024, 12, 31))
    assert lookup(FakeFacts([earlier]), "EXMP", 2025, "revenue") is None


def test_an_instant_must_fall_on_the_period_of_report() -> None:
    assert (
        lookup(
            FakeFacts([instant("us-gaap:Assets", "9", on=date(2024, 12, 31))]),
            "EXMP",
            2025,
            "total_assets",
        )
        is None
    )
    result = lookup(FakeFacts([instant("us-gaap:Assets", "10")]), "EXMP", 2025, "total_assets")
    assert result is not None and (result.instant, result.value) == (
        date(2025, 12, 31),
        Decimal(10),
    )


def test_only_company_totals_count_never_a_segment() -> None:
    segment = duration(
        "us-gaap:Revenues", "500", dimensions={"us-gaap:StatementBusinessSegmentsAxis": "x:A"}
    )
    assert lookup(FakeFacts([segment]), "EXMP", 2025, "revenue") is None


def test_a_duration_fact_is_not_taken_for_an_instant_metric_or_the_reverse() -> None:
    assert (
        lookup(FakeFacts([duration("us-gaap:Assets", "1")]), "EXMP", 2025, "total_assets") is None
    )
    assert lookup(FakeFacts([instant("us-gaap:Revenues", "1")]), "EXMP", 2025, "revenue") is None


def test_the_cover_page_share_count_keeps_its_own_later_date_and_says_so() -> None:
    cover = instant(
        "dei:EntityCommonStockSharesOutstanding",
        "7500000",
        on=date(2026, 2, 10),
        unit="shares",
        decimals="INF",
    )
    result = lookup(FakeFacts([cover]), "EXMP", 2025, "shares_outstanding")
    assert result is not None
    assert (result.value, result.unit, result.instant) == (
        Decimal(7500000),
        "shares",
        date(2026, 2, 10),
    )
    assert result.note is not None and "2026-02-10" in result.note and "2025-12-31" in result.note
    period_end = instant("us-gaap:CommonStockSharesOutstanding", "7400000", unit="shares")
    result = lookup(FakeFacts([cover, period_end]), "EXMP", 2025, "shares_outstanding")
    assert result is not None and (result.concept, result.note) == (
        "us-gaap:CommonStockSharesOutstanding",
        None,
    )


def test_a_cover_page_count_only_per_class_of_stock_is_unavailable() -> None:
    per_class = instant(
        "dei:EntityCommonStockSharesOutstanding",
        "900",
        on=date(2026, 2, 10),
        unit="shares",
        dimensions={"us-gaap:StatementClassOfStockAxis": "us-gaap:CommonClassAMember"},
    )
    assert lookup(FakeFacts([per_class]), "EXMP", 2025, "shares_outstanding") is None


def test_a_metric_the_filing_does_not_report_is_unavailable_and_never_derived() -> None:
    facts = [
        instant("us-gaap:LiabilitiesAndStockholdersEquity", "100"),
        instant("us-gaap:StockholdersEquity", "40"),
    ]
    assert lookup(FakeFacts(facts), "EXMP", 2025, "total_liabilities") is None


def test_two_different_values_for_the_answer_stop_the_lookup() -> None:
    # The facts stage leaves no conflicts; if one ever reached the lookup, it must not choose.
    facts = [duration("us-gaap:Revenues", "1000"), duration("us-gaap:Revenues", "1001")]
    with pytest.raises(LookupError, match="us-gaap:Revenues"):
        lookup(FakeFacts(facts), "EXMP", 2025, "revenue")


def test_units_are_never_changed() -> None:
    eps = duration("us-gaap:EarningsPerShareDiluted", "8.98", unit="USD/shares", decimals="2")
    result = lookup(FakeFacts([eps]), "EXMP", 2025, "diluted_eps")
    assert result is not None and (result.value, result.unit, result.decimals) == (
        Decimal("8.98"),
        "USD/shares",
        "2",
    )


# ---------------------------------------------------------------- line labels and the added tags


def test_every_candidate_tag_has_a_line_label() -> None:
    from filingcheck.facts.metrics import BANK_REVENUE_TAGS, line_label

    for spec in METRICS.values():
        for tag in spec.tags:
            assert line_label(tag, "EXMP"), tag
    for tag in BANK_REVENUE_TAGS:
        assert line_label(tag, "EXMP"), tag


def test_the_line_label_comes_through_for_a_bank_tag_and_a_standard_tag() -> None:
    bank = lookup(
        FakeFacts([duration("us-gaap:RevenuesNetOfInterestExpense", "60515000000")], "bank"),
        "EXMP",
        2025,
        "revenue",
    )
    assert bank is not None and bank.line_label == "Revenues, net of interest expense"
    standard = lookup(FakeFacts([instant("us-gaap:Assets", "10")]), "EXMP", 2025, "total_assets")
    assert standard is not None and standard.line_label == "Total assets"


def gs_filing() -> FilingRef:
    return FilingRef(
        ticker="GS",
        fiscal_year=2025,
        accession=ACC,
        period_of_report=date(2025, 12, 31),
        source_url=URL,
        revenue_rule="bank",
    )


def test_a_company_whose_statement_words_the_line_differently_gets_its_own_label() -> None:
    debt = instant("us-gaap:UnsecuredLongTermDebt", "285500000000")
    result = lookup(FakeFacts([debt], filing=gs_filing()), "GS", 2025, "long_term_debt")
    assert result is not None
    assert (result.concept, result.line_label) == (
        "us-gaap:UnsecuredLongTermDebt",
        "Unsecured long-term borrowings",
    )
    nvda = FilingRef(
        ticker="NVDA",
        fiscal_year=2025,
        accession=ACC,
        period_of_report=date(2025, 12, 31),
        source_url=URL,
        revenue_rule="standard",
    )
    capex = duration("us-gaap:PaymentsToAcquireProductiveAssets", "6042000000")
    result = lookup(FakeFacts([capex], filing=nvda), "NVDA", 2025, "capital_expenditures")
    assert result is not None
    assert result.line_label == "Purchases related to property and equipment and intangible assets"


def test_the_capex_and_debt_tags_are_tried_in_the_agreed_order() -> None:
    assert candidate_tags("capital_expenditures", "standard") == (
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        "us-gaap:PaymentsToAcquireProductiveAssets",
        "us-gaap:PaymentsToAcquireOtherProductiveAssets",
    )
    # The balance-sheet line (LongTermDebtAndCapitalLeaseObligations) comes before
    # LongTermDebt, which some filers use for the debt note's total with current maturities.
    assert candidate_tags("long_term_debt", "standard") == (
        "us-gaap:LongTermDebtNoncurrent",
        "us-gaap:LongTermDebtAndCapitalLeaseObligations",
        "us-gaap:LongTermDebt",
        "us-gaap:UnsecuredLongTermDebt",
        "us-gaap:LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
    )
    both = [
        duration("us-gaap:PaymentsToAcquireProductiveAssets", "2"),
        duration("us-gaap:PaymentsToAcquirePropertyPlantAndEquipment", "1"),
    ]
    result = lookup(FakeFacts(both), "EXMP", 2025, "capital_expenditures")
    assert (
        result is not None
        and result.concept == "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment"
    )


def test_the_balance_sheet_debt_line_wins_over_the_debt_note_total() -> None:
    # Alphabet FY2023: no LongTermDebtNoncurrent; the balance sheet's "Long-term debt" is
    # LongTermDebtAndCapitalLeaseObligations 13,253; LongTermDebt 14,862 is the note's total.
    both = [
        instant("us-gaap:LongTermDebt", "14862000000"),
        instant("us-gaap:LongTermDebtAndCapitalLeaseObligations", "13253000000"),
    ]
    result = lookup(FakeFacts(both), "EXMP", 2025, "long_term_debt")
    assert result is not None
    assert (result.concept, result.value) == (
        "us-gaap:LongTermDebtAndCapitalLeaseObligations",
        Decimal("13253000000"),
    )


def test_the_cover_page_note_says_only_what_is_true_of_the_filing() -> None:
    # A filing may report a year-end count per class of stock (with dimensions); the lookup
    # does not add classes up, so the note must not say the filing has no year-end count.
    cover = instant(
        "dei:EntityCommonStockSharesOutstanding", "4300000000", on=date(2026, 2, 10), unit="shares"
    )
    result = lookup(FakeFacts([cover]), "EXMP", 2025, "shares_outstanding")
    assert result is not None and result.note is not None
    assert "reports no count dated at year end" not in result.note
    assert "no year-end count for the company as a whole" in result.note
