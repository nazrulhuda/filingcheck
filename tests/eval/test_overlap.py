"""The word-overlap check that keeps new questions from copying old ones."""

from filingcheck.eval.overlap import flagged, overlap, words

RIGHT_QUOTE = chr(0x2019)  # the curly apostrophe models and people type


def test_words_ignore_case_punctuation_and_possessives() -> None:
    assert words("What was Apple's revenue in 2025?") == {
        "what",
        "was",
        "apple",
        "revenue",
        "in",
        "2025",
    }
    assert words(f"S&P Global{RIGHT_QUOTE}s EPS") == {"s&p", "global", "eps"}


def test_overlap_is_shared_words_over_all_words() -> None:
    assert overlap("Apple revenue 2025", "Apple revenue 2025") == 1.0
    assert overlap("Apple revenue 2025", "Costco net income") == 0.0
    # {apple, revenue} shared of {apple, revenue, 2025, 2024}
    assert overlap("Apple revenue 2025", "Apple revenue 2024") == 0.5


def test_a_question_above_the_threshold_is_flagged_with_its_closest_match() -> None:
    new = {"dev-001": "What was Coca-Cola's net income in 2024?", "dev-002": "Who audits Netflix?"}
    refs = {
        "What was Coca-Cola's net income in fiscal 2024?": "probes",
        "What was Apple's net income in fiscal 2024?": "probes",
    }
    (hit,) = flagged(new, refs, threshold=0.6)
    assert (hit.id, hit.reference, hit.source) == (
        "dev-001",
        "What was Coca-Cola's net income in fiscal 2024?",
        "probes",
    )
    assert hit.score > 0.6


def test_a_question_exactly_at_the_threshold_is_not_flagged() -> None:
    # 3 shared of 5 distinct words: 0.6, which is not above 0.6.
    assert flagged({"x-001": "a b c d"}, {"a b c e": "refs"}, threshold=0.6) == []
