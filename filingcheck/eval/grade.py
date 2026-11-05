"""The deterministic number grader (Week 3; the LLM grader is Week 5).

A number question is correct when one of the numbers in the answer, converted to raw units,
is within `tolerance_pct` of the gold value and the fiscal year is stated. A question that
should be clarified or refused is correct when the answer has no number and asks or declines
(keyword rules). Every answer gets one outcome: correct, wrong_number, wrong_year,
answered_when_should_ask (for a refuse question: answered when it should have declined),
abstained, error (no answer), or not_graded (no gold value to grade against).
"""

import re
from collections.abc import Sequence
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel

from filingcheck.answer.baseline import ABSTAIN, is_abstain
from filingcheck.answer.citations import NOT_FIGURES, normalize_text, sentences
from filingcheck.eval.questions import Question

Outcome = Literal[
    "correct",
    "wrong_number",
    "wrong_year",
    "answered_when_should_ask",
    "abstained",
    "error",
    "not_graded",
]
OUTCOMES: tuple[Outcome, ...] = (
    "correct",
    "wrong_number",
    "wrong_year",
    "answered_when_should_ask",
    "abstained",
    "error",
    "not_graded",
)

SCALES = {
    "thousand": 10**3,
    "million": 10**6,
    "mn": 10**6,
    "billion": 10**9,
    "bn": 10**9,
    "trillion": 10**12,
    "K": 10**3,
    "M": 10**6,
    "B": 10**9,
    "T": 10**12,
}
# A number with its sign, currency, parentheses, percent sign or scale word. A minus counts as
# a sign only when no word, digit or closing bracket is right before it ("2024-25" is no sign).
NUMBER_RE = re.compile(
    r"(?P<sign>(?<![\w)\]])-\s?)?"
    r"(?P<open>\()?\s?(?P<cur>\$)?\s?(?P<sign2>-)?(?P<open2>\()?"
    r"(?P<num>(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\w.,])\d+(?:\.\d+)?)(?![\d,]\d)"
    r"(?P<close>\))?"
    r"(?:\s?(?P<pct>%|(?i:percent)\b)"
    r"|\s?(?P<scale>(?i:thousand|million|billion|trillion|bn|mn))\b"
    r"|(?P<letter>[KMBT])\b)?"
)
# Words that make a positive amount in the same sentence a negative one ("a net loss of $1.2B").
RIGHT_QUOTE = chr(0x2019)
# A narrow no-break, no-break or thin space between digit groups is a thousands separator
# ("680 985 000 000" with U+202F); a plain space is not.
GROUP_SPACE_RE = re.compile(
    r"(?<=\d)[" + chr(0x202F) + chr(0x00A0) + chr(0x2009) + r"](?=\d{3}(?!\d))"
)
LOSS_RE = re.compile(r"\b(?:loss|losses|negative|deficit|outflow|used in)\b", re.IGNORECASE)
ASK_RE = re.compile(
    r"\?|\b(?:did you mean|do you mean|could you (?:clarify|specify|confirm)"
    r"|can you (?:clarify|specify|confirm)|please (?:clarify|specify|confirm)|ambiguous)\b",
    re.IGNORECASE,
)
DECLINE_RE = re.compile(
    r"\b(?:can't|cannot|can not|unable|not able|don't have|do not have|not available"
    r"|unavailable|not (?:included|loaded|covered)|only (?:annual|10-K)|10-Q)\b"
    r"|" + re.escape(ABSTAIN),
    re.IGNORECASE,
)


class Number(BaseModel):
    """A number found in an answer, in raw units (dollars, not millions)."""

    value: Decimal
    percent: bool = False
    loss_word: bool = False  # its sentence speaks of a loss, so a positive amount may be one


class Grade(BaseModel):
    """How one answer was graded, and what the grader found in it."""

    outcome: Outcome
    numbers: list[str]  # every number found, raw units; percentages end in "%"
    matched: str | None  # the number that matched the gold value, if any
    year_stated: bool


def _plain(value: Decimal) -> str:
    return "0" if value == 0 else format(value.normalize(), "f")


def find_numbers(text: str) -> list[Number]:
    """Every figure in the text in raw units; years, dates, citations and labels are skipped."""
    numbers: list[Number] = []
    text = GROUP_SPACE_RE.sub(",", text)
    for sentence in sentences(normalize_text(text)):
        loss = bool(LOSS_RE.search(sentence))
        for pattern in NOT_FIGURES:
            sentence = pattern.sub(" ", sentence)
        for match in NUMBER_RE.finditer(sentence):
            value = Decimal(match["num"].replace(",", ""))
            wrapped = (match["open"] or match["open2"]) and match["close"]
            if match["sign"] or match["sign2"] or wrapped:
                value = -value
            scale = match["scale"] or match["letter"]
            if scale:
                value *= SCALES[scale if scale in SCALES else scale.lower()]
            numbers.append(Number(value=value, percent=bool(match["pct"]), loss_word=loss))
    return numbers


def states_year(text: str, fiscal_year: int) -> bool:
    """True if the answer names the fiscal year: 2025, FY2025 or FY25."""
    short = str(fiscal_year)[-2:]
    pattern = rf"(?<!\d){fiscal_year}(?!\d)|\bFY\s?'?{short}(?!\d)"
    return re.search(pattern, normalize_text(text), re.IGNORECASE) is not None


def asks_or_declines(text: str) -> bool:
    """True if the answer asks which company or year is meant, or declines to answer."""
    text = normalize_text(text).replace(RIGHT_QUOTE, "'")  # a curly apostrophe reads as plain
    return bool(ASK_RE.search(text) or DECLINE_RE.search(text))


def _within(found: Decimal, gold: Decimal, tolerance_pct: float) -> bool:
    return abs(found - gold) <= abs(gold) * Decimal(str(tolerance_pct)) / 100


def grade(row: dict[str, Any], question: Question) -> Grade:
    """Grade one batch row against its question (see the module docstring for the rules)."""
    text = row.get("answer")
    if row.get("error") or text is None:
        return Grade(outcome="error", numbers=[], matched=None, year_stated=False)
    numbers = find_numbers(text)
    shown = [_plain(n.value) + ("%" if n.percent else "") for n in numbers]
    year = question.fiscal_year is not None and states_year(text, question.fiscal_year)
    if question.expected_behavior in ("clarify", "refuse"):
        ok = not numbers and asks_or_declines(text)
        outcome: Outcome = "correct" if ok else "answered_when_should_ask"
        return Grade(outcome=outcome, numbers=shown, matched=None, year_stated=year)
    if row.get("abstained") or is_abstain(text):
        return Grade(outcome="abstained", numbers=shown, matched=None, year_stated=year)
    if question.gold_value is None:
        return Grade(outcome="not_graded", numbers=shown, matched=None, year_stated=year)
    gold = Decimal(str(question.gold_value))
    matched = None
    for number in numbers:
        if number.percent:
            continue
        candidates = [number.value]
        if gold < 0 < number.value and number.loss_word:
            candidates.append(-number.value)
        if any(_within(c, gold, question.tolerance_pct) for c in candidates):
            matched = _plain(number.value)
            break
    if matched is None:
        return Grade(outcome="wrong_number", numbers=shown, matched=None, year_stated=year)
    outcome = "correct" if year else "wrong_year"
    return Grade(outcome=outcome, numbers=shown, matched=matched, year_stated=year)


LABELS = {
    "correct": "Correct",
    "wrong_number": "Wrong number",
    "wrong_year": "Wrong year",
    "answered_when_should_ask": "Answered when it should have asked",
    "abstained": "Abstained",
    "error": "Errors",
    "not_graded": "Not graded",
}


def summary_table(
    graded: Sequence[tuple[dict[str, Any], Grade]], *, mode: str, settings: str | None = None
) -> str:
    """One table: a row per question with its outcome counts, cost and time, and a total row."""
    ids = list(dict.fromkeys(row["id"] for row, _ in graded))
    header = (
        "| Question | Answers | "
        + " | ".join(LABELS[o] for o in OUTCOMES)
        + " | Cost | Mean time |"
    )
    lines = [
        f"Mode: {mode}" + (f"; {settings}" if settings else ""),
        "",
        header,
        "|---|" + "---:|" * (len(OUTCOMES) + 3),
    ]

    def line(name: str, part: Sequence[tuple[dict[str, Any], Grade]]) -> str:
        counts = [sum(1 for _, g in part if g.outcome == o) for o in OUTCOMES]
        costs = [r.get("cost_usd") for r, _ in part]
        cost = "unknown" if None in costs else f"${sum(c for c in costs if c is not None):.6f}"
        times = [r["latency_ms"] for r, _ in part if r.get("latency_ms") is not None]
        mean = f"{sum(times) / len(times) / 1000:.1f} s" if times else "-"
        cells = [name, str(len(part)), *map(str, counts), cost, mean]
        return "| " + " | ".join(cells) + " |"

    for qid in ids:
        lines.append(line(qid, [(r, g) for r, g in graded if r["id"] == qid]))
    lines.append(line("**All**", graded))
    return "\n".join(lines) + "\n"
