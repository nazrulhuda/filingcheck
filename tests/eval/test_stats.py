"""The paired bootstrap clustered by question, and McNemar's exact test (the pre-registration)."""

import pytest

from filingcheck.eval.stats import SEED, majority, mcnemar, mcnemar_exact, paired_bootstrap


def test_identical_arms_give_a_zero_difference_and_a_zero_interval() -> None:
    a = {f"q-{n}": n / 10 for n in range(20)}
    result = paired_bootstrap(a, dict(a))
    assert (result.estimate, result.low, result.high) == (0.0, 0.0, 0.0)


def test_when_every_question_improves_the_interval_lies_above_zero() -> None:
    a = {f"q-{n}": 0.2 for n in range(30)}
    b = {f"q-{n}": 0.2 + (n % 3 + 1) / 10 for n in range(30)}
    result = paired_bootstrap(a, b)
    assert result.low > 0 and result.estimate == pytest.approx(0.2)
    assert result.low <= result.estimate <= result.high


def test_the_same_seed_gives_the_same_interval() -> None:
    a = {f"q-{n}": (n * 7 % 10) / 10 for n in range(40)}
    b = {f"q-{n}": (n * 3 % 10) / 10 for n in range(40)}
    assert paired_bootstrap(a, b) == paired_bootstrap(a, b, seed=SEED)
    assert SEED == 20261113


def test_the_two_arms_must_hold_the_same_questions() -> None:
    with pytest.raises(ValueError, match="same questions"):
        paired_bootstrap({"q-1": 1.0}, {"q-2": 1.0})


def test_mcnemars_exact_test() -> None:
    assert mcnemar_exact(10, 2) == pytest.approx(0.0386, abs=0.00005)
    assert mcnemar_exact(5, 5) == 1.0
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(2, 10) == mcnemar_exact(10, 2)


def test_mcnemar_uses_each_questions_majority_of_its_three_runs() -> None:
    assert majority([True, True, False]) is True and majority([True, False, False]) is False
    a = {"q-1": [True, True, True], "q-2": [True, True, False], "q-3": [False, False, False]}
    b = {"q-1": [False, False, False], "q-2": [False, True, False], "q-3": [False, True, True]}
    # b counts questions yes in the first arm and no in the second; c the other way round.
    assert mcnemar(a, b)[:2] == (2, 1)
