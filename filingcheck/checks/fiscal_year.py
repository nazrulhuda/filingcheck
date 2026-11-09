"""The fiscal-year check: the `fiscal_year` argument against the question and the manifest.

A repair rests on strong evidence only: an explicit year ("2025" is the fiscal-year label by
the settled convention, "fiscal 2025", "FY2025", "FY25", "fiscal years 2024 and 2025"), "the
year ended/ending <date>" or "as of <date>" (the fiscal year ending within a week of that date),
a date range one fiscal year long ("Jan 27, 2025 to Jan 25, 2026": the year ending on the
second date), a relative
word ("last year", "latest", "most recent", "this year": the latest pinned year; "the year
before" one earlier; "two years ago" two earlier), or the page filter. A date after a weak cue
("on", "to", "at", "compared to", "filed on", "announced on") counts for nothing and leaves
the model's argument standing: a false repair is a silent wrong answer, a false pass is not.
A date or range that is no fiscal year of the company ("the year ended December 31, 2025"
for Walmart, "January 1 to June 30, 2025") is rejected with the company's real periods and
"ask the user": the 10-K data has no figure for it, and the nearest year would be a guess.
"Calendar 2025" is read apart: it is fiscal 2025 for a company whose year ends in December,
and for the others a reject naming the two overlapping fiscal years, with "ask the user".
Every reason states the period dates: "fiscal 2025 (Feb 1, 2024 to Jan 31, 2025)".
"""

import re
from datetime import date, timedelta

from filingcheck.checks.base import CheckContext, CheckedCall, CheckResult
from filingcheck.facts.lookup import FactsSource, lookup
from filingcheck.ingest.filings import Manifest

NAME = "fiscal_year"
RIGHT_QUOTE = chr(0x2019)
DASHES = str.maketrans({chr(0x2013): "-", chr(0x2014): "-", chr(0x2212): "-"})
MONTHS = {
    m: i + 1
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")
    )
}
MONTH = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?"
    r"|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
# One full date: "January 31, 2025", "Jan. 31, 2025", "31 January 2025" or "2025-01-31".
DATE_RE = re.compile(
    r"\b(?P<month>" + MONTH + r")\.?\s+(?P<day>\d{1,2}),?\s+(?P<year>\d{4})\b"
    r"|\b(?P<day2>\d{1,2})\s+(?P<month2>" + MONTH + r")\.?,?\s+(?P<year2>\d{4})\b"
    r"|\b(?P<iso>\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)
# A month and a year with no day ("November 2025"): a filing date, never a fiscal year.
MONTH_YEAR_RE = re.compile(r"\b" + MONTH + r"\.?\s+\d{4}\b", re.IGNORECASE)
# The words that make a date the end of a fiscal year. "on", "to", "at", "through" are not
# among them: "compared to <date>" and "reported on <date>" are not periods.
PERIOD_END_RE = re.compile(r"\b(?:ended|ending|ends|end of|as of)\s*$", re.IGNORECASE)
RANGE_GAP_RE = re.compile(r"\s*(?:to|through|until|-)\s*", re.IGNORECASE)
_YEAR = r"(?:\d{4}|'?\d{2})(?!\d)(?!-?\s*week)"
FISCAL_RE = re.compile(
    r"\b(?:fiscal(?:[\s-]+years?)?|FY)[\s-]*(" + _YEAR + r")"
    r"((?:\s*(?:,|and|&|-|to|through)\s*(?:fiscal\s+|FY\s?)?" + _YEAR + r")*)",
    re.IGNORECASE,
)
CALENDAR_RE = re.compile(
    r"\b(?:calendar(?:\s+year)?\s+(?P<a>\d{4})|CY\s?(?P<b>\d{4}|\d{2})(?!\d)"
    r"|the\s+(?P<c>\d{4})\s+calendar\s+year)\b",
    re.IGNORECASE,
)
BARE_RANGE_RE = re.compile(r"(?<![\d$.,])((?:19|20)\d{2})\s*-\s*(\d{2})(?!\d)")
BARE_YEAR_RE = re.compile(
    r"(?<![\d$.,])((?:19|20)\d{2})(?![\d%]|[.,]\d)(?!\s*(?:million|billion|thousand))"
)
# Relative words, longest first: (pattern, years before the reference, the reference).
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
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _pinned(ticker: str, manifest: Manifest) -> dict[int, date]:
    """The company's pinned fiscal years and the date each one ends."""
    return {f.fiscal_year: f.period_of_report for f in manifest.filings if f.ticker == ticker}


def _short(day: date) -> str:
    return f"{day:%b} {day.day}, {day.year}"


def _start(year: int, pinned: dict[int, date]) -> date | None:
    """The day after the previous pinned year ends; None for the earliest pinned year."""
    return pinned[year - 1] + timedelta(days=1) if year - 1 in pinned else None


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
    start = _start(year, pinned)
    if start is None and facts is not None:
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


def _date(match: re.Match[str]) -> date:
    if match["iso"]:
        return date.fromisoformat(match["iso"])
    if match["month"]:
        month, day, year = match["month"], match["day"], match["year"]
    else:
        month, day, year = match["month2"], match["day2"], match["year2"]
    return date(int(year), MONTHS[month[:3].lower()], int(day))


def _normalize(question: str) -> str:
    return question.replace(RIGHT_QUOTE, "'").translate(DASHES)


def read_calendar_years(question: str) -> set[int]:
    """The calendar years the question names ("calendar 2025", "CY2025")."""
    return {_year(m["a"] or m["b"] or m["c"]) for m in CALENDAR_RE.finditer(_normalize(question))}


# A date this close to a year end is that year end (52/53-week years end on a weekday).
NEAR_DAYS = 7
# A range this long is one fiscal year: 52 weeks is 363 days end minus start, 53 weeks 370.
YEAR_DAYS = range(350, 381)


def _shift(day: date, years: int) -> date:
    try:
        return day.replace(year=day.year + years)
    except ValueError:  # Feb 29
        return day.replace(year=day.year + years, day=28)


def _label(day: date, pinned: dict[int, date]) -> int | None:
    """The fiscal year ending within a week of `day`, or None if it is no year end.

    The year end is a pinned one or a pinned one moved by whole years, so Dec 31, 2022 is
    Coca-Cola's fiscal 2022, which is not in the dataset.
    """
    best: tuple[int, int, int] | None = None  # (days off, years moved, fiscal year)
    for year, end in pinned.items():
        for moved in range(-6, 7):
            off = abs((_shift(end, moved) - day).days)
            if off <= NEAR_DAYS and (best is None or (off, abs(moved)) < best[:2]):
                best = (off, abs(moved), year + moved)
    return best[2] if best else None


def read_years(question: str, ticker: str, manifest: Manifest) -> dict[int, str]:
    """The fiscal years the question asks about, each with how it was read."""
    return _read(question, ticker, manifest)[0]


def read_odd_periods(question: str, ticker: str, manifest: Manifest) -> list[tuple[date, date]]:
    """The dates and ranges named as periods that are no fiscal year of the company.

    Each is (start, end); a single date is (date, date).
    """
    return _read(question, ticker, manifest)[1]


def _read(
    question: str, ticker: str, manifest: Manifest
) -> tuple[dict[int, str], list[tuple[date, date]]]:
    text = CALENDAR_RE.sub(" ", _normalize(question))
    pinned = _pinned(ticker, manifest)
    years: dict[int, str] = {}
    odd: list[tuple[date, date]] = []

    dates = list(DATE_RE.finditer(text))
    i = 0
    while i < len(dates):
        this = dates[i]
        gap = text[this.end() : dates[i + 1].start()] if i + 1 < len(dates) else None
        if gap is not None and RANGE_GAP_RE.fullmatch(gap):
            start, end = _date(this), _date(dates[i + 1])
            year = _label(end, pinned)
            if year is None or (end - start).days not in YEAR_DAYS:
                odd.append((start, end))
            else:
                how = f"the question names the period {_short(start)} to {_short(end)}"
                years.setdefault(year, how)
            i += 2
            continue
        if PERIOD_END_RE.search(text[: this.start()]):
            day = _date(this)
            year = _label(day, pinned)
            if year is None:
                odd.append((day, day))
            else:
                years.setdefault(year, f"the question names the year ended {_short(day)}")
        i += 1
    rest = MONTH_YEAR_RE.sub(" ", DATE_RE.sub(" ", text))
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
    return years, odd


def _join(years: list[int]) -> str:
    named = [f"fiscal {y}" for y in years]
    return named[0] if len(named) == 1 else ", ".join(named[:-1]) + " and " + named[-1]


class FiscalYearCheck:
    """Rules (a) to (e) of the Week 4 spec, with the page-filter and calendar rules from review."""

    name = NAME

    def run(self, call: CheckedCall, context: CheckContext) -> CheckResult:
        """Judge the `fiscal_year` argument against the question, the filter and the manifest."""
        if context.manifest is None:
            return CheckResult.passed(
                self.name, "fiscal_year", call.arguments, "no manifest; the year is not checked"
            )
        manifest = context.manifest
        ticker, sent = call.arguments["ticker"], call.arguments["fiscal_year"]
        pinned = _pinned(ticker, manifest)
        listed = ", ".join(str(y) for y in sorted(pinned))

        def period(year: int) -> str:
            return period_text(ticker, year, manifest, context.facts)

        def reject(reason: str, options: list[int]) -> CheckResult:
            return CheckResult.rejected(
                self.name, "fiscal_year", call.arguments, reason, options=[str(y) for y in options]
            )

        def unpinned(year: int) -> CheckResult:
            reason = (
                f"{ticker} has no 10-K for fiscal {year} in the dataset; "
                f"the pinned fiscal years are {listed}"
            )
            return reject(reason, sorted(pinned))

        def settle(target: int, why: str) -> CheckResult:
            if target not in pinned:
                return unpinned(target)
            if target == sent:
                reason = f"{why}; the model sent {sent}: {period(target)}"
                return CheckResult.passed(self.name, "fiscal_year", call.arguments, reason)
            reason = f"{why}; the model sent {sent}; used {period(target)}"
            used = {**call.arguments, "fiscal_year": target}
            return CheckResult.repaired(self.name, "fiscal_year", call.arguments, used, reason)

        asked, odd = _read(context.question, ticker, manifest)
        if odd:
            start, end = odd[0]
            named = (
                f"no fiscal year of {ticker} ends on {_short(end)}"
                if start == end
                else f"{_short(start)} to {_short(end)} is not one of {ticker}'s fiscal years"
            )
            periods = [period(y) for y in sorted(pinned)]
            listed_periods = (
                periods[0] if len(periods) == 1 else ", ".join(periods[:-1]) + " and " + periods[-1]
            )
            reason = (
                f"{named}; the 10-K data has annual figures only, for {listed_periods}; "
                "ask the user which fiscal year"
            )
            overlapping = [
                y
                for y, last in sorted(pinned.items())
                if (_start(y, pinned) or last - timedelta(days=364)) <= end and start <= last
            ]
            return reject(reason, overlapping or sorted(pinned))
        calendar = read_calendar_years(context.question)
        if calendar:
            company = next((c for c in context.companies if c.ticker == ticker), None)
            if company is not None and company.fiscal_year_end == 12:
                for year in sorted(calendar):
                    asked.setdefault(
                        year,
                        f"the question says calendar {year}, which is {ticker}'s fiscal {year}",
                    )
            else:
                year = min(calendar)
                overlapping = [y for y in (year, year + 1) if y in pinned]
                month = MONTH_NAMES[company.fiscal_year_end - 1] if company else "another month"
                parts = [
                    period(y) if y in pinned else f"fiscal {y} (no 10-K in the dataset)"
                    for y in (year, year + 1)
                ]
                reason = (
                    f"calendar {year} is not one of {ticker}'s fiscal years, which end in {month}; "
                    f"it overlaps {parts[0]} and {parts[1]}; ask the user which fiscal year"
                )
                return reject(reason, overlapping)
        page = context.fiscal_year
        if asked:
            if page is not None and page not in asked:
                reason = (
                    f"the question asks about {_join(sorted(asked))} but the page filter is "
                    f"fiscal {page}; ask the user which one"
                )
                return reject(reason, sorted({*asked, page}))
            if sent in asked:
                return settle(sent, asked[sent])
            if len(asked) == 1:
                ((target, why),) = asked.items()
                return settle(target, why)
            reason = f"the question names {_join(sorted(asked))}; the model sent {sent}"
            return reject(reason, sorted(asked))
        if page is not None:
            return settle(page, f"no year in the question; the user selected fiscal {page}")
        if sent not in pinned:
            return unpinned(sent)
        reason = f"no year in the question; the model's choice stands: {period(sent)}"
        return CheckResult.passed(self.name, "fiscal_year", call.arguments, reason)
