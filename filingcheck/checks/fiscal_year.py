"""The fiscal-year check: the `fiscal_year` argument against the question and the manifest.

The question's years: a bare year or a fiscal phrase ("2025", "fiscal 2025", "FY2025",
"FY25", "fiscal '25", "fiscal years 2024 and 2025") is the fiscal-year label; "the year
ended <date>" is the pinned fiscal year whose period ends on that date; relative words
("last year", "latest", "most recent", "this year") mean the company's latest pinned year,
"the year before" one year earlier and "two years ago" two. A year inside any other date
(a filing date) is not a fiscal year. Every reason states the period dates, so a reader can
see what was meant: "fiscal 2025 (Feb 1, 2024 to Jan 31, 2025)".
"""

import re
from datetime import date, timedelta

from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult
from filingcheck.facts.lookup import FactsSource, lookup
from filingcheck.ingest.filings import Manifest

NAME = "fiscal_year"
RIGHT_QUOTE = chr(0x2019)
MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
    )
}
MONTH_RE = (
    r"(?P<month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
DATE_RE = re.compile(
    r"\b" + MONTH_RE + r"\.?\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})\b"
    r"|\b(?P<iso>\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
# The words before a date that make it the end of a fiscal year.
PERIOD_END_RE = re.compile(
    r"(?:\bended|\bending|\bend|\bas of|\bthrough|\bto|\bat|\bon)\s*$", re.IGNORECASE
)
# Not "filed on <date>": a filing date is not a period end.
FILED_RE = re.compile(r"\b(?:filed|dated|issued|released|published)\s+(?:on\s+)?$", re.IGNORECASE)
_YEAR = r"(?:\d{4}|'?\d{2})(?!\d)(?!-?\s*week)"
FISCAL_RE = re.compile(
    r"\b(?:fiscal(?:[\s-]+years?)?|FY)[\s-]*(" + _YEAR + r")"
    r"((?:\s*(?:,|and|&|-|to|through)\s*(?:fiscal\s+|FY\s?)?" + _YEAR + r")*)",
    re.IGNORECASE,
)
BARE_RANGE_RE = re.compile(r"(?<![\d$.,])((?:19|20)\d{2})\s*-\s*(\d{2})(?!\d)")
BARE_YEAR_RE = re.compile(
    r"(?<![\d$.,])((?:19|20)\d{2})(?![\d%]|[.,]\d)(?!\s*(?:million|billion|thousand))"
)
# Relative words, longest first: (pattern, how many years before the reference, reference).
RELATIVE: tuple[tuple[str, int, str], ...] = (
    (r"the year before last|two years ago", 2, "latest"),
    (
        r"the year before|the prior year|the previous year|a year earlier|the preceding year",
        1,
        "stated",
    ),
    (
        r"last fiscal year|last year|the latest(?: annual)? report|the latest|latest"
        r"|most recent(?: fiscal year)?|this year|the current year|current fiscal year",
        0,
        "latest",
    ),
)


def _pinned(ticker: str, manifest: Manifest) -> dict[int, date]:
    """The company's pinned fiscal years and the date each one ends."""
    return {f.fiscal_year: f.period_of_report for f in manifest.filings if f.ticker == ticker}


def _short(day: date) -> str:
    return f"{day:%b} {day.day}, {day.year}"


def period_text(
    ticker: str, year: int, manifest: Manifest, facts: FactsSource | None = None
) -> str:
    """The period of a pinned fiscal year, as in fiscal 2025 (Feb 1, 2024 to Jan 31, 2025).

    A year starts the day after the previous pinned year ends; the earliest pinned year's
    start comes from its operating cash flow fact when the facts are given.
    """
    pinned = _pinned(ticker, manifest)
    end = pinned.get(year)
    if end is None:
        return f"fiscal {year}"
    start: date | None = None
    if year - 1 in pinned:
        start = pinned[year - 1] + timedelta(days=1)
    elif facts is not None:
        try:
            result = lookup(facts, ticker, year, "operating_cash_flow")
        except LookupError:
            result = None
        start = result.period_start if result is not None else None
    if start is None:
        return f"fiscal {year} (year ended {_short(end)})"
    return f"fiscal {year} ({_short(start)} to {_short(end)})"


def _year(text: str) -> int:
    digits = text.lstrip("'")
    return int(digits) if len(digits) == 4 else 2000 + int(digits)


def read_years(question: str, ticker: str, manifest: Manifest) -> dict[int, str]:
    """The fiscal years the question asks about, each with how it was read."""
    text = question.replace(RIGHT_QUOTE, "'").replace(chr(0x2013), "-")
    pinned = _pinned(ticker, manifest)
    years: dict[int, str] = {}
    for match in DATE_RE.finditer(text):
        before = text[: match.start()]
        if FILED_RE.search(before) or not PERIOD_END_RE.search(before):
            continue
        if match["iso"]:
            day = date.fromisoformat(match["iso"])
        else:
            day = date(int(match["year"]), MONTHS[match["month"][:3].lower()], int(match["day"]))
        near = [y for y, end in pinned.items() if abs((end - day).days) <= 7]
        year = near[0] if near else day.year
        years.setdefault(year, f"the question names the year ended {_short(day)}")
    rest = DATE_RE.sub(" ", text)
    for match in FISCAL_RE.finditer(rest):
        for found in [match.group(1), *re.findall(r"'?\d{4}|'?\d{2}", match.group(2))]:
            years.setdefault(_year(found), f"the question says fiscal {_year(found)}")
    rest = FISCAL_RE.sub(" ", rest)
    for match in BARE_RANGE_RE.finditer(rest):
        first = int(match.group(1))
        for year in (first, first // 100 * 100 + int(match.group(2))):
            years.setdefault(year, f"the question says {year}")
    rest = BARE_RANGE_RE.sub(" ", rest)
    for match in BARE_YEAR_RE.finditer(rest):
        year = int(match.group(1))
        years.setdefault(year, f"the question says {year}")
    if pinned:
        latest = max(pinned)
        lowered = rest.lower()
        for pattern, back, reference in RELATIVE:
            found_word = re.search(r"\b(?:" + pattern + r")\b", lowered)
            if found_word is None:
                continue
            word = found_word.group(0)
            lowered = lowered.replace(word, " ")
            base = min(years) if reference == "stated" and years else latest
            year = base - back
            if back == 0:
                how = f"'{word}' read as the latest annual report"
            elif reference == "stated" and years:
                how = f"'{word}' read as the year before fiscal {base}"
            else:
                how = f"'{word}' read as {back} year(s) before the latest annual report"
            years.setdefault(year, how)
    return years


def _join(years: list[int]) -> str:
    named = [f"fiscal {y}" for y in years]
    return named[0] if len(named) == 1 else ", ".join(named[:-1]) + " and " + named[-1]


class FiscalYearCheck:
    """Rules (a) to (e) of the Week 4 spec, with the page-filter rules from the review."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the `fiscal_year` argument against the question, the filter and the manifest."""
        if context.manifest is None:
            return CheckResult.passed(
                self.name, "fiscal_year", call.arguments, "no manifest; the year is not checked"
            )
        ticker, sent = call.arguments["ticker"], call.arguments["fiscal_year"]
        pinned = _pinned(ticker, context.manifest)

        def period(year: int) -> str:
            return period_text(ticker, year, context.manifest, context.facts)  # type: ignore[arg-type]

        def unpinned(year: int) -> CheckResult:
            listed = ", ".join(str(y) for y in sorted(pinned))
            reason = (
                f"{ticker} has no 10-K for fiscal {year} in the dataset; "
                f"the pinned fiscal years are {listed}"
            )
            return CheckResult.rejected(
                self.name,
                "fiscal_year",
                call.arguments,
                reason,
                options=[str(y) for y in sorted(pinned)],
            )

        def settle(target: int, why: str) -> CheckResult:
            if target not in pinned:
                return unpinned(target)
            if target == sent:
                reason = f"{why}; the model sent {sent}: {period(target)}"
                return CheckResult.passed(self.name, "fiscal_year", call.arguments, reason)
            reason = f"{why}; the model sent {sent}; used {period(target)}"
            used = {**call.arguments, "fiscal_year": target}
            return CheckResult.repaired(self.name, "fiscal_year", call.arguments, used, reason)

        asked = read_years(context.question, ticker, context.manifest)
        page = context.fiscal_year
        if asked:
            if page is not None and page not in asked:
                options = sorted({*asked, page})
                reason = (
                    f"the question asks about {_join(sorted(asked))} but the page filter is "
                    f"fiscal {page}; ask the user which one"
                )
                return CheckResult.rejected(
                    self.name,
                    "fiscal_year",
                    call.arguments,
                    reason,
                    options=[str(y) for y in options],
                )
            if sent in asked:
                return settle(sent, asked[sent])
            if len(asked) == 1:
                ((target, why),) = asked.items()
                return settle(target, why)
            reason = f"the question names {_join(sorted(asked))}; the model sent {sent}"
            return CheckResult.rejected(
                self.name,
                "fiscal_year",
                call.arguments,
                reason,
                options=[str(y) for y in sorted(asked)],
            )
        if page is not None:
            return settle(page, f"no year in the question; the user selected fiscal {page}")
        if sent not in pinned:
            return unpinned(sent)
        reason = f"no year in the question; the model's choice stands: {period(sent)}"
        return CheckResult.passed(self.name, "fiscal_year", call.arguments, reason)
