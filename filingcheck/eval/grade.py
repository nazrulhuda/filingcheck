"""The deterministic number grader (Week 3; the LLM grader is Week 5).

Outcomes for a number question (`expected_behavior: answer`):
- correct: a number within `tolerance_pct` of the gold value, and the fiscal year stated;
- year_not_stated: the number matches but the answer does not state the fiscal year;
- other_year_number: the number matches the same metric for another pinned year of the
  company (`gold_other_years`), not the year asked about;
- wrong_number: a number is given but matches nothing;
- no_number: no amount is given and the answer neither declines nor asks;
- asked_when_should_answer: no amount, and the answer asks the user a question instead;
- abstained: the abstain sentence, or a decline in other words with no amount.
A clarify or refuse question is correct when the answer gives no amount and asks or declines
(keyword rules), else answered_when_should_ask. Rows with no answer are error; a number
question with no gold value is not_graded.

The fiscal year is stated by an explicit phrase ("fiscal 2025", "fiscal year 2025", "FY2025",
"FY25", "fiscal '25"), which wins; without one, by a period-end date ("the year ended
January 31, 2025", "as of June 30, 2025", "on June 30, 2025", "... to 2025-01-31") or a year
standing on its own.
A year inside any other date ("filed on February 25, 2026", "from January 27, 2025") counts
for nothing. In all 75 pinned filings the fiscal year is the calendar year of the period end.
"""

import functools
import re
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel

from filingcheck.answer.abstain import ABSTAIN, is_abstain
from filingcheck.answer.citations import (
    MONTH,
    NOT_FIGURES,
    cited_numbers,
    normalize_text,
    parse_fact_citations,
    sentences,
)
from filingcheck.checks.company import find_mentions
from filingcheck.eval.questions import Question
from filingcheck.ingest.companies import Company, load_companies
from filingcheck.paths import DATA_DIR

Outcome = Literal[
    "correct",
    "year_not_stated",
    "other_year_number",
    "wrong_number",
    "no_number",
    "asked_when_should_answer",
    "answered_when_should_ask",
    "asked_about_another_thing",
    "abstained",
    "answered",
    "error",
    "not_graded",
]
OUTCOMES: tuple[Outcome, ...] = (
    "correct",
    "year_not_stated",
    "other_year_number",
    "wrong_number",
    "no_number",
    "asked_when_should_answer",
    "answered_when_should_ask",
    "asked_about_another_thing",
    "abstained",
    "answered",
    "error",
    "not_graded",
)

SCALE_WORDS = {
    "thousand": 10**3,
    "million": 10**6,
    "mn": 10**6,
    "mm": 10**6,
    "mln": 10**6,
    "billion": 10**9,
    "bn": 10**9,
    "bln": 10**9,
    "trillion": 10**12,
}
SCALE_LETTERS = {"k": 10**3, "m": 10**6, "b": 10**9, "t": 10**12}
SCALE_WORD_PATTERN = "|".join(SCALE_WORDS)
# A minus is a sign only when it is attached to the number or the currency sign and no word,
# digit or closing bracket is right before it: "-$1.2 billion" is negative; the dash of a
# range ("$10-12 billion"), of "2024-25", of a list ("revenue - $681 billion") or of a
# subtraction ("713 - 680") is not.
NOT_AFTER_WORD = r"(?<![\w)\]])"
NUMBER_RE = re.compile(
    r"(?P<sign>" + NOT_AFTER_WORD + r"-(?=[\d$.(]))?"
    r"(?P<open>\()?\s?(?P<cur>\$)?\s?(?P<sign2>" + NOT_AFTER_WORD + r"-(?=[\d.(]))?(?P<open2>\()?"
    r"(?P<num>(?<![\w.,])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+))(?![\d,]\d)"
    r"(?P<close>\))?"
    r"(?:\s?(?P<pct>%|(?i:percent)\b)"
    r"|(?:\s+|-)?(?P<scale>(?i:" + SCALE_WORD_PATTERN + r"))\b"
    r"|(?P<letter>\s?[KMBTkmbt])\b)?"
    r"(?P<close2>\))?"
)
# The text between the two numbers of a range: "$10-12 billion", "10 to 12%".
RANGE_GAP_RE = re.compile(r"\s*(?:-|to)\s*")
# A number stated as a loss: "a net loss of $10.6 billion", "loss before income taxes of $3B".
# Not the "(loss)" of a label like "Net income (loss)", not "before losses", and not across a
# comma, semicolon or bracket ("Despite the loss, net income was $5 billion").
LOSS_BEFORE_RE = re.compile(
    r"(?<!before )\b(?:loss|losses|deficit)\b(?!\))[^\d$,;()]{0,30}$", re.IGNORECASE
)
RIGHT_QUOTE = chr(0x2019)
# A narrow no-break, no-break or thin space between digit groups is a thousands separator
# ("680 985 000 000" with U+202F); a plain space is not.
GROUP_SPACE_RE = re.compile(
    r"(?<=\d)[" + chr(0x202F) + chr(0x00A0) + chr(0x2009) + r"](?=\d{3}(?!\d))"
)
# A number on one line and its scale word on the next.
SPLIT_SCALE_RE = re.compile(r"(\d)[ \t]*\n\s*(?=(?:" + SCALE_WORD_PATTERN + r")\b)", re.IGNORECASE)
# Dates, removed before numbers are read: long, day-first, month-and-year, ISO and slashed.
DATE_RE = re.compile(
    r"\b" + MONTH + r"\.?\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4}\b"
    r"|\b\d{1,2}\s+" + MONTH + r"\.?,?\s+\d{4}\b"
    r"|\b" + MONTH + r"\.?\s+\d{4}\b"
    r"|\b\d{4}-\d{2}-\d{2}\b"
    r"|\b\d{1,2}/\d{1,2}/\d{2,4}\b"
)
# The words before a date that make it a period's end ("the year ended", "through", "as of").
PERIOD_END_BEFORE_RE = re.compile(
    r"(?:\bended|\bending|\bend(?:ed)?\s+on|\bthrough|\bthru|\bto|\buntil|\bas\s+of|\bat|-"
    r"|(?<!filed )(?<!dated )(?<!issued )\bon)\s*(?:on\s+)?$"
    r"|\d\s+$",  # a date right after another date or number ends a range
    re.IGNORECASE,
)
_YEAR = r"(?:\d{4}|\d{2})(?!\d)(?!-?\s*week)(?!-[KQ]\b)"
FISCAL_PHRASE_RE = re.compile(
    r"\b(?:fiscal(?:[\s-]+years?)?|FY)[\s-]*'?\s*(" + _YEAR + r")"
    r"((?:\s*(?:,|and|&|-|to|through)\s*'?" + _YEAR + r")*)",
    re.IGNORECASE,
)
YEAR_THEN_FISCAL_RE = re.compile(r"(?<!\d)(\d{4})[\s-]+fiscal[\s-]+year\b", re.IGNORECASE)
YEAR_ALONE_RE = re.compile(r"(?<![\d$.,])(?:19|20)\d{2}(?![\d%]|[.,]\d)")
# Asking: one of these phrases, or a question to the user ("...you...?" or "Which ...?").
ASK_PHRASE_RE = re.compile(
    r"\b(?:did you mean|do you mean|could you (?:clarify|specify|confirm|tell)"
    r"|can you (?:clarify|specify|confirm)|please (?:clarify|specify|confirm)|ambiguous"
    r"|(?:please (?:say|tell me)|let me know) which)\b",
    re.IGNORECASE,
)
QUESTION_TO_USER_RE = re.compile(
    r"\byou\b|^\W*(?:which|did|do|does|could|can|would|should|are|is|was|were)\b", re.IGNORECASE
)
# Declining: saying it cannot answer, or that the data is not there.
DECLINE_RE = re.compile(
    r"\b(?:can't|cannot|can not|could not|couldn't|unable to|not able to|won't be able to"
    r"|wasn't able to|was unable to)\s+(?:\w+\s+){0,2}?"
    r"(?:answer|find|provide|give|determine|locate|report|say|tell|confirm|access|see"
    r"|identify|help)\b"
    r"|\b(?:don't|do not|doesn't|does not|didn't|did not)\s+"
    r"(?:have|include|cover|contain|report|provide)\b"
    r"|\b(?:isn't|is not|aren't|are not|not)\s+(?:available|included|loaded|covered)\b"
    r"|\bnot in the (?:filings|data|dataset|10-K)\b|\bunavailable\b"
    r"|\bonly\s+(?:annual|10-K|have)\b|\b10-Q\b|\bno (?:quarterly|such)\b"
    r"|" + re.escape(ABSTAIN),
    re.IGNORECASE,
)
PLACEHOLDER = " _"  # what removed text becomes, so a dash after it is no sign


class Number(BaseModel):
    """A number found in an answer, in raw units (dollars, not millions)."""

    value: Decimal
    percent: bool = False
    # An amount, not a small count: a currency sign, a scale, a percent sign, digit groups,
    # decimals or at least 1,000. "3 months", "25 companies" and a footnote "(1)" are not.
    amount: bool = True


class Figure(BaseModel):
    """A figure as read by `read_figures`: its value and what the number labeler needs beside it."""

    value: Decimal  # raw units, signed
    percent: bool
    amount: bool
    text: str  # as written, after spaces, dashes and brackets are normalized
    decimals: int  # digits shown after the decimal point
    scale: int  # the scale word or letter it was written with, else 1
    currency: bool  # written with a dollar sign
    sentence: str  # its sentence, citation markers kept
    after: str  # the rest of its sentence after it, citation markers removed
    passage_refs: list[int]  # passages its sentence cites, in first-cited order
    fact_refs: list[int]  # facts ([Fn]) its sentence cites, in first-cited order


class Grade(BaseModel):
    """How one answer was graded, and what the grader found in it."""

    outcome: Outcome
    numbers: list[str]  # every number found, raw units; percentages end in "%"
    matched: str | None  # the number that matched the gold value or another year's value
    year_stated: bool
    other_year: int | None = None  # for other_year_number: the year whose value it matched
    # For a clarify question: the grade under the lenient rule, which also counts asking about
    # something else (only which year, when the company is ambiguous) or declining.
    lenient_outcome: Outcome | None = None
    # For a question with `also_accept`: which expectation a correct answer met, and whether the
    # case is left to the LLM grader (a `note` the rules here cannot check).
    accepted_by: Literal["main", "also_accept"] | None = None
    llm_decides: bool = False


def _plain(value: Decimal) -> str:
    return "0" if value == 0 else format(value.normalize(), "f")


def _prepare(text: str) -> str:
    text = GROUP_SPACE_RE.sub(",", text).replace("**", "")  # markdown bold hides a period end
    text = normalize_text(text).replace(RIGHT_QUOTE, "'")
    return SPLIT_SCALE_RE.sub(r"\1 ", text)


def _scale(match: re.Match[str]) -> int | None:
    if match["scale"]:
        return SCALE_WORDS[match["scale"].lower()]
    letter = (match["letter"] or "").strip()
    if not letter:
        return None
    # A single letter is a scale only after a currency sign, or attached and in capitals.
    if match["cur"] or (letter.isupper() and not match["letter"].startswith(" ")):
        return SCALE_LETTERS[letter.lower()]
    return None


# Citation numbers in one sentence are read up to this bound (a run numbers far fewer).
MAX_CITED = 1000


def read_figures(text: str) -> list[Figure]:
    """Every figure in the text, as `find_numbers` reads them, with how each was written."""
    text = DATE_RE.sub(PLACEHOLDER, _prepare(text))
    figures: list[Figure] = []
    for original in sentences(text):
        passage_refs = cited_numbers(original, MAX_CITED)
        fact_refs = parse_fact_citations(original, MAX_CITED)
        sentence = original
        for pattern in NOT_FIGURES:
            sentence = pattern.sub(PLACEHOLDER, sentence)
        matches = list(NUMBER_RE.finditer(sentence))
        scales = [_scale(m) for m in matches]
        percents = [bool(m["pct"]) for m in matches]
        for i in range(len(matches) - 1):  # the first number of a range takes the second's unit
            gap = sentence[matches[i].end() : matches[i + 1].start()]
            if scales[i] is None and not percents[i] and RANGE_GAP_RE.fullmatch(gap):
                scales[i], percents[i] = scales[i + 1], percents[i + 1]
        for match, scale, percent in zip(matches, scales, percents, strict=True):
            digits = match["num"]
            value = Decimal(digits.replace(",", ""))
            amount = bool(
                match["cur"] or scale or percent or "," in digits or "." in digits or value >= 1000
            )
            wrapped = (match["open"] or match["open2"]) and (match["close"] or match["close2"])
            loss = LOSS_BEFORE_RE.search(sentence[: match.start()]) is not None
            if match["sign"] or match["sign2"] or (wrapped and amount) or loss:
                value = -value
            if scale:
                value *= scale
            figures.append(
                Figure(
                    value=value,
                    percent=percent,
                    amount=amount,
                    text=match.group(0).strip(),
                    decimals=len(digits.partition(".")[2]),
                    scale=scale or 1,
                    currency=bool(match["cur"]),
                    sentence=original,
                    after=sentence[match.end() : match.end() + 40],
                    passage_refs=passage_refs,
                    fact_refs=fact_refs,
                )
            )
    return figures


def find_numbers(text: str) -> list[Number]:
    """Every figure in the text in raw units; years, dates, citations and labels are skipped."""
    return [Number(value=f.value, percent=f.percent, amount=f.amount) for f in read_figures(text)]


def _year(digits: str) -> int:
    return int(digits) if len(digits) == 4 else 2000 + int(digits)


def states_year(text: str, fiscal_year: int) -> bool:
    """True if the answer states the fiscal year (see the module docstring for the rule)."""
    text = _prepare(text)
    phrases: set[int] = set()
    for match in FISCAL_PHRASE_RE.finditer(text):
        phrases.add(_year(match.group(1)))
        phrases |= {_year(y) for y in re.findall(r"\d{4}|\d{2}", match.group(2))}
    phrases |= {int(y) for y in YEAR_THEN_FISCAL_RE.findall(text)}
    if phrases:
        return fiscal_year in phrases
    period_ends: set[int] = set()
    for match in DATE_RE.finditer(text):
        if PERIOD_END_BEFORE_RE.search(text[: match.start()]):
            found = re.findall(r"\d{4}", match.group(0)) or [match.group(0)[-2:]]
            period_ends.add(_year(found[-1]))
    alone = {int(y) for y in YEAR_ALONE_RE.findall(DATE_RE.sub(PLACEHOLDER, text))}
    return fiscal_year in period_ends or fiscal_year in alone


def asks(text: str) -> bool:
    """True if the answer asks the user which company or year is meant."""
    text = _prepare(text)
    if ASK_PHRASE_RE.search(text):
        return True
    for sentence in sentences(text):
        if sentence.rstrip(" \"')]*").endswith("?") and QUESTION_TO_USER_RE.search(sentence):
            return True
    return False


def declines(text: str) -> bool:
    """True if the answer says it cannot answer or that the data is not there."""
    return DECLINE_RE.search(_prepare(text)) is not None


# Asking which company: "which company", "which one", "which of them".
# "which company", "which credit-card company", "which of the two", "specify the ticker".
ASK_COMPANY_RE = re.compile(
    r"\bwhich (?:[\w'-]+ ){0,2}(?:company|companies|one|firm|bank|business|issuer"
    r"|of (?:them|these|the two))\b"
    r"|\bwhat company\b|\bspecify the (?:ticker|company)\b",
    re.IGNORECASE,
)
# Asking which year or period: "which fiscal year", "specify the year", "what period".
ASK_YEAR_RE = re.compile(
    r"\b(?:which|what) (?:fiscal )?(?:year|period)\b"
    r"|\b(?:specify|clarify|confirm) (?:the |a |which )?(?:fiscal )?(?:year|period)\b",
    re.IGNORECASE,
)


@functools.cache
def _companies() -> list[Company]:
    return load_companies(DATA_DIR / "companies.yaml")


def addresses_ambiguity(text: str, question: Question) -> bool:
    """Whether a clarify answer asks about what is ambiguous (the strict clarify rule).

    With no company resolved (by the question or its page filter), the company is ambiguous:
    the answer must name at least two companies or ask which company. With a company but no
    fiscal year, the year is: the answer must ask which year or period, or name at least two
    fiscal years.
    """
    text = _prepare(text)
    company = question.company
    if company is None and question.page_filter is not None:
        company = question.page_filter.ticker  # the page resolved the company for the model
    if company is None:
        named = {
            next(iter(m.tickers)) for m in find_mentions(text, _companies()) if len(m.tickers) == 1
        }
        return len(named) >= 2 or ASK_COMPANY_RE.search(text) is not None
    years = {_year(m.group(1)) for m in FISCAL_PHRASE_RE.finditer(text)}
    return ASK_YEAR_RE.search(text) is not None or len(years) >= 2


def asks_or_declines(text: str) -> bool:
    """True if the answer asks which company or year is meant, or declines to answer."""
    return asks(text) or declines(text)


def _within(found: Decimal, gold: Decimal, tolerance_pct: float) -> bool:
    return abs(found - gold) <= abs(gold) * Decimal(str(tolerance_pct)) / 100


def _nearest(
    number: Number, targets: list[tuple[int | None, Decimal]], tolerance_pct: float
) -> tuple[bool, int | None]:
    """Whether the number matches a target within the tolerance, and which year's.

    Two years' values can be inside the tolerance of each other (Coca-Cola's net income was
    10,714 million in FY2023 and 10,631 million in FY2024), so a number goes to the value it is
    closest to; on a tie the gold year (None, first in `targets`) wins.
    """
    best: tuple[Decimal, int, int | None] | None = None
    for order, (year, target) in enumerate(targets):
        if not _within(number.value, target, tolerance_pct):
            continue
        distance = abs(number.value - target) / abs(target) if target else Decimal(0)
        if best is None or (distance, order) < best[:2]:
            best = (distance, order, year)
    return (False, None) if best is None else (True, best[2])


def _closest(
    numbers: list[Number], targets: list[tuple[int | None, Decimal]], tolerance_pct: float
) -> tuple[int | None, str] | None:
    """The year and number the answer lands on: the gold year if any number does.

    Each number goes to its own nearest year. If any number lands on the gold value the
    answer is right; otherwise the first other year hit is named; otherwise nothing.
    """
    other: tuple[int | None, str] | None = None
    for number in numbers:
        if number.percent:
            continue
        matched, year = _nearest(number, targets, tolerance_pct)
        if not matched:
            continue
        if year is None:
            return (None, _plain(number.value))
        if other is None:
            other = (year, _plain(number.value))
    return other


def grade(row: dict[str, Any], question: Question) -> Grade:
    """Grade one batch row against its question (see the module docstring for the rules).

    A question with `also_accept` is correct if the answer meets either expectation, the main one
    first; `accepted_by` records which. A clarify alternative is about the company: the answer
    asks which company, names two or more, or asks whether the question's company is meant.
    """
    main = _grade_one(row, question)
    also = question.also_accept
    if also is None or main.outcome == "error":
        return main
    if main.outcome == "correct":
        return main.model_copy(update={"accepted_by": "main"})
    if also.expected_behavior is not None or also.gold_value is not None:
        alternative = question.model_copy(
            update={
                "expected_behavior": also.expected_behavior or question.expected_behavior,
                "company": None if also.expected_behavior == "clarify" else question.company,
                "fiscal_year": also.fiscal_year or question.fiscal_year,
                "gold_value": also.gold_value,
                "gold_unit": also.gold_unit,
                "gold_other_years": None,
                "also_accept": None,
            }
        )
        other = _grade_one(row, alternative)
        if (
            other.outcome == "asked_about_another_thing"
            and question.company is not None
            and _asks_about(str(row.get("answer")), question.company)
        ):
            other = other.model_copy(update={"outcome": "correct"})
        if other.outcome == "correct":
            return other.model_copy(update={"accepted_by": "also_accept"})
    return main.model_copy(update={"llm_decides": bool(also.note)})


def _asks_about(text: str, ticker: str) -> bool:
    """Whether the answer asks a question back that names this company ("do you mean ...?")."""
    named = {
        next(iter(m.tickers))
        for m in find_mentions(_prepare(text), _companies())
        if len(m.tickers) == 1
    }
    return asks(text) and ticker in named


def _grade_one(row: dict[str, Any], question: Question) -> Grade:
    """Grade one row against one expectation: the question's main one, or its alternative."""
    text = row.get("answer")
    if row.get("error") or text is None:
        return Grade(outcome="error", numbers=[], matched=None, year_stated=False)
    numbers = find_numbers(text)
    shown = [_plain(n.value) + ("%" if n.percent else "") for n in numbers]
    year = question.fiscal_year is not None and states_year(text, question.fiscal_year)

    def result(
        outcome: Outcome,
        matched: str | None = None,
        other: int | None = None,
        lenient: Outcome | None = None,
    ) -> Grade:
        return Grade(
            outcome=outcome,
            numbers=shown,
            matched=matched,
            year_stated=year,
            other_year=other,
            lenient_outcome=lenient,
        )

    amounts = [n for n in numbers if n.amount]
    if question.category == "unanswerable_text":  # correctness is the LLM grader's
        declined = is_abstain(text) or (not amounts and declines(text))
        return result("abstained" if declined else "answered")
    if question.expected_behavior in ("clarify", "refuse"):
        ok = not amounts and asks_or_declines(text)
        lenient: Outcome = "correct" if ok else "answered_when_should_ask"
        if question.expected_behavior == "refuse":
            return result(lenient)
        strict: Outcome = lenient
        if ok and not addresses_ambiguity(text, question):
            strict = "asked_about_another_thing"
        return result(strict, lenient=lenient)
    if row.get("abstained") or is_abstain(text) or (not amounts and declines(text)):
        return result("abstained")
    if not amounts and asks(text):
        return result("asked_when_should_answer")
    if question.gold_value is None:
        return result("not_graded")
    if not any(n.amount or n.percent for n in numbers):
        return result("no_number")
    targets: list[tuple[int | None, Decimal]] = [(None, Decimal(str(question.gold_value)))]
    targets += [(y, Decimal(str(v))) for y, v in sorted((question.gold_other_years or {}).items())]
    found = _closest(numbers, targets, question.tolerance_pct)
    if found is None:
        return result("wrong_number")
    other_year, matched = found
    if other_year is None:
        return result("correct" if year else "year_not_stated", matched)
    return result("other_year_number", matched, other_year)


LABELS = {
    "correct": "Correct",
    "year_not_stated": "Year not stated",
    "other_year_number": "Other year's number",
    "wrong_number": "Wrong number",
    "no_number": "No number",
    "asked_when_should_answer": "Asked when it should have answered",
    "answered_when_should_ask": "Answered when it should have asked",
    "asked_about_another_thing": "Asked about another thing",
    "abstained": "Abstained",
    "answered": "Answered (unanswerable)",
    "error": "Errors",
    "not_graded": "Not graded",
}


def summary_table(
    graded: Sequence[tuple[dict[str, Any], Grade]], *, mode: str, settings: str | None = None
) -> str:
    """One table: a row per question with its outcome counts, cost and time, and a total row."""
    ids = list(dict.fromkeys(row["id"] for row, _ in graded))
    lines = [f"Mode: {mode}" + (f"; {settings}" if settings else ""), ""]
    lines += summary_header("Question")
    for qid in ids:
        lines.append(summary_row(qid, [(r, g) for r, g in graded if r["id"] == qid]))
    lines.append(summary_row("**All**", graded))
    return "\n".join(lines) + "\n"


def summary_header(first: str) -> list[str]:
    """The header and rule lines of a summary table whose first column is `first`."""
    labels = " | ".join(LABELS[o] for o in OUTCOMES)
    return [
        f"| {first} | Answers | {labels} | Correct, lenient clarify rule | Cost | Mean time |",
        "|---|" + "---:|" * (len(OUTCOMES) + 4),
    ]


def summary_row(name: str, part: Sequence[tuple[dict[str, Any], Grade]]) -> str:
    """One summary line: the answers, each outcome's count, the total cost and the mean time."""
    counts = [sum(1 for _, g in part if g.outcome == o) for o in OUTCOMES]
    lenient = sum(1 for _, g in part if (g.lenient_outcome or g.outcome) == "correct")
    costs = [r.get("cost_usd") for r, _ in part]
    cost = "unknown" if None in costs else f"${sum(c for c in costs if c is not None):.6f}"
    times = [r["latency_ms"] for r, _ in part if r.get("latency_ms") is not None]
    mean = f"{sum(times) / len(times) / 1000:.1f} s" if times else "-"
    cells = [name, str(len(part)), *map(str, counts), str(lenient), cost, mean]
    return "| " + " | ".join(cells) + " |"
