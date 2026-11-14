"""The prompt-rules arm: the skeptical checks' rules written into the agent's system prompt.

The Week 6 measurement asks "why not just tell the model the rules?": this arm runs the agent
with the checks off and one block added to the end of the frozen system prompt. The block is
built from the data the checks read (the company list, the not-covered list, the manifest,
the metric map and the checks' word patterns), so it cannot leave out a name, a year or a word
a check knows. It has one instruction for every check in `CHECKS_BY_TOOL`, keyed by the tool
and the check's class, in the checks' own words where they have them, and nothing no check
does. What a prompt cannot copy stays a difference: the checks change or stop a call before
it runs, and the units check hands over the scaled value. The deployed prompt is unchanged.
"""

from collections.abc import Sequence

from filingcheck.agent.graph import system_prompt
from filingcheck.checks import CHECKED_TOOL, CHECKS_BY_TOOL
from filingcheck.checks.base import Check
from filingcheck.checks.company import CompanyCheck
from filingcheck.checks.fiscal_year import (
    MONTH_NAMES,
    RELATIVE,
    FiscalYearCheck,
    SearchYearCheck,
    period_text,
)
from filingcheck.checks.metric import QUARTER_RE, SUPPORTED, UNSUPPORTED_RE, MetricCheck
from filingcheck.checks.segment import EXCLUDED_BEFORE_RE, INCLUDE_RE, SegmentCheck
from filingcheck.checks.units import SCALES, UnitsCheck
from filingcheck.facts.metrics import METRICS
from filingcheck.ingest.companies import Company
from filingcheck.ingest.filings import Manifest

SEARCH_TOOL = "search_filings"


# ---------------------------------------------------------------- the phrases a pattern matches


def expand(pattern: str) -> list[str]:
    r"""Every phrase a check's word pattern matches, in order, for listing in the block.

    Handles what the checks' word patterns use: literals, `(?:...)` groups, `|`, `?`, simple
    character classes, `\b`, `\s` (one space, or none with `*`) and the anchors `^` and `$`.
    Anything else raises ValueError rather than listing words the pattern does not match.
    """
    phrases, end = _alternation(pattern, 0)
    if end != len(pattern):
        raise ValueError(f"unbalanced ')' at {end} in {pattern!r}")
    return list(dict.fromkeys(phrases))


def _alternation(p: str, i: int) -> tuple[list[str], int]:
    options, i = _sequence(p, i)
    while i < len(p) and p[i] == "|":
        more, i = _sequence(p, i + 1)
        options += more
    return options, i


def _sequence(p: str, i: int) -> tuple[list[str], int]:
    phrases = [""]
    while i < len(p) and p[i] not in "|)":
        atom, i = _atom(p, i)
        if i < len(p) and p[i] in "?*+":
            if p[i] == "?":
                atom = ["", *atom]
            elif p[i] == "*":
                atom = [""]
            i += 1  # "+": once
        phrases = [a + b for a in phrases for b in atom]
    return phrases, i


def _atom(p: str, i: int) -> tuple[list[str], int]:
    c = p[i]
    if c == "(":
        if not p.startswith("(?:", i):
            raise ValueError(f"only (?:...) groups are listed, at {i} in {p!r}")
        inner, j = _alternation(p, i + 3)
        if j >= len(p) or p[j] != ")":
            raise ValueError(f"unclosed group at {i} in {p!r}")
        return inner, j + 1
    if c == "[":
        j = p.index("]", i + 1)
        body, chars, k = p[i + 1 : j], [], 0
        while k < len(body):
            if k + 2 < len(body) and body[k + 1] == "-":
                chars += [chr(x) for x in range(ord(body[k]), ord(body[k + 2]) + 1)]
                k += 3
            else:
                chars.append(body[k])
                k += 1
        return chars, j + 1
    if c == "\\":
        escaped = p[i + 1]
        if escaped == "b":
            return [""], i + 2
        if escaped == "s":
            return [" "], i + 2
        if escaped.isalnum():
            raise ValueError(f"\\{escaped} is not listed, at {i} in {p!r}")
        return [escaped], i + 2
    if c in "^$":
        return [""], i + 1
    if c in ".{}":
        raise ValueError(f"{c!r} is not listed, at {i} in {p!r}")
    return [c], i + 1


def _quoted(words: Sequence[str]) -> str:
    return ", ".join(f'"{w}"' for w in words)


def _join(items: Sequence[str], last: str = "and") -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + f" {last} " + items[-1]


def _either(words: Sequence[str]) -> str:
    return _join([f'"{w}"' for w in words], "or")


# ---------------------------------------------------------------- one instruction per check

_RELATIVE_MEANING = {
    (0, "latest"): "the latest fiscal year held (marked above)",
    (1, "stated"): (
        "the fiscal year before the one the question names (with none named, the year "
        "before the latest)"
    ),
    (2, "latest"): "two fiscal years before the latest",
}
_RELATIVE = "; ".join(
    f"{_quoted(expand(pattern))}: {_RELATIVE_MEANING[(back, reference)]}"
    for pattern, back, reference in RELATIVE
)
_EXCLUDED = [
    word.strip() for word in expand(EXCLUDED_BEFORE_RE.pattern) if not word.strip().endswith(" the")
]
_SCALE_WORDS = [f'"in {scale}"' for scale in SCALES.values()]
_SCALE_LETTERS = [f'"in ${letter.upper()}"' for letter in SCALES]

RULE_LINES: dict[tuple[str, type[Check]], str] = {
    (CHECKED_TOOL, CompanyCheck): (
        "- Company (get_financial_fact's ticker): use the company the question names; with none "
        "named, the company the user selected. If the question names two or more companies, "
        "use only those. A name that fits two or more companies (listed above): the "
        "question's company is ambiguous; ask the user which one. A company that is not one "
        "of the 25 (such as those listed as not in the dataset): say it is not in the dataset. "
        "If the question names one company and the user selected another, ask the user which "
        "one."
    ),
    (CHECKED_TOOL, FiscalYearCheck): (
        '- Fiscal year (get_financial_fact\'s fiscal_year): a year in the question ("2025", '
        '"fiscal 2025", "FY2025", "FY25") is the fiscal-year label; "the year ended <date>" or '
        '"as of <date>" is the fiscal year that ends within a week of that date; a date range '
        "one fiscal year long is the fiscal year ending on its second date. With no year in "
        f"the question, use the fiscal year the user selected. {_RELATIVE}. A year the company "
        "has no 10-K for: say the company has no 10-K for fiscal <year> in the dataset, and "
        "give the fiscal years held. A date or range that is no fiscal year of the company: "
        'the 10-K data has annual figures only; ask the user which fiscal year. "Calendar '
        '<year>" for a company whose fiscal year ends in December is that fiscal year; for '
        "any other company, calendar <year> is not one of its fiscal years: it overlaps fiscal "
        "<year> and fiscal <year + 1>; ask the user which fiscal year. If the question names "
        "a year and the user selected another, ask the user which one."
    ),
    (CHECKED_TOOL, MetricCheck): (
        "- Metric and period (get_financial_fact's metric): the dataset has annual figures only "
        f"(10-K); no quarterly periods: for {_quoted(expand(QUARTER_RE.pattern))}, say so. "
        f"{_quoted(expand(UNSUPPORTED_RE.pattern))}: each is not one of the 13 metrics the data "
        "holds; say so, and if the question also names one of the 13 metrics, look that one up. "
        "The question's words for the 13 metrics are listed above."
    ),
    (CHECKED_TOOL, UnitsCheck): (
        f"- Units: a figure asked {_join(_SCALE_WORDS, 'or')} (or {', '.join(_SCALE_LETTERS)}, "
        '"($ in millions)"): the user asked for that scale; the figure in that scale goes '
        "next to the raw value."
    ),
    (CHECKED_TOOL, SegmentCheck): (
        "- Segments: for a figure of a segment or product (the names listed for each company "
        "above), the fact tool returns company totals only; segment figures are not "
        "supported; use search_filings for the text or say so. A total with a segment named "
        f"after {_either(expand(INCLUDE_RE.pattern))} is the company total; a total with a "
        f"segment named after {_either(_EXCLUDED)} is a figure the 10-K data does not hold: "
        "say so."
    ),
    (SEARCH_TOOL, SearchYearCheck): (
        "- Fiscal year (search_filings' fiscal_year): the same year rules as for "
        "get_financial_fact; when neither the question nor the user's selection names a year, "
        "search the latest fiscal year's filing (marked above)."
    ),
}
LAST_LINE = (
    "- State the fiscal year and the period for every figure, as in fiscal 2025 "
    "(Feb 1, 2024 to Jan 31, 2025)."
)


# ---------------------------------------------------------------- the block


def _years(company: Company, manifest: Manifest) -> str:
    years = sorted({f.fiscal_year for f in manifest.filings if f.ticker == company.ticker})
    parts = [period_text(company.ticker, year, manifest) for year in years]
    if parts:
        parts[-1] = parts[-1][:-1] + "; the latest)"
    return ", ".join(parts)


def _company_line(company: Company, manifest: Manifest) -> str:
    month = MONTH_NAMES[company.fiscal_year_end - 1]
    names = ", ".join(company.aliases)
    line = (
        f"- {company.name} ({company.ticker}): also {names}; fiscal year ends in {month}; "
        f"fiscal years held: {_years(company, manifest)}"
    )
    if company.segments:
        line += f"; segments and products: {', '.join(company.segments)}"
    return line + "."


def rules_block(companies: list[Company], not_covered: list[str], manifest: Manifest) -> str:
    """The block for the end of the system prompt, from the data the checks read.

    Raises ValueError if a check in `CHECKS_BY_TOOL` has no instruction.
    """
    by_ticker = {c.ticker: c for c in companies}
    lookalikes: dict[str, list[str]] = {}
    for company in companies:
        for word in company.lookalikes:
            lookalikes.setdefault(word, []).append(company.ticker)
    fits = "; ".join(
        f'"{word}": ' + _join([f"{by_ticker[t].name} ({t})" for t in tickers], "or")
        for word, tickers in lookalikes.items()
    )
    lines = [
        "The data and its rules.",
        "",
        f"The {len(companies)} companies in the dataset, each with the other names a question "
        "may use, the month its fiscal year ends, the fiscal years held with their periods "
        "(the latest marked) and the segment and product names people ask about:",
        *(_company_line(c, manifest) for c in companies),
        f"Names that fit two or more companies: {fits}.",
        f"Well-known companies not in the dataset: {', '.join(not_covered)}.",
        "",
        f"The {len(METRICS)} metrics, annual figures only and company totals only: "
        f"{', '.join(METRICS)}. The question's words for them (the longest words first):",
        *(f"- {_quoted(expand(pattern))}: {metric}" for pattern, metric in SUPPORTED),
        "",
        "Rules:",
    ]
    for tool, checks in CHECKS_BY_TOOL.items():
        for check in checks:
            line = RULE_LINES.get((tool, type(check)))
            if line is None:
                raise ValueError(
                    f"no instruction for {type(check).__name__} on {tool}: add one to RULE_LINES"
                )
            lines.append(line)
    lines.append(LAST_LINE)
    return "\n".join(lines)


__all__ = ["LAST_LINE", "RULE_LINES", "expand", "rules_block", "system_prompt"]
