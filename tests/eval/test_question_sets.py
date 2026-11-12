"""The Week 5 question sets: their sizes, coverage and the rules each question follows."""

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

QUESTIONS = Path(__file__).resolve().parents[2] / "eval" / "questions"
TICKERS = {
    "JPM", "GS", "MS", "C", "AXP", "COF", "MCO", "SPGI", "MA", "AAPL", "MSFT", "AMZN", "GOOGL",
    "META", "NVDA", "IBM", "WMT", "COST", "KO", "NKE", "PFE", "JNJ", "UNH", "VZ", "NFLX",
}  # fmt: skip
TRAP_CATEGORIES = {
    "lookalike_company", "wrong_fiscal_year", "relative_year", "units_scale",
    "segment_vs_total", "metric_not_supported", "prompt_injection",
}  # fmt: skip


def rows(name: str) -> list[dict[str, Any]]:
    path = QUESTIONS / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_the_development_trap_set_covers_every_category_and_company() -> None:
    dev = rows("dev_traps.jsonl")
    assert 75 <= len(dev) <= 90
    counts = Counter(r["category"] for r in dev)
    assert set(counts) == TRAP_CATEGORIES
    assert all(10 <= n <= 14 for n in counts.values()), counts
    named = Counter(
        t for r in dev for t in {r["company"], (r.get("page_filter") or {}).get("ticker")} - {None}
    )
    assert {t for t in TICKERS if named[t] < 2} == set(), named
    assert 8 <= sum(1 for r in dev if r.get("page_filter")) <= 12
    assert all(r["id"].startswith("dev-") and r["trap_note"] for r in dev)


def test_every_answer_question_has_a_gold_value_or_a_gold_text() -> None:
    for name in ("dev_traps.jsonl", "control.jsonl"):
        for r in rows(name):
            if r["expected_behavior"] == "answer":
                assert r["gold_value"] is not None or r["gold_text"], r["id"]
            else:
                assert r["gold_value"] is None, r["id"]


def test_the_unanswerable_set_is_ten_refusals_each_with_its_search_terms() -> None:
    una = rows("dev_unanswerable.jsonl")
    assert len(una) == 10
    for r in una:
        assert (r["category"], r["expected_behavior"], r["metric"]) == (
            "unanswerable_text",
            "refuse",
            None,
        )
        assert r["company"] in TICKERS and "Searched:" in r["trap_note"], r["id"]


def test_the_control_set_follows_financebench_s_three_styles() -> None:
    control = rows("control.jsonl")
    assert len(control) == 50
    styles = Counter(r["style"] for r in control)
    assert styles == {"metrics-generated": 20, "domain-relevant": 15, "novel-generated": 15}
    for r in control:
        if r["style"] == "metrics-generated":
            assert r["gold_source"] == "facts", r["id"]
        if r["gold_text"]:
            assert "Key phrase" in (r["trap_note"] or ""), r["id"]


@pytest.mark.parametrize("name", ["dev_traps.jsonl", "dev_unanswerable.jsonl", "control.jsonl"])
def test_a_value_set_by_hand_says_where_in_the_filing_it_comes_from(name: str) -> None:
    for r in rows(name):
        if r.get("gold_source") == "hand":
            assert "10-K" in (r["trap_note"] or ""), r["id"]
