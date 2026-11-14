"""The final report (Week 6, Day 41): the pre-registered comparisons and their sentences.

Everything here follows `eval/PREREGISTRATION.md` ("Comparisons"): every comparison is paired
by question, with the 95% bootstrap interval of the difference (second minus first) and, for
accuracy and confidently wrong, McNemar's exact test on each question's majority. A reduction
in the primary outcome is claimed only when its interval lies entirely below zero; held-out
and development are pooled only when they agree; the prompt-rules sentence is stated
whichever way it comes out. Nothing here calls a model; the report reads committed rows only.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from filingcheck.eval.metrics import RunScore, per_question, runs_by_question
from filingcheck.eval.stats import Interval, mcnemar, paired_bootstrap

Value = Callable[[RunScore], float | bool | int]


@dataclass(frozen=True)
class Comparison:
    """Two arms on the same questions: each arm's rate, the difference's interval, McNemar."""

    first: float
    second: float
    interval: Interval  # second minus first
    questions: int
    b: int | None = None  # yes in the first arm, no in the second (each question's majority)
    c: int | None = None
    p: float | None = None


def compare(
    first: Sequence[RunScore], second: Sequence[RunScore], value: Value, *, majority: bool
) -> Comparison:
    """The paired comparison of two arms over the scored questions both of them ran."""
    a, b = per_question(first, value), per_question(second, value)
    shared = sorted(set(a) & set(b))
    a, b = {k: a[k] for k in shared}, {k: b[k] for k in shared}
    interval = paired_bootstrap(a, b)
    result = Comparison(
        first=sum(a.values()) / len(a),
        second=sum(b.values()) / len(b),
        interval=interval,
        questions=len(shared),
    )
    if not majority:
        return result
    runs_a = runs_by_question(first, lambda s: bool(value(s)))
    runs_b = runs_by_question(second, lambda s: bool(value(s)))
    bb, cc, p = mcnemar({k: runs_a[k] for k in shared}, {k: runs_b[k] for k in shared})
    return Comparison(result.first, result.second, interval, len(shared), bb, cc, p)


def _pct(value: float) -> str:
    return f"{100 * value:.1f}%"


def _signed(value: float) -> str:
    return f"{100 * value:+.1f}"


def _difference(c: Comparison) -> str:
    i = c.interval
    return f"{_signed(i.estimate)} points (95% interval {_signed(i.low)} to {_signed(i.high)})"


def headline(c: Comparison) -> str:
    """The pre-registered headline sentence, filled in from the primary comparison."""
    i = c.interval
    return (
        f"On {c.questions} held-out trap questions (3 runs each), turning the checks on changed "
        f"the confidently-wrong rate from {_pct(c.first)} to {_pct(c.second)} (difference "
        f"{100 * i.estimate:.1f} points, 95% interval {100 * i.low:.1f} to {100 * i.high:.1f})."
    )


def claims_reduction(c: Comparison) -> bool:
    """A reduction is claimed only if the difference's 95% interval lies entirely below zero."""
    return c.interval.high < 0


def agree(held: Comparison, dev: Comparison) -> bool:
    """Held-out and development agree: the same sign, and each estimate in the other's interval.

    An estimate of exactly zero has no sign, so it agrees with nothing.
    """
    a, b = held.interval, dev.interval
    same_sign = (a.estimate > 0 and b.estimate > 0) or (a.estimate < 0 and b.estimate < 0)
    return same_sign and b.low <= a.estimate <= b.high and a.low <= b.estimate <= a.high


def confirmation_sentences(held: Comparison, dev: Comparison) -> list[str]:
    """What the README must say if the held-out set does not confirm the development result."""
    sentences: list[str] = []
    i = held.interval
    if i.low <= 0 <= i.high:
        sentences.append(
            "The held-out questions do not confirm the development result: held-out "
            f"{_difference(held)}, development {_difference(dev)}."
        )
    if i.estimate > 0:
        sentences.append(
            "On the held-out questions the estimate goes against the checks: with them on, "
            f"the confidently-wrong rate is higher by {_difference(held)}."
        )
    return sentences


def s1_sentence(c: Comparison) -> str:
    """The prompt-rules sentence (S1), on confidently wrong: checks on minus prompt rules."""
    i = c.interval
    if i.high < 0:
        return (
            "The server-side checks did better than the same rules given as instructions: "
            f"confidently wrong {_difference(c)} with the checks on against the prompt rules."
        )
    if i.low > 0:
        return (
            "The same rules written into the prompt did better than the server-side checks: "
            f"confidently wrong {_difference(c)} with the checks on against the prompt rules."
        )
    return (
        "On these questions, the same rules written into the prompt did about as well as the "
        "server-side checks; the checks add enforcement that does not depend on the model "
        "following instructions, and a log of every decision (confidently wrong "
        f"{_difference(c)} with the checks on against the prompt rules)."
    )
