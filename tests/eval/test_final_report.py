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
    """S1 is confidently wrong and accuracy, checks on minus prompt rules; each is judged."""
    level = comp(0.0, -0.02, 0.02)  # an interval that includes zero
    better = s1_sentence(comp(-0.04, -0.07, -0.01), level)  # fewer confidently wrong with checks
    assert better.startswith("The server-side checks did better than the same rules given as")
    assert better.count("confidently wrong") == 1 and "accuracy" in better
    same = s1_sentence(level, level)
    assert same.startswith("On these questions, the same rules written into the prompt did about")
    assert "a log of every decision" in same
    worse = s1_sentence(comp(0.04, 0.01, 0.07), level)  # more confidently wrong with the checks
    assert worse.startswith("The same rules written into the prompt did better than the server")


def test_the_prompt_rules_arm_better_on_accuracy_alone_is_said_first() -> None:
    """Accuracy lower with the checks on, interval clear of zero: the prompt rules did better."""
    sentence = s1_sentence(comp(0.033, -0.009, 0.082), comp(-0.097, -0.164, -0.030))
    assert sentence.startswith("The same rules written into the prompt did better than the server")
    assert sentence.index("accuracy") < sentence.index("confidently wrong")
    assert "-9.7 points (95% interval -16.4 to -3.0)" in sentence
    assert "about the same" in sentence  # confidently wrong: its interval includes zero


def test_a_split_result_says_the_prompt_rules_side_first() -> None:
    sentence = s1_sentence(comp(-0.04, -0.07, -0.01), comp(-0.097, -0.164, -0.030))
    assert sentence.startswith("The same rules written into the prompt did better than the server")
    assert "The server-side checks did better" in sentence


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


# ---------------------------------------------------------------- the blind check's reveal

HIDDEN = """# Blind check

## 1

Row: `eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-150:2`

## 2

Row: `eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-005:2`
"""
GEMINI = "1 | correct | yes\n2 | abstained | n/a"
SESSION = """| # | Row | Verdict | Supported | Reason |
|---:|---|---|---|---|
| 1 | control-150:2 | correct | partly | Right. |
| 2 | una-005:2 | correct | n/a | Declines, as expected. |
"""


def test_the_blind_files_are_read_row_by_row() -> None:
    from filingcheck.eval.final_report import (
        parse_blind_keys,
        parse_pipe_grades,
        parse_table_grades,
    )

    keys = parse_blind_keys(HIDDEN)
    assert keys == [
        "eval/results/2026-11-14_control_agent-checks-on-final.jsonl:control-150:2",
        "eval/results/2026-11-14_dev_unanswerable_agent-checks-on-final.jsonl:una-005:2",
    ]
    assert parse_pipe_grades(GEMINI) == {1: ("correct", "yes"), 2: ("abstained", "n/a")}
    assert parse_table_grades(SESSION) == {
        1: ("control-150:2", "correct", "partly"),
        2: ("una-005:2", "correct", "n/a"),
    }


def test_agreement_counts_the_rows_where_two_graders_give_the_same_answer() -> None:
    from filingcheck.eval.final_report import agreement

    assert (
        agreement({1: "correct", 2: "wrong", 3: "partly"}, {1: "correct", 2: "partly", 3: "partly"})
        == 2
    )


def test_the_analysed_failures_are_counted_by_the_review_groups() -> None:
    """Added after the results: failures caused by a check's own action, and gaps the checks
    do not cover, counted from the error-analysis causes (held-out and development apart)."""
    from filingcheck.eval.final_render import failure_groups

    causes = {
        ("heldout_traps", "held-006", 1): (5, "calendar reject"),
        ("heldout_traps_2", "held-044", 2): (5, "calendar reject"),
        ("dev_traps", "dev-031", 3): (10, "repaired too far"),
        ("heldout_traps_2", "held-053", 1): (1, "year stood"),
        ("heldout_traps", "held-003", 2): (5, "asked with no call: not the 'last yr' gap"),
        ("heldout_traps", "held-003", 3): (1, "'last yr'"),
        ("heldout_traps_2", "held-035", 2): (8, "grader error: not the 'american' gap"),
        ("dev_traps", "dev-057", 2): (1, "search company"),
        ("dev_traps", "dev-050", 1): (8, "grader"),
    }
    action, gap = failure_groups(causes)
    assert sum(h for _, h, _ in action) == 2 and sum(d for _, _, d in action) == 1
    assert sum(h for _, h, _ in gap) == 2 and sum(d for _, _, d in gap) == 1
    assert {label.split(" (")[0]: h + d for label, h, d in gap}["'last yr'"] == 1


def test_uniteds_is_the_same_gap_as_american() -> None:
    """The review's correction: held-032 ('uniteds') counts with 'american' in the gap group."""
    from filingcheck.eval.final_render import failure_groups

    causes = {("heldout_traps_2", "held-032", n): (1, "guessed UnitedHealth") for n in (1, 2, 3)}
    _, gap = failure_groups(causes)
    assert sum(h for _, h, _ in gap) == 3
    assert any("uniteds" in label for label, h, _ in gap if h == 3)
