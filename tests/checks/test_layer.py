"""The check layer: pass, repair and reject results, the override log, and `run_checks`."""

from typing import Any

from filingcheck.checks import (
    CheckContext,
    CheckedCall,
    CheckResult,
    Override,
    run_checks,
)


def context(question: str = "What was revenue?", **over: Any) -> CheckContext:
    fields: dict[str, Any] = {
        "question": question,
        "ticker": None,
        "fiscal_year": None,
        "companies": [],
        "not_covered": [],
    }
    fields.update(over)
    return CheckContext(**fields)


class Passes:
    name = "always_pass"

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        return CheckResult.passed(self.name, "ticker", call.arguments, "nothing to change")


class RepairsYear:
    name = "year_to_2026"

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        return CheckResult.repaired(
            self.name,
            "fiscal_year",
            call.arguments,
            {**call.arguments, "fiscal_year": 2026},
            "'last year' read as FY2026",
        )


class SeesRepair:
    """Asserts the chain hands it the arguments as repaired by the check before it."""

    name = "sees_repair"

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        assert call.arguments["fiscal_year"] == 2026
        return CheckResult.passed(self.name, "fiscal_year", call.arguments, "seen")


class Rejects:
    name = "company"
    ran = 0

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        Rejects.ran += 1
        return CheckResult.rejected(
            self.name, "ticker", call.arguments, "ambiguous", options=["JPM", "MS"]
        )


class NeverRuns:
    name = "never"

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        raise AssertionError("a check after a reject must not run")


CALL = CheckedCall("get_financial_fact", {"ticker": "MS", "fiscal_year": 2025, "metric": "revenue"})


def test_every_result_is_an_override_record_pass_included() -> None:
    call, overrides = run_checks(CALL, context(), [Passes()])
    assert call == CALL
    [record] = overrides
    assert isinstance(record, Override)
    assert (record.check, record.outcome, record.argument) == ("always_pass", "pass", "ticker")
    assert (record.sent, record.used) == ("MS", "MS")
    assert record.reason == "nothing to change" and record.options == []


def test_a_repair_changes_the_arguments_for_the_checks_after_it_and_for_the_tool() -> None:
    call, overrides = run_checks(CALL, context(), [RepairsYear(), SeesRepair()])
    assert call is not None and call.arguments["fiscal_year"] == 2026
    assert call.name == "get_financial_fact"
    assert [(o.check, o.outcome) for o in overrides] == [
        ("year_to_2026", "repair"),
        ("sees_repair", "pass"),
    ]
    assert (overrides[0].sent, overrides[0].used) == (2025, 2026)


def test_the_first_reject_stops_the_chain_and_returns_no_call() -> None:
    Rejects.ran = 0
    call, overrides = run_checks(CALL, context(), [Passes(), Rejects(), NeverRuns()])
    assert call is None
    assert [o.outcome for o in overrides] == ["pass", "reject"]
    reject = overrides[-1]
    assert (reject.sent, reject.used, reject.options) == ("MS", None, ["JPM", "MS"])
    assert Rejects.ran == 1


def test_the_original_call_is_not_changed_by_a_repair() -> None:
    before = dict(CALL.arguments)
    run_checks(CALL, context(), [RepairsYear()])
    assert CALL.arguments == before


def test_an_override_serializes_to_plain_json_for_the_log() -> None:
    record = Override(
        check="company",
        outcome="repair",
        argument="ticker",
        sent="MSFT",
        used="AAPL",
        reason="the question names Apple Inc. (AAPL); the model sent MSFT",
    )
    data = record.model_dump()
    assert data["options"] == [] and data["used"] == "AAPL"
    assert Override.model_validate(data) == record
