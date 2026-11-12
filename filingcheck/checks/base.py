"""The check layer: rules that run on a tool call's arguments before the tool does.

A check reads the user's question, the page filters and the SEC data we hold, never the
model's reasoning, and gives one of three results: pass (arguments unchanged), repair (the
arguments changed, with a reason) or reject (the tool does not run, with a reason and the
options the model can act on). Every result is an `Override` record; the records of one run
are the override log, carried in the answer, the request log, the batch rows and `make ask`.
The checks are pure: no network, no model, no writes. When a check is not sure it rejects
with the options listed; it never guesses at SEC data semantics.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field

from filingcheck.facts.lookup import FactsSource
from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest

Outcome = Literal["pass", "repair", "reject"]


class Override(BaseModel):
    """One check's result on one tool call: what was sent, what was used, and why."""

    check: str  # "company", "fiscal_year", ...
    tool: str | None = None  # the tool the call was for ("get_financial_fact", "search_filings")
    outcome: Outcome
    argument: str | None  # the argument the check looked at ("ticker"); None if none
    sent: Any  # the value the model sent
    used: Any  # the value the tool ran with (None on a reject)
    reason: str
    options: list[str] = Field(default_factory=list)  # on a reject: what the model may send


@dataclass(frozen=True)
class CheckedCall:
    """A tool call as the checks see it: the tool's name and its validated arguments.

    `annotations` carry what a check asks to add next to the tool's result (the units
    check's requested scale); they never change the arguments.
    """

    name: str
    arguments: dict[str, Any]
    annotations: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckContext:
    """What a check may read: the question, the page filters and the data we hold."""

    question: str
    ticker: str | None  # the page's company filter
    fiscal_year: int | None  # the page's year filter
    companies: list[Company]
    not_covered: list[str] = field(default_factory=list)
    manifest: Manifest | None = None
    facts: FactsSource | None = None  # read-only


@dataclass(frozen=True)
class CheckResult:
    """A check's verdict: the arguments after it, and its override record."""

    outcome: Outcome
    arguments: dict[str, Any]
    override: Override
    annotations: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def passed(
        cls,
        check: str,
        argument: str | None,
        arguments: dict[str, Any],
        reason: str,
        annotations: dict[str, Any] | None = None,
    ) -> "CheckResult":
        """The arguments stand; the record says why."""
        value = arguments.get(argument) if argument else None
        record = Override(
            check=check, outcome="pass", argument=argument, sent=value, used=value, reason=reason
        )
        return cls("pass", dict(arguments), record, dict(annotations or {}))

    @classmethod
    def repaired(
        cls, check: str, argument: str, sent: dict[str, Any], used: dict[str, Any], reason: str
    ) -> "CheckResult":
        """The tool runs with `used` instead of `sent`."""
        record = Override(
            check=check,
            outcome="repair",
            argument=argument,
            sent=sent.get(argument),
            used=used.get(argument),
            reason=reason,
        )
        return cls("repair", dict(used), record)

    @classmethod
    def rejected(
        cls,
        check: str,
        argument: str | None,
        arguments: dict[str, Any],
        reason: str,
        *,
        options: Sequence[str] = (),
    ) -> "CheckResult":
        """The tool does not run; the model gets the reason and the options."""
        record = Override(
            check=check,
            outcome="reject",
            argument=argument,
            sent=arguments.get(argument) if argument else None,
            used=None,
            reason=reason,
            options=list(options),
        )
        return cls("reject", dict(arguments), record)


class Check(Protocol):
    """One rule over a tool call's arguments."""

    name: str

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the call; pure."""
        ...


def run_checks(
    call: CheckedCall, context: CheckContext, checks: Sequence[Check]
) -> tuple[CheckedCall | None, list[Override]]:
    """Run the checks in order; a repair feeds the checks after it, the first reject stops.

    Returns the call to run (None after a reject) and every check's override record.
    """
    overrides: list[Override] = []
    arguments = dict(call.arguments)
    annotations: dict[str, Any] = {}
    for check in checks:
        result = check.run(CheckedCall(call.name, dict(arguments)), context)
        overrides.append(result.override.model_copy(update={"tool": call.name}))
        if result.outcome == "reject":
            return None, overrides
        arguments = dict(result.arguments)
        annotations.update(result.annotations)
    return CheckedCall(call.name, arguments, annotations), overrides
