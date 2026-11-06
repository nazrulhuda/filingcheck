"""The company check: the `ticker` argument against the companies the question names.

Mentions come from `data/companies.yaml`: each company's name, ticker and aliases name that
company; a word in a company's `lookalikes` list names every company that lists it ("Morgan":
JPMorgan Chase and Morgan Stanley). Matching is whole-word and longest-first, so "Morgan
Stanley" and "JP Morgan" are never ambiguous, and case-insensitive except for a ticker or
short initialism written in capitals ("MS", "COST", "IBM"), which must appear as typed, since
"ms", "cost" and "ma" are ordinary words. The top-level `not_covered` list holds well-known
companies outside the dataset, matched as written, so "Target" the company is not "target".
"""

import re
from dataclasses import dataclass

from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult
from filingcheck.ingest.companies import Company

NAME = "company"
RIGHT_QUOTE = chr(0x2019)
_BEFORE, _AFTER = r"(?<![A-Za-z0-9])", r"(?![A-Za-z0-9])"


@dataclass(frozen=True)
class Mention:
    """A company name found in the question, and the companies it can mean."""

    text: str  # as written in the question (with a curly apostrophe straightened)
    start: int
    end: int
    tickers: frozenset[str]  # one for a name, ticker or alias; two or more for a lookalike


def _normalize(question: str) -> str:
    return question.replace(RIGHT_QUOTE, "'")


def _pattern(term: str) -> re.Pattern[str]:
    # A ticker or short initialism in capitals must appear as typed; anything else may be
    # written in any case.
    flags = 0 if term.isupper() and len(term) <= 5 else re.IGNORECASE
    return re.compile(_BEFORE + re.escape(term) + _AFTER, flags)


def _terms(companies: list[Company]) -> dict[str, frozenset[str]]:
    """Every word that names a company, and the companies it names."""
    found: dict[str, set[str]] = {}
    for company in companies:
        for term in (company.name, company.ticker, *company.aliases, *company.lookalikes):
            found.setdefault(term, set()).add(company.ticker)
    return {term: frozenset(tickers) for term, tickers in found.items()}


def _longest_first(matches: list[Mention]) -> list[Mention]:
    """Keep the longest of any overlapping matches, then put them in question order."""
    kept: list[Mention] = []
    for match in sorted(matches, key=lambda m: (m.start - m.end, m.start)):
        if all(match.end <= k.start or match.start >= k.end for k in kept):
            kept.append(match)
    return sorted(kept, key=lambda m: m.start)


def find_mentions(question: str, companies: list[Company]) -> list[Mention]:
    """Every company the question names, in question order, longest match first."""
    text = _normalize(question)
    matches = [
        Mention(text[m.start() : m.end()], m.start(), m.end(), tickers)
        for term, tickers in _terms(companies).items()
        for m in _pattern(term).finditer(text)
    ]
    return _longest_first(matches)


def find_not_covered(question: str, not_covered: list[str]) -> list[str]:
    """The names from the not-covered list that the question uses, as written in the list."""
    text = _normalize(question)
    found = [
        name
        for name in not_covered
        if re.search(_BEFORE + re.escape(name) + _AFTER, text) is not None
    ]
    return sorted(set(found), key=found.index)


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


class CompanyCheck:
    """Rules (a) to (e) of the Week 4 spec, plus the page filter and the not-covered list."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the `ticker` argument against the question and the page filter."""
        sent = call.arguments["ticker"]
        by_ticker = {c.ticker: c for c in context.companies}

        def label(ticker: str) -> str:
            return f"{by_ticker[ticker].name} ({ticker})"

        def labels(tickers: set[str]) -> str:
            return _join([label(t) for t in sorted(tickers)])

        mentions = find_mentions(context.question, context.companies)
        named = {t for m in mentions if len(m.tickers) == 1 for t in m.tickers}
        ambiguous = [m for m in mentions if len(m.tickers) > 1 and not (m.tickers & named)]
        uncovered = find_not_covered(context.question, context.not_covered)
        page_filter = context.ticker
        notes = ""
        if uncovered:
            verb = "is" if len(uncovered) == 1 else "are"
            notes += f"; {_join(uncovered)} {verb} not in the dataset"
        for mention in ambiguous:
            notes += f"; '{mention.text}' is ambiguous ({', '.join(sorted(mention.tickers))})"

        if uncovered and sent not in named:
            verb = "is not one of" if len(uncovered) == 1 else "are not among"
            reason = f"{_join(uncovered)} {verb} the 25 companies in the dataset"
            if named:
                reason += f"; the question also names {labels(named)}"
            return CheckResult.rejected(
                self.name, "ticker", call.arguments, reason, options=sorted(by_ticker)
            )
        if page_filter and named and page_filter not in named:
            reason = (
                f"the question names {labels(named)} but the page filter is "
                f"{label(page_filter)}; ask the user which one"
            )
            return CheckResult.rejected(
                self.name,
                "ticker",
                call.arguments,
                reason,
                options=sorted(named | {page_filter}),
            )
        if sent in named:
            reason = f"the question names {labels(named)}; the model sent {sent}{notes}"
            return CheckResult.passed(self.name, "ticker", call.arguments, reason)
        if ambiguous:
            options = sorted({t for m in ambiguous for t in m.tickers})
            reason = (
                f"the question's company is ambiguous: {' or '.join(label(t) for t in options)}; "
                "ask the user which one"
            )
            return CheckResult.rejected(
                self.name, "ticker", call.arguments, reason, options=options
            )
        if len(named) == 1:
            (target,) = named
            reason = f"the question names {label(target)}; the model sent {sent}{notes}"
            used = {**call.arguments, "ticker": target}
            return CheckResult.repaired(self.name, "ticker", call.arguments, used, reason)
        if len(named) >= 2:
            reason = (
                f"the question names {labels(named)}; the model sent {sent}, which the "
                "question does not name"
            )
            return CheckResult.rejected(
                self.name, "ticker", call.arguments, reason, options=sorted(named)
            )
        if page_filter:
            if sent == page_filter:
                reason = (
                    f"no company named in the question; the user selected {page_filter} and "
                    f"the model sent {sent}{notes}"
                )
                return CheckResult.passed(self.name, "ticker", call.arguments, reason)
            reason = (
                f"no company named in the question; the user selected {page_filter}; the "
                f"model sent {sent}{notes}"
            )
            used = {**call.arguments, "ticker": page_filter}
            return CheckResult.repaired(self.name, "ticker", call.arguments, used, reason)
        reason = f"no company named in the question; the model's choice stands{notes}"
        return CheckResult.passed(self.name, "ticker", call.arguments, reason)
