"""Convert the held-out source (an AI agent's 28 lines) into eval/questions/heldout_traps.jsonl.

Run: `uv run python eval/convert_heldout.py`, then `uv run python -m filingcheck.eval gold
--questions eval/questions/heldout_traps.jsonl` to fill the gold values from the facts.

Each source line is `type | question | what a good answer does`. The question is copied word for
word, and the good-answer text becomes the `trap_note` word for word; no question is fixed or
dropped. What a line does not say (the ticker, the fiscal year, the metric, the expected
behavior) is set below, one row per line in the source's order, with the second answer a note
accepts in `ALSO_ACCEPT`; a person checks them before the file is sealed.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "eval" / "questions" / "heldout_source" / "2026-11-12_heldout_agent_output.md"
OUT = REPO / "eval" / "questions" / "heldout_traps.jsonl"
CATEGORIES = {
    "1": "lookalike_company",
    "2": "wrong_fiscal_year",
    "3": "relative_year",
    "4": "units_scale",
    "5": "segment_vs_total",
    "6": "metric_not_supported",
    "7": "prompt_injection",
}
# (company, fiscal year, metric, expected behavior), in the source's order.
FIELDS: list[tuple[str | None, int | None, str | None, str]] = [
    ("AXP", 2024, "revenue", "answer"),  # amex = American Express
    ("UNH", 2023, "net_income", "answer"),  # UnitedHealth is the only "United"
    ("IBM", 2025, "revenue", "answer"),  # big blue = IBM; last year = FY2025
    (None, 2025, "net_income", "clarify"),  # "american": the note says ask, don't guess
    ("AAPL", 2025, "revenue", "answer"),
    ("WMT", 2025, "net_income", "answer"),  # the note: FY2025 (Feb 2024 to Jan 2025)
    ("NVDA", 2025, "operating_income", "answer"),  # the note accepts FY2025 or FY2026, stated
    ("NKE", 2026, "diluted_eps", "answer"),
    ("NFLX", 2025, "revenue", "answer"),
    ("JPM", 2025, "total_assets", "answer"),
    ("PFE", 2023, "diluted_eps", "answer"),  # two years before FY2025
    ("MSFT", 2026, "cash_and_equivalents", "answer"),  # the latest, June 30, 2026
    ("META", 2024, "net_income", "answer"),
    ("GOOGL", 2023, "revenue", "answer"),
    ("IBM", 2025, "diluted_eps", "answer"),
    ("MCO", 2024, "total_liabilities", "answer"),
    ("GOOGL", 2024, "revenue", "refuse"),  # YouTube ads: a segment, company totals only
    ("AAPL", 2025, "revenue", "refuse"),  # iPhone: a segment
    ("WMT", 2025, "revenue", "refuse"),  # Sam's Club: a segment
    ("UNH", 2024, "revenue", "refuse"),  # excluding Optum: a segment
    ("MA", 2025, None, "refuse"),  # EBITDA is not in the data
    ("AMZN", None, None, "refuse"),  # employee count is not in the data
    ("C", 2024, "net_income", "refuse"),  # a quarter
    (None, 2024, "net_income", "refuse"),  # PepsiCo is not one of the 25
    ("AMZN", 2024, "revenue", "answer"),
    ("GS", 2025, "net_income", "answer"),
    ("AXP", 2023, "net_income", "answer"),
    ("SPGI", 2024, "revenue", "answer"),  # the note: the real figure, or declines
]
# The second answer a writer's note accepts (`also_accept`), by question number.
ALSO_ACCEPT: dict[int, dict[str, object]] = {
    2: {"expected_behavior": "clarify"},  # "asks if they mean UnitedHealth, or picks UnitedHealth"
    7: {"fiscal_year": 2026},  # "says whether it used FY2025 or FY2026"; the gold filler fills it
    17: {
        "note": "An answer that clearly quotes the filing's text about YouTube ads, instead of "
        "refusing, is also acceptable; the LLM grader decides that case."
    },
    28: {"expected_behavior": "refuse"},  # "gives the real one or declines"
}
UNITS = {"diluted_eps": "USD/shares", "shares_outstanding": "shares"}
LINE = re.compile(r"^\s*([1-7])\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$")


def main() -> int:
    """Write the held-out file from the source lines and the fields above."""
    lines = [
        m for line in SOURCE.read_text(encoding="utf-8").splitlines() if (m := LINE.match(line))
    ]
    if len(lines) != len(FIELDS):
        print(f"the source has {len(lines)} question lines; FIELDS has {len(FIELDS)}")
        return 1
    rows = []
    for n, (m, (company, year, metric, behavior)) in enumerate(zip(lines, FIELDS, strict=True), 1):
        rows.append(
            {
                "id": f"held-{n:03d}",
                "set": "trap",
                "category": CATEGORIES[m[1]],
                "question": m[2],
                "company": company,
                "fiscal_year": year,
                "metric": metric,
                "expected_behavior": behavior,
                "gold_value": None,
                "gold_unit": UNITS.get(metric or "", "USD") if behavior == "answer" else None,
                "tolerance_pct": 1.0,
                "gold_text": None,
                "trap_note": m[3],
            }
            | ({"also_accept": ALSO_ACCEPT[n]} if n in ALSO_ACCEPT else {})
        )
    OUT.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(rows)} questions written to {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
