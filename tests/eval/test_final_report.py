"""The final report's rules from the pre-registration: the headline, the claim, pooling,
confirmation and the prompt-rules sentence (eval/PREREGISTRATION.md, "Comparisons")."""

from dataclasses import replace

from filingcheck.eval.final_report import (
    Comparison,
    agree,
    claims_reduction,
    compare,
    confirmation_sentences,
    headline,
    s1_sentence,
)
from filingcheck.eval.metrics import score_run
from filingcheck.eval.stats import Interval
from tests.eval.test_metrics import question, row

RIGHT = "Apple's fiscal 2025 revenue was $416.2 billion."
WRONG = "Apple's fiscal 2025 revenue was $5 billion."


def comp(
    estimate: float, low: float, high: float, first: float = 0.2, second: float = 0.1
) -> Comparison:
    return Comparison(
        first=first, second=second, interval=Interval(estimate, low, high), questions=110
    )


# ---------------------------------------------------------------- the headline and the claim


def test_the_headline_is_the_pre_registered_sentence() -> None:
    c = comp(-0.052, -0.091, -0.013, first=0.183, second=0.131)
    assert headline(c) == (
        "On 110 held-out trap questions (3 runs each), turning the checks on changed the "
        "confidently-wrong rate from 18.3% to 13.1% (difference -5.2 points, 95% interval -9.1 "
        "to -1.3)."
    )


def test_a_reduction_is_claimed_only_when_the_interval_is_entirely_below_zero() -> None:
    assert claims_reduction(comp(-0.05, -0.09, -0.01))
    assert not claims_reduction(comp(-0.05, -0.09, 0.0))  # touches zero
    assert not claims_reduction(comp(-0.05, -0.09, 0.02))
    assert not claims_reduction(comp(0.03, 0.01, 0.05))


# ---------------------------------------------------------------- pooling and confirmation


def test_held_out_and_development_agree_only_with_the_same_sign_and_each_inside_the_other() -> None:
    held, dev = comp(-0.05, -0.09, -0.01), comp(-0.07, -0.12, -0.03)
    assert agree(held, dev)
    assert not agree(held, comp(0.02, -0.01, 0.05))  # another sign
    assert not agree(held, comp(-0.11, -0.15, -0.08))  # its estimate outside held-out's interval
    assert not agree(comp(-0.05, -0.06, -0.04), dev)  # dev's estimate outside held-out's
    assert not agree(comp(0.0, -0.02, 0.02), comp(0.0, -0.02, 0.02))  # zero has no sign


def test_the_confirmation_sentences() -> None:
    dev = comp(-0.11, -0.17, -0.05)
    assert confirmation_sentences(comp(-0.05, -0.09, -0.01), dev) == []
    [sentence] = confirmation_sentences(comp(-0.02, -0.06, 0.02), dev)
    assert "do not confirm the development result" in sentence
    assert "-2.0 points (95% interval -6.0 to +2.0)" in sentence
    assert "-11.0 points (95% interval -17.0 to -5.0)" in sentence
    against = confirmation_sentences(comp(0.01, -0.03, 0.05), dev)
    assert len(against) == 2 and "goes against the checks" in against[1]


# ---------------------------------------------------------------- the prompt-rules sentence (S1)


def test_the_prompt_rules_sentence_is_stated_whichever_way_it_comes_out() -> None:
    better = s1_sentence(comp(-0.04, -0.07, -0.01))
    assert better.startswith("The server-side checks did better than the same rules given as")
    same = s1_sentence(comp(-0.01, -0.04, 0.02))
    assert same.startswith("On these questions, the same rules written into the prompt did about")
    assert "a log of every decision" in same
    worse = s1_sentence(comp(0.04, 0.01, 0.07))
    assert worse.startswith("The same rules written into the prompt did better than the server")


# ---------------------------------------------------------------- a paired comparison


def test_a_comparison_is_paired_by_question_with_its_interval_and_mcnemar() -> None:
    first, second = [], []
    for n in range(1, 11):
        q = question(id=f"held-{n:03d}")
        for repeat in (1, 2, 3):
            base = score_run(row(WRONG, id=q.id, repeat=repeat), q, None, set_name="x", arm="off")
            first.append(base)
            good = score_run(row(RIGHT, id=q.id, repeat=repeat), q, None, set_name="x", arm="on")
            second.append(good)
    c = compare(first, second, lambda s: s.correct, majority=True)
    assert (c.first, c.second, c.questions) == (0.0, 1.0, 10)
    assert c.interval.estimate == 1.0 and c.interval.low == 1.0
    assert (c.b, c.c) == (0, 10) and c.p is not None and c.p < 0.01
    unscored = [replace(s, scored=False) if s.id == "held-001" else s for s in second]
    assert compare(first, unscored, lambda s: s.correct, majority=False).questions == 9


def test_one_arms_rate_gets_a_bootstrap_interval_over_questions() -> None:
    """For the charts: the same resampling of questions, the same seed and count."""
    from filingcheck.eval.final_report import rate_interval

    def scores(answers: list[str]) -> list:  # type: ignore[type-arg]
        out = []
        for n, answer in enumerate(answers, 1):
            q = question(id=f"held-{n:03d}")
            out += [
                score_run(row(answer, id=q.id, repeat=r), q, None, set_name="x", arm="a")
                for r in (1, 2, 3)
            ]
        return out

    same = rate_interval(scores([RIGHT] * 8), lambda s: s.correct)
    assert (same.estimate, same.low, same.high) == (1.0, 1.0, 1.0)
    mixed = rate_interval(scores([RIGHT] * 5 + [WRONG] * 5), lambda s: s.correct)
    assert mixed.estimate == 0.5 and 0.0 < mixed.low < 0.5 < mixed.high < 1.0
    assert rate_interval(scores([RIGHT] * 5 + [WRONG] * 5), lambda s: s.correct) == mixed
