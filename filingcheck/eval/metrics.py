"""The pre-registered metrics (eval/PREREGISTRATION.md), as pure functions over rows and questions.

`score_run` turns one stored run (a batch row), its question and its LLM grade into a
`RunScore`: which grader decides, whether the run is correct, confidently wrong (with and
without the number labels, and with both graders), its wrong-argument calls (as run and as
sent), its calls on a segment refusal, whether it abstained, whether a check made a false repair
on a control question, its latency, cost and error. `rate` turns runs into a rate: per question
first (the share of its runs), then the mean over the questions, leaving out questions marked
not scored. Nothing here calls a model or reads a file.
"""

import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

from filingcheck.answer.baseline import ABSTAIN
from filingcheck.eval.grade import Grade, find_numbers, grade
from filingcheck.eval.llm_grade import LlmGrade
from filingcheck.eval.questions import Question

NUMBER_TOOL = "get_financial_fact"
WRONG_OUTCOMES = {"wrong_number", "other_year_number", "answered_when_should_ask"}
WARNINGS = {"conflict", "unverified"}
ERROR_LIMIT = 0.05  # more error rows than this in an arm: stop and ask


@dataclass(frozen=True)
class RunScore:
    """One run, scored by the pre-registered rules; the per-run CSV holds these fields."""

    set_name: str
    id: str
    repeat: int
    arm: str
    category: str
    expected_behavior: str
    graded_by: Literal["number", "text"]
    outcome: str  # the deterministic grader's outcome (strict clarify rule)
    llm_verdict: str | None  # the deciding verdict for a text-graded run, else the second opinion
    correct: bool
    confidently_wrong: bool
    confidently_wrong_no_labels: bool
    confidently_wrong_both_graders: bool
    wrong_arg_ran: int
    wrong_arg_sent: int | None  # None when the run did not record the arguments as sent
    segment_total_calls: int | None  # only on segment_vs_total refusals that name a company
    calls_ran: int
    abstained: bool
    false_repair: bool
    search_repairs: int  # the search-year check's repairs or rejects: listed apart, its design
    latency_ms: float | None
    cost_usd: float
    error: str | None
    scored: bool
    text_ungraded: bool  # a text-graded run with no usable LLM verdict


def _is_text_graded(question: Question, det: Grade) -> bool:
    """Text-graded runs: gold_text questions, unanswerable_text ones, and llm_decides rows."""
    return bool(question.gold_text) or question.category == "unanswerable_text" or det.llm_decides


def _decimal(value: Any) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def key_figures(answer: str, det: Grade) -> list[tuple[Decimal, bool]]:
    """The figures whose warning counts, as (value, percent).

    The matched figure for another year's number; else every figure the grader counts as an
    amount, percentages included.
    """
    if det.outcome == "other_year_number" and det.matched is not None:
        matched = _decimal(det.matched)
        return [(matched, False)] if matched is not None else []
    return [(n.value, n.percent) for n in find_numbers(answer) if n.amount]


def carries_no_warning(row: Mapping[str, Any], figures: list[tuple[Decimal, bool]]) -> bool:
    """True when at least one key figure has no Conflict or Unverified label, or there is none.

    A figure with no label carries no warning; labels cover figures, not sentences.
    """
    if not figures:
        return True
    labels: dict[tuple[Decimal, bool], str] = {}
    for item in row.get("number_labels") or []:
        value = _decimal(item.get("value"))
        if value is not None:
            labels.setdefault((value, bool(item.get("percent"))), str(item.get("label")))
    return any(labels.get(figure) not in WARNINGS for figure in figures)


def _fact_calls(row: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [c for c in row.get("tool_calls") or [] if c.get("name") == NUMBER_TOOL]


def _is_wrong(arguments: Mapping[str, Any], question: Question) -> bool:
    """Whether one number-tool call's arguments are wrong for the question, by the rules."""
    ticker, year = arguments.get("ticker"), arguments.get("fiscal_year")
    if question.expected_behavior == "answer":
        if question.gold_value is None or question.company is None or question.fiscal_year is None:
            return False
        years = {question.fiscal_year}
        if question.also_accept is not None and question.also_accept.fiscal_year is not None:
            years.add(question.also_accept.fiscal_year)
        return ticker != question.company or year not in years
    if question.company is None:  # clarify or refuse, the name fits two companies or none
        return question.page_filter is None
    if question.expected_behavior == "clarify":  # the year is the unclear part
        return ticker != question.company
    return False  # a refusal that names its company


def _as_sent(call: Mapping[str, Any]) -> dict[str, Any] | None:
    """The model's own arguments, with the page filter's defaults as filled in before the checks."""
    sent = call.get("sent_arguments")
    if not isinstance(sent, dict):
        return None
    filled = {k: (call.get("arguments") or {}).get(k) for k in call.get("defaults_applied") or []}
    return {**sent, **filled}


def wrong_argument_calls(row: Mapping[str, Any], question: Question) -> int:
    """Number-tool calls the tool ran (status ok) whose arguments, as run, are wrong."""
    return sum(
        1
        for c in _fact_calls(row)
        if c.get("status") == "ok" and _is_wrong(c.get("arguments") or {}, question)
    )


def wrong_argument_calls_sent(row: Mapping[str, Any], question: Question) -> int | None:
    """Number-tool calls the model sent (ran or stopped by a check) whose own arguments are wrong.

    None when a call did not record the arguments as sent (rows before 2026-11-13).
    """
    calls = [c for c in _fact_calls(row) if c.get("status") in ("ok", "error")]
    sent = [_as_sent(c) for c in calls]
    if any(s is None for s in sent):
        return None
    return sum(1 for s in sent if s is not None and _is_wrong(s, question))


def sent_breakdown(row: Mapping[str, Any], question: Question) -> dict[str, int]:
    """Of the wrong calls as sent: how many were repaired, rejected, or ran unchanged."""
    out = {"repaired": 0, "rejected": 0, "ran unchanged": 0}
    for call in _fact_calls(row):
        sent = _as_sent(call)
        if sent is None or not _is_wrong(sent, question):
            continue
        if call.get("status") == "error":
            out["rejected"] += 1
        elif call.get("status") == "ok":
            ran = call.get("arguments") or {}
            same = all(ran.get(k) == sent.get(k) for k in ("ticker", "fiscal_year", "metric"))
            out["ran unchanged" if same else "repaired"] += 1
    return out


def segment_total_calls(row: Mapping[str, Any], question: Question) -> int | None:
    """On a segment refusal for company C and metric M: the calls for C and M that ran."""
    if question.category != "segment_vs_total" or question.expected_behavior != "refuse":
        return None
    if question.company is None or question.metric is None:
        return None
    return sum(
        1
        for c in _fact_calls(row)
        if c.get("status") == "ok"
        and (c.get("arguments") or {}).get("ticker") == question.company
        and (c.get("arguments") or {}).get("metric") == question.metric
    )


def _tool(entry: Mapping[str, Any]) -> str:
    return str(entry.get("tool") or NUMBER_TOOL)  # records before 2026-11-13 name no tool


def score_run(
    row: Mapping[str, Any],
    question: Question,
    llm: LlmGrade | None,
    *,
    set_name: str,
    arm: str,
) -> RunScore:
    """Score one run by the pre-registered rules (see the module docstring)."""
    det = grade(dict(row), question)
    text_graded = _is_text_graded(question, det)
    verdict = llm.verdict if llm is not None and not llm.error else None
    error = row.get("error") if row.get("error") or row.get("answer") is None else None
    if row.get("answer") is None and error is None:
        error = "no answer"
    if error:
        correct = wrong = False
    elif text_graded:
        correct, wrong = verdict == "correct", verdict == "wrong"
    else:
        correct, wrong = det.outcome == "correct", det.outcome in WRONG_OUTCOMES
    unwarned = carries_no_warning(row, key_figures(str(row.get("answer") or ""), det))
    confidently_wrong = wrong and unwarned
    second_opinion_wrong = llm is not None and llm.use == "second opinion" and verdict == "wrong"
    overrides = row.get("overrides") or []
    is_control = question.category == "control"
    calls_ran = sum(1 for c in _fact_calls(row) if c.get("status") == "ok")
    return RunScore(
        set_name=set_name,
        id=str(row["id"]),
        repeat=int(row.get("repeat", 1)),
        arm=arm,
        category=question.category,
        expected_behavior=question.expected_behavior,
        graded_by="text" if text_graded else "number",
        outcome=det.outcome,
        llm_verdict=verdict,
        correct=correct,
        confidently_wrong=confidently_wrong,
        confidently_wrong_no_labels=wrong,
        confidently_wrong_both_graders=(
            confidently_wrong if text_graded else confidently_wrong and second_opinion_wrong
        ),
        wrong_arg_ran=wrong_argument_calls(row, question),
        wrong_arg_sent=wrong_argument_calls_sent(row, question),
        segment_total_calls=segment_total_calls(row, question),
        calls_ran=calls_ran,
        abstained=det.outcome == "abstained",
        false_repair=is_control
        and any(
            e.get("outcome") in ("repair", "reject") and _tool(e) == NUMBER_TOOL for e in overrides
        ),
        search_repairs=sum(
            1
            for e in overrides
            if is_control
            and _tool(e) == "search_filings"
            and e.get("outcome") in ("repair", "reject")
        ),
        latency_ms=float(row["latency_ms"]) if row.get("latency_ms") is not None else None,
        cost_usd=float(row.get("cost_usd") or 0.0),
        error=error,
        scored=question.scored,
        text_ungraded=text_graded and not error and verdict is None,
    )


def always_abstain(question: Question, llm: LlmGrade | None, *, set_name: str) -> RunScore:
    """The floor: the abstain sentence graded as the answer, by the same graders.

    Its confidently-wrong rate is 0 by definition.
    """
    row = {"id": question.id, "repeat": 1, "answer": ABSTAIN, "latency_ms": None, "cost_usd": 0.0}
    scored = score_run(row, question, llm, set_name=set_name, arm="always-abstain")
    return replace(
        scored,
        confidently_wrong=False,
        confidently_wrong_no_labels=False,
        confidently_wrong_both_graders=False,
    )


def per_question(
    scores: Iterable[RunScore], value: Callable[[RunScore], float | bool | int]
) -> dict[str, float]:
    """Each scored question's mean value over its runs."""
    runs: dict[str, list[float]] = defaultdict(list)
    for s in scores:
        if s.scored:
            runs[s.id].append(float(value(s)))
    return {qid: sum(v) / len(v) for qid, v in runs.items()}


def rate(scores: Iterable[RunScore], value: Callable[[RunScore], float | bool | int]) -> float:
    """Per question first, then the mean over the scored questions (NaN when there are none)."""
    means = per_question(scores, value)
    return sum(means.values()) / len(means) if means else math.nan


def runs_by_question(
    scores: Iterable[RunScore], value: Callable[[RunScore], bool]
) -> dict[str, list[bool]]:
    """Each scored question's runs as booleans, for McNemar's test on the majority."""
    runs: dict[str, list[bool]] = defaultdict(list)
    for s in scores:
        if s.scored:
            runs[s.id].append(bool(value(s)))
    return dict(runs)


def error_share(scores: Iterable[RunScore]) -> float:
    """The share of runs (all of them, scored or not) that are error rows."""
    items = list(scores)
    return sum(1 for s in items if s.error) / len(items) if items else math.nan


def deciding_outcome(score: RunScore) -> str:
    """The outcome the deciding grader gave: the LLM verdict for a text-graded run."""
    if score.error:
        return "error"
    return str(score.llm_verdict) if score.graded_by == "text" else score.outcome


def noise(scores: Iterable[RunScore]) -> float:
    """The share of scored questions whose runs do not all get the same outcome."""
    outcomes: dict[str, set[str]] = defaultdict(set)
    for s in scores:
        if s.scored:
            outcomes[s.id].add(deciding_outcome(s))
    return sum(1 for o in outcomes.values() if len(o) > 1) / len(outcomes) if outcomes else math.nan
