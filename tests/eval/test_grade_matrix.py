"""Generated checks for the grader, so a change is tried against every way of writing a number,
a year and a sentence at once, not against a few hand-picked strings; plus whole answers with a
known outcome and every real model answer we have (eval/results and tests/fixtures)."""

import itertools
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from filingcheck.eval.grade import find_numbers, grade, states_year
from filingcheck.eval.run import read_questions

REPO = Path(__file__).resolve().parents[2]
EN, EM, NNBSP = chr(0x2013), chr(0x2014), chr(0x202F)
GOLD = Decimal("680985000000")

# ---------------------------------------------------------------- amounts: every combination

RENDERINGS = {
    "full": "680,985,000,000",
    "full_nnbsp": f"680{NNBSP}985{NNBSP}000{NNBSP}000",
    "millions": "680,985 million",
    "millions_M": "680,985M",
    "millions_mm": "680,985 mm",
    "billions1": "681.0 billion",
    "billions3": "680.985 billion",
    "billions_B": "681.0B",
    "billions_bn": "681.0 bn",
    "billions_sB": "681.0 B",  # a spaced single letter is a scale only after a currency sign
}
CURRENCIES = {"$": "$", "US$": "US$", "none": "", "USD_after": None}
CONTEXTS = {
    "was": "Walmart's fiscal 2025 revenue was {v}.",
    "colon": "Walmart fiscal 2025 revenue: {v}.",
    "hyphen_spaced": "Walmart fiscal 2025 revenue - {v}.",
    "endash_spaced": f"Walmart fiscal 2025 revenue {EN} {{v}}.",
    "emdash_spaced": f"Walmart fiscal 2025 revenue {EM} {{v}}.",
    "emdash_tight": f"Walmart fiscal 2025 revenue{EM}{{v}}.",
    "bullet": "- Fiscal 2025 total revenues: {v}",
    "bullet_endash": f"- Fiscal 2025 total revenues {EN} {{v}}",
    "bold": "Walmart's fiscal 2025 revenue was **{v}**.",
    "table": "| Fiscal 2025 | Total revenues | {v} |",
    "cite_lenticular": "Walmart's fiscal 2025 revenue was {v}"
    + chr(0x3010)
    + "F1"
    + chr(0x3011)
    + ".",
    "cite_space": "Walmart's fiscal 2025 revenue was {v} [F1].",
    "paren_after": "Walmart's revenue was {v} (fiscal 2025).",
    "newline_before": "Walmart's fiscal 2025 revenue was\n{v}.",
    "approx": "Walmart's fiscal 2025 revenue was about {v}.",
    "tilde": "Walmart's fiscal 2025 revenue was ~{v}.",
    "vs_prior": "Fiscal 2025 revenue was {v}, up from $648.1 billion in fiscal 2024.",
    "prior_first": "Revenue rose from $648.1 billion in fiscal 2024 to {v} in fiscal 2025.",
    "income_loss_label": "Net income (loss) for fiscal 2025: {v}.",
    "formula": "Growth = ({v} - $648,125,000,000) / $648,125,000,000.",
}


def amount_cases() -> list[Any]:
    cases = []
    for (rk, rv), (ck, cv), (xk, xv) in itertools.product(
        RENDERINGS.items(), CURRENCIES.items(), CONTEXTS.items()
    ):
        if rk == "billions_sB" and ck in ("none", "USD_after"):
            continue  # by design: "681.0 B" without a currency sign is not read as billions
        amount = rv + " USD" if cv is None else cv + rv
        cases.append(pytest.param(xv.replace("{v}", amount), id=f"{rk}-{ck}-{xk}"))
    return cases


@pytest.mark.parametrize("text", amount_cases())
def test_the_amount_is_found_in_raw_units_and_positive(text: str) -> None:
    values = [n.value for n in find_numbers(text) if not n.percent]
    assert any(abs(v - GOLD) <= GOLD / 100 for v in values), values
    assert all(v >= 0 for v in values), values


# ---------------------------------------------------------------- years: every phrasing

YEAR_CASES = [
    ("Fiscal 2025 revenue was $681B.", 2025, True),
    ("FY2025 revenue was $681B.", 2025, True),
    ("FY 2025 revenue was $681B.", 2025, True),
    ("FY25 revenue was $681B.", 2025, True),
    ("Fiscal-year 2025 revenue was $681B.", 2025, True),
    ("Revenue for the 2025 fiscal year was $681B.", 2025, True),
    ("Revenue for fiscal year 2025 was $681B.", 2025, True),
    ("Revenue (FY2025) was $681B.", 2025, True),
    ("Revenue in fiscal years 2024 and 2025 was $648B and $681B.", 2025, True),
    ("Revenue in fiscal 2024 and 2025 was $648B and $681B.", 2025, True),
    (f"Revenue in fiscal 2024{EN}2025 rose.", 2025, True),
    ("Revenue in fiscal 2025-26 rose.", 2026, True),
    ("Revenue for the fiscal year ended January 31, 2025 was $681B.", 2025, True),
    ("Revenue for the 52-week fiscal year ended January 31, 2025 was $681B.", 2025, True),
    ("Revenue for the fiscal 52-week year ended January 31, 2025 was $681B.", 2025, True),
    ("Total assets on June 30, 2025 were $619B.", 2025, True),
    ("Total assets at June 30, 2025 were $619B.", 2025, True),
    ("Total assets as of June 30, 2025 were $619B.", 2025, True),
    (f"Net income for 2024-01-29 {EM} 2025-01-26 was $72.9B.", 2025, True),
    ("Net income for 2024-01-29 to 2025-01-26 was $72.9B.", 2025, True),
    ("Net income for January 29, 2024 through January 26, 2025 was $72.9B.", 2025, True),
    ("Its fiscal year 10-K reported $681B for fiscal 2025.", 2025, True),
    ("Revenue in 2025 was $681B.", 2025, True),
    ("Fiscal 2024 revenue was $648B.", 2025, False),
    ("Fiscal 2025 (the year ended January 25, 2026) net income was $120B.", 2026, False),
    ("The 10-K filed on February 25, 2026 reports $120B.", 2026, False),
    ("The 10-K filed in February 2026 reports $120B.", 2026, False),
    ("From January 27, 2025, net income was $120B.", 2025, False),
    ("Net income was $120B.", 2026, False),
    ("The fiscal 52-week year ended January 31, 2025 had sales of $681B.", 2052, False),
]


@pytest.mark.parametrize(("text", "year", "expected"), YEAR_CASES)
def test_the_fiscal_year_rule_on_every_phrasing(text: str, year: int, expected: bool) -> None:
    assert states_year(text, year) == expected


# ---------------------------------------------------------------- whole answers


def questions() -> dict[str, Any]:
    return {q.id: q for q in read_questions(REPO / "eval" / "questions" / "examples.jsonl")}


ANSWER_CASES = [
    ("trap-002", "Walmart's fiscal 2025 revenue was $681.0 billion [F1].", "correct"),
    (
        "trap-002",
        "Fiscal 2025 revenue was $681.0 billion, up from $648.1 billion in fiscal 2024.",
        "correct",
    ),
    (
        "trap-002",
        "Fiscal 2025 revenue was $681.0 billion, up from $648,125 million in fiscal 2024.",
        "correct",
    ),
    (
        "trap-002",
        "Revenue rose from $648,125 million in fiscal 2024 to $680,985 million in fiscal 2025.",
        "correct",
    ),
    ("trap-002", "Fiscal 2025: $680,985 million; fiscal 2026: $713,163 million.", "correct"),
    ("trap-002", f"- Fiscal 2025 total revenues {EN} $680,985 million [F1]", "correct"),
    ("trap-002", f"Total revenues {EN} $681.0 billion for fiscal 2025 [2]", "correct"),
    ("trap-002", "Walmart's fiscal 2025 revenue grew 5.1% to $681.0 billion.", "correct"),
    ("trap-002", "Walmart's fiscal 2026 revenue was $713,163 million [F1].", "other_year_number"),
    (
        "trap-002",
        "Walmart's revenue was $713.2 billion in fiscal 2026 and $681.0 billion in fiscal 2025.",
        "correct",
    ),
    ("trap-002", "Walmart's revenue was $681.0 billion [F1].", "year_not_stated"),
    ("trap-002", "Walmart's fiscal 2025 revenue was $700 billion.", "wrong_number"),
    ("trap-002", "Walmart reports its revenue in Item 8 of its 10-K [1].", "no_number"),
    ("trap-002", "I couldn't find Walmart's revenue in the filings I have.", "abstained"),
    ("control-001", "Coca-Cola's fiscal 2024 net income was $10,631 million [F1].", "correct"),
    (
        "control-001",
        "Coca-Cola's fiscal 2024 net income was $10.6 billion, compared with $10,714 million in "
        "fiscal 2023.",
        "correct",
    ),
    (
        "control-001",
        "Coca-Cola's fiscal 2023 net income was $10,714 million [F1].",
        "other_year_number",
    ),
    (
        "control-001",
        "Net income (loss) attributable to Coca-Cola for fiscal 2024: $10,631 million.",
        "correct",
    ),
    (
        "control-001",
        "Coca-Cola reported a net loss of $10.6 billion in fiscal 2024.",
        "wrong_number",
    ),
    ("trap-003", "Nvidia's fiscal 2026 net income was $120,067 million [F1].", "correct"),
    ("trap-003", "Nvidia's fiscal 2025 net income was $72,880 million [F1].", "other_year_number"),
    (
        "trap-003",
        "Nvidia's net income was $120.1 billion in fiscal 2026, up from $72.9 billion in "
        "fiscal 2025.",
        "correct",
    ),
    (
        "trap-003",
        "Which year do you mean? Nvidia's latest is fiscal 2026.",
        "asked_when_should_answer",
    ),
    ("trap-004", "Microsoft's total assets were $619,003 million on June 30, 2025.", "correct"),
    ("trap-004", "Microsoft's FY2025 total assets: $619,003 million ($619.0 billion).", "correct"),
    (
        "trap-005",
        "I could not find quarterly figures; only annual 10-K filings are loaded.",
        "correct",
    ),
    ("trap-005", "That figure isn't available in the filings I have.", "correct"),
    (
        "trap-005",
        "I can't help with quarterly figures: the dataset has 10-K filings only.",
        "correct",
    ),
    ("trap-005", "The dataset does not include quarterly reports.", "correct"),
    (
        "trap-005",
        "Goldman Sachs's fiscal 2025 net revenue was $58,283 million.",
        "answered_when_should_ask",
    ),
    ("trap-001", "Do you mean Morgan Stanley or JPMorgan Chase?", "correct"),
    (
        "trap-001",
        "Morgan Stanley's fiscal 2025 net revenues were $70,645 million [F1].",
        "answered_when_should_ask",
    ),
    (
        "trap-001",
        "Morgan's net revenue grew strongly, though segments cannot be compared.",
        "answered_when_should_ask",
    ),
]


@pytest.mark.parametrize(("qid", "text", "expected"), ANSWER_CASES)
def test_whole_answers_get_the_expected_outcome(qid: str, text: str, expected: str) -> None:
    row = {"answer": text, "abstained": False, "error": None}
    result = grade(row, questions()[qid])
    assert result.outcome == expected, (result.outcome, result.numbers, result.other_year)


# ---------------------------------------------------------------- real model answers


def real_answers() -> list[Any]:
    rows = [
        json.loads(line)
        for line in (REPO / "tests" / "fixtures" / "real_answers.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    return [pytest.param(r, id=f"{r['source']}-{r['id']}") for r in rows if r.get("answer")]


@pytest.mark.parametrize("row", real_answers())
def test_real_answers_yield_their_amounts_and_no_false_negatives(row: dict[str, Any]) -> None:
    numbers = find_numbers(row["answer"])
    found = {str(n.value.normalize()) + ("%" if n.percent else "") for n in numbers}
    for must in row["must_find"]:
        assert any(
            f == must
            or f == str(Decimal(must.rstrip("%")).normalize()) + ("%" if must.endswith("%") else "")
            for f in found
        ), (must, found)
    assert all(n.value >= 0 for n in numbers), [str(n.value) for n in numbers]


def stored_rows() -> list[Any]:
    cases = []
    for path in sorted((REPO / "eval" / "results").glob("*_examples_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("grade") is not None:
                key = (f"eval/results/{path.name}", row["id"], row.get("repeat", 1))
                cases.append(pytest.param(key, row, id="-".join(map(str, key))))
    return cases


# The grades the Week 5 grader changed, listed with the re-grade
# (eval/results/2026-11-12_regrade.md).
REGRADED = {
    (r["file"], r["id"], r["repeat"]): r
    for r in (
        json.loads(line)
        for line in (REPO / "eval" / "results" / "2026-11-12_regrade.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line
    )
}


@pytest.mark.parametrize(("key", "row"), stored_rows())
def test_the_stored_rows_grade_as_stored_or_as_listed_in_the_regrade(
    key: tuple[str, str, int], row: dict[str, Any]
) -> None:
    graded = grade(row, questions()[row["id"]]).model_dump()
    lenient = graded.pop("lenient_outcome")
    if key in REGRADED:
        listed = REGRADED[key]
        assert (row["grade"]["outcome"], graded["outcome"], lenient) == (
            listed["before"],
            listed["after"],
            listed["lenient"],
        )
        graded["outcome"] = row["grade"]["outcome"]
    assert graded == row["grade"]
    assert lenient in (None, row["grade"]["outcome"]) or key in REGRADED


def test_the_regrade_lists_only_rows_that_exist() -> None:
    keys = {case.values[0] for case in stored_rows()}
    assert set(REGRADED) <= keys and len(REGRADED) == 10
