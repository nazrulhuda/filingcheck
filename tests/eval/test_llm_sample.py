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
