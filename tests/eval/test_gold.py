"""The gold filler: number questions get their gold value from the facts, never over a human's."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from filingcheck.eval.gold import fill_gold, fill_gold_file
from filingcheck.eval.questions import Question
from tests.agent.test_agent import APPLE, apple_deps


def row(**over: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "id": "control-001",
        "set": "control",
        "category": "control",
        "question": "What were Apple's total net sales in fiscal 2025?",
        "company": "AAPL",
        "fiscal_year": 2025,
        "metric": "revenue",
        "expected_behavior": "answer",
        "gold_value": None,
        "gold_unit": "USD",
        "tolerance_pct": 1.0,
        "gold_text": None,
        "trap_note": None,
        "style": "metrics-generated",
    }
    fields.update(over)
    return fields


def test_a_number_question_gets_its_value_period_and_source_from_the_facts() -> None:
    [filled], report = fill_gold([row()], apple_deps().facts)
    assert filled["gold_value"] == 416161000000 and isinstance(filled["gold_value"], int)
    assert filled["gold_unit"] == "USD"
    assert (filled["gold_period_start"], filled["gold_period_end"]) == ("2024-09-29", "2025-09-27")
    assert filled["gold_instant"] is None
    assert filled["gold_concept"] == "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
    assert filled["gold_accession"] == APPLE.accession
    assert filled["gold_source"] == "facts"
    assert report == [("control-001", "filled", "416161000000 USD, 2024-09-29 to 2025-09-27")]
    Question.model_validate(filled)  # still a valid question


def test_a_value_set_by_hand_is_never_overwritten() -> None:
    hand = row(gold_value=1, gold_source="hand")
    [kept], report = fill_gold([hand], apple_deps().facts)
    assert kept == hand
    assert report[0][:2] == ("control-001", "kept: set by hand")


def test_a_value_with_no_source_is_kept_too() -> None:
    unknown = row(gold_value=1)
    [kept], report = fill_gold([unknown], apple_deps().facts)
    assert kept == unknown and report[0][1].startswith("kept")


def test_a_value_from_the_facts_is_filled_again_the_same_way() -> None:
    [first], _ = fill_gold([row()], apple_deps().facts)
    [second], report = fill_gold([first], apple_deps().facts)
    assert second == first and report[0][1] == "filled"


def test_a_question_without_company_year_or_metric_stays_null() -> None:
    ambiguous = row(company=None, fiscal_year=None)
    [kept], report = fill_gold([ambiguous], apple_deps().facts)
    assert kept["gold_value"] is None and "gold_source" not in kept
    assert report[0][1] == "skipped: no company, year or metric"


def test_an_unavailable_metric_leaves_the_value_null_and_says_why() -> None:
    [kept], report = fill_gold([row(metric="operating_income")], apple_deps().facts)
    assert kept["gold_value"] is None
    assert report[0][1] == "unavailable: the filing reports no operating_income"


def test_a_per_share_value_keeps_its_decimals() -> None:
    from tests.facts.test_lookup import FakeFacts, duration

    eps = duration(
        "us-gaap:EarningsPerShareDiluted",
        "6.08",
        date(2024, 9, 29),
        date(2025, 9, 27),
        unit="USD/shares",
        decimals="2",
    )

    [filled], _ = fill_gold([row(metric="diluted_eps")], FakeFacts([eps], filing=APPLE))
    assert filled["gold_value"] == 6.08 and filled["gold_unit"] == "USD/shares"


def test_the_file_is_rewritten_line_by_line_in_its_own_order(tmp_path: Path) -> None:
    path = tmp_path / "q.jsonl"
    rows = [row(), row(id="control-002", company=None)]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    report = fill_gold_file(path, apple_deps().facts)
    written = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [r["id"] for r in written] == ["control-001", "control-002"]
    assert written[0]["gold_value"] == 416161000000 and written[1]["gold_value"] is None
    assert [r[1] for r in report] == ["filled", "skipped: no company, year or metric"]


def test_the_question_format_requires_a_value_for_a_facts_source() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="gold_source"):
        Question.model_validate(row(gold_source="facts"))


class TwoYears:
    """Apple's FY2024 and FY2025 filings, each with its own revenue fact."""

    def __init__(self) -> None:
        from dataclasses import replace

        from tests.facts.test_lookup import duration

        self.refs = {
            2025: APPLE,
            2024: replace(
                APPLE,
                fiscal_year=2024,
                accession="0000320193-24-000123",
                period_of_report=date(2024, 9, 28),
            ),
        }
        tag = "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"
        self.by_accession = {
            APPLE.accession: [duration(tag, "416161000000", date(2024, 9, 29), date(2025, 9, 27))],
            "0000320193-24-000123": [
                duration(tag, "391035000000", date(2023, 10, 1), date(2024, 9, 28))
            ],
        }

    def filing(self, ticker: str, fiscal_year: int) -> Any:
        return self.refs.get(fiscal_year) if ticker == "AAPL" else None

    def facts(self, accession: str, concepts: Any) -> Any:
        return [f for f in self.by_accession.get(accession, []) if f.concept in concepts]


def test_the_same_metric_for_the_companys_other_pinned_years_is_recorded() -> None:
    [filled], _ = fill_gold([row()], TwoYears())
    assert filled["gold_value"] == 416161000000
    assert filled["gold_other_years"] == {"2024": 391035000000}
    assert Question.model_validate(filled).gold_other_years == {2024: 391035000000}


def test_a_clarify_or_refuse_question_gets_no_gold_value() -> None:
    refuse = row(
        id="trap-005",
        set="trap",
        category="metric_not_supported",
        expected_behavior="refuse",
        style=None,
    )
    [kept], report = fill_gold([refuse], apple_deps().facts)
    assert kept["gold_value"] is None and report[0][1] == "skipped: a refuse question"
    # A value filled from the facts before is cleared.
    [filled], _ = fill_gold([row()], apple_deps().facts)
    [cleared], _ = fill_gold([{**filled, "expected_behavior": "clarify"}], apple_deps().facts)
    assert cleared["gold_value"] is None and cleared["gold_source"] is None
    assert cleared["gold_other_years"] is None
    # A value set by hand stays, as always.
    hand = {**refuse, "gold_value": 1, "gold_source": "hand"}
    assert fill_gold([hand], apple_deps().facts)[0] == [hand]


def test_an_alternative_year_in_also_accept_gets_its_gold_value_from_the_facts() -> None:
    question = row(also_accept={"fiscal_year": 2024})
    [filled], report = fill_gold([question], TwoYears())
    also = filled["also_accept"]
    assert (also["gold_value"], also["gold_unit"], also["gold_source"]) == (
        391035000000,
        "USD",
        "facts",
    )
    assert (also["gold_period_start"], also["gold_period_end"]) == ("2023-10-01", "2024-09-28")
    assert also["gold_accession"] == "0000320193-24-000123"
    assert report[-1] == ("control-001", "also_accept filled", "391035000000 USD, fiscal 2024")
    Question.model_validate(filled)


def test_an_alternative_behavior_alone_gets_no_gold_value() -> None:
    question = row(also_accept={"expected_behavior": "refuse"})
    [filled], _ = fill_gold([question], TwoYears())
    assert filled["also_accept"] == {"expected_behavior": "refuse"}
