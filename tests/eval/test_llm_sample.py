"""The hand-graded sample for the LLM grader: drawn by seed, in fixed strata, verdicts hidden."""

from filingcheck.eval.llm_sample import Candidate, draw_sample, owner_subset


def candidates(stratum: str, n: int) -> list[Candidate]:
    return [Candidate(key=f"{stratum}-{i}", stratum=stratum) for i in range(n)]


POOL = (
    candidates("text", 30) + candidates("number, not clean", 25) + candidates("number, clean", 40)
)
SIZES = {"text": 15, "number, not clean": 15, "number, clean": 10}


def test_the_sample_has_fifteen_text_fifteen_unclean_and_ten_clean_rows() -> None:
    sample = draw_sample(POOL, SIZES, seed=2026)
    assert len(sample) == 40
    assert {s: sum(1 for c in sample if c.stratum == s) for s in SIZES} == SIZES
    assert len({c.key for c in sample}) == 40


def test_the_same_seed_draws_the_same_rows_and_another_seed_does_not() -> None:
    first = [c.key for c in draw_sample(POOL, SIZES, seed=2026)]
    assert first == [c.key for c in draw_sample(list(reversed(POOL)), SIZES, seed=2026)]
    assert first != [c.key for c in draw_sample(POOL, SIZES, seed=2027)]


def test_the_owner_grades_ten_of_the_forty_picked_by_the_seed() -> None:
    sample = draw_sample(POOL, SIZES, seed=2026)
    ten = owner_subset(sample, 10, seed=2026)
    assert len(ten) == 10 and set(ten) <= {c.key for c in sample}
    assert ten == owner_subset(sample, 10, seed=2026)


def test_the_hidden_file_shows_each_row_without_its_stratum_or_verdict() -> None:
    from filingcheck.eval.llm_sample import HiddenRow, render_hidden

    rows = [
        HiddenRow(
            key="eval/results/2026-11-12_control_agent-checks-on.jsonl:control-131:2",
            question="Where is Nike's headquarters?",
            expected="answer; company NKE, fiscal year 2025",
            reference=["Gold text: Beaverton, Oregon."],
            answer="Beaverton, Oregon [1].",
            passages=[(1, "Our headquarters are in Beaverton, Oregon.")],
            facts=["us-gaap:Revenues = 1 USD (2024-06-01 to 2025-05-31)"],
            owner=True,
        )
    ]
    page = render_hidden(
        rows, title="Hand-graded sample 3 for the LLM grader (2026-11-12)", intro="Drawn by seed 7."
    )
    assert page.startswith(
        "# Hand-graded sample 3 for the LLM grader (2026-11-12)\n\nDrawn by seed 7."
    )
    assert (
        "## 1 **[owner]**" in page and "text" not in page.split("## 1")[1].split("**Question:**")[0]
    )
    assert "**Question:** Where is Nike's headquarters?" in page
    assert "- Gold text: Beaverton, Oregon." in page
    assert "> Beaverton, Oregon [1]." in page
    assert "[1] Our headquarters are in Beaverton, Oregon." in page
    assert "- F1: us-gaap:Revenues = 1 USD (2024-06-01 to 2025-05-31)" in page
    assert page.rstrip().endswith("Verdict: ______  Supported: ______")
    assert "verdict:" not in page.lower().replace("verdict: ______", "")


# ---------------------------------------------------------------- the final run's blind check


def test_the_blind_pool_is_the_text_graded_runs_with_a_verdict() -> None:
    from filingcheck.eval.llm_sample import blind_pool

    grades = {
        "eval/results/f_control_agent-checks-on-final.jsonl": [
            {"id": "control-140", "repeat": 1, "use": "text", "verdict": "correct"},
            {"id": "control-140", "repeat": 2, "use": "text", "verdict": None},  # no verdict
            {"id": "control-001", "repeat": 1, "use": "second opinion", "verdict": "correct"},
        ],
        "eval/results/f_dev_unanswerable_agent-checks-on-final.jsonl": [
            {"id": "una-001", "repeat": 3, "use": "text", "verdict": "abstained"},
        ],
    }
    pool = blind_pool(grades)
    assert [c.key for c in pool] == [
        "eval/results/f_control_agent-checks-on-final.jsonl:control-140:1",
        "eval/results/f_dev_unanswerable_agent-checks-on-final.jsonl:una-001:3",
    ]
    assert {c.stratum for c in pool} == {"text"}


def test_the_verdict_definitions_are_the_grader_prompts_own_words() -> None:
    from pathlib import Path

    from filingcheck.eval.llm_sample import verdict_definitions

    prompt = Path("eval/grader_prompt.md").read_text(encoding="utf-8")
    text = verdict_definitions(prompt)
    assert text.startswith("1. **verdict**, one of:")
    assert "2. **supported**" in text and "Rules:" in text
    assert "**Text questions name no year.**" in text
    for left_out in ("3. **reason**", "4. **evidence**", "Answer with the JSON object only"):
        assert left_out not in text
    for part in text.split("\n"):  # every line is copied from the prompt, none is written here
        assert part in prompt
