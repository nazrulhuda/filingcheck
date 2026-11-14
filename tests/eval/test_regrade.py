"""Re-grading stored rows after the decline fix (Day 39 review): what changed, row by row."""

from typing import Any

from filingcheck.eval.grade import asks_or_declines
from filingcheck.eval.regrade import previous_decline_rule, regrade_rows, render_changes, set_for
from tests.eval.test_grade import question, row

REFUSE = question(
    id="trap-067",
    set="trap",
    category="metric_not_supported",
    expected_behavior="refuse",
    style=None,
)
TESLA = "I'm sorry, but Tesla is not one of the 25 companies in the dataset."


def stored(
    answer: str, qid: str = "trap-067", repeat: int = 1, outcome: str = "x"
) -> dict[str, Any]:
    return row(answer, id=qid, repeat=repeat) | {"grade": {"outcome": outcome}}


def test_the_set_is_read_from_the_file_name_longest_first() -> None:
    sets = ["control", "dev_traps", "heldout_traps", "heldout_traps_2"]
    assert set_for("2026-11-12_control_agent-checks-off-search-year.jsonl", sets) == "control"
    assert set_for("2026-11-15_heldout_traps_2_agent-checks-on-final.jsonl", sets) == (
        "heldout_traps_2"
    )
    assert set_for("2026-11-15_heldout_traps_agent-checks-on-final.jsonl", sets) == (
        "heldout_traps"
    )
    assert set_for("2026-11-09_examples_agent.jsonl", sets) is None


def test_the_previous_rule_is_the_grader_before_the_fix_and_is_put_back() -> None:
    assert asks_or_declines(TESLA)
    with previous_decline_rule():
        assert not asks_or_declines(TESLA)
        assert asks_or_declines("I can't find this in the filings I have.")
    assert asks_or_declines(TESLA)


def test_a_refusal_in_the_checks_words_changes_and_nothing_else_does() -> None:
    rows = [
        stored(TESLA, outcome="answered_when_should_ask"),
        stored("I can't find this in the filings I have.", repeat=2, outcome="correct"),
        stored(
            "Tesla's 2024 sales were $97.7 billion.", repeat=3, outcome="answered_when_should_ask"
        ),
        stored(TESLA, qid="gone-001"),  # its question is no longer in the file
    ]
    regraded, skipped = regrade_rows(rows, {"trap-067": REFUSE})
    assert skipped == 1
    assert [(r.repeat, r.before, r.after.outcome, r.changed) for r in regraded] == [
        (1, "answered_when_should_ask", "correct", True),
        (2, "correct", "correct", False),
        (3, "answered_when_should_ask", "answered_when_should_ask", False),
    ]
    assert [r.stored for r in regraded] == [
        "answered_when_should_ask",
        "correct",
        "answered_when_should_ask",
    ]


def test_the_changes_page_lists_every_change_with_its_answer() -> None:
    regraded, _ = regrade_rows(
        [stored(TESLA, outcome="answered_when_should_ask")], {"trap-067": REFUSE}
    )
    page = render_changes({"2026-11-14_dev_traps_agent-prompt-rules.jsonl": regraded}, skipped=0)
    assert "| 2026-11-14_dev_traps_agent-prompt-rules.jsonl | trap-067 | 1 |" in page
    assert "answered_when_should_ask | correct |" in page
    assert "Tesla is not one of the 25 companies" in page
    assert "1 outcome(s) change, in 1 of 1 row(s)" in page
