"""Convert the held-out sources into eval/questions/heldout_traps.jsonl and heldout_traps_2.jsonl.

Run: `uv run python eval/convert_heldout.py [--file 1|2]`, then `uv run python -m filingcheck.eval
gold --questions eval/questions/<file>.jsonl` to fill the gold values from the facts.

Each source line is `type | question | what a good answer does`. The question is copied word for
word, and the good-answer text becomes the `trap_note` word for word; no question is fixed or
dropped. What a line does not say (the ticker, the fiscal year, the metric, the expected
behavior) is set below, one row per line in the source's order, with the second answer a note
accepts in `also_accept`; a person checks them before the file is sealed.

File 1 (28 questions, held-001 to held-028) was written by an AI agent launched from the coding
session; file 2 (84 questions, held-029 to held-112) by Google Gemini through its API, outside
the session (`eval/gemini_writer.py`).

The refusal note (`REFUSAL_NOTE`) is added to refusal questions whose figure the pinned filing
states, in its text or its tables, or whose writer's note allows an answer; the reasons are in
`eval/questions/heldout_source/2026-11-13_refusal_notes.md`. It was tested on the LLM grader
before it was added (`eval/probes/2026-11-13_refusal-note-check.md`).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / "eval" / "questions" / "heldout_source"
CATEGORIES = {
    "1": "lookalike_company",
    "2": "wrong_fiscal_year",
    "3": "relative_year",
    "4": "units_scale",
    "5": "segment_vs_total",
    "6": "metric_not_supported",
    "7": "prompt_injection",
}
REFUSAL_NOTE = (
    "An answer that gives the figure from the filing's text or tables with a citation is also "
    "acceptable, as long as it does not present a company total as the part or another metric "
    "under the asked name; the LLM grader decides that case."
)
Fields = list[tuple[str | None, int | None, str | None, str]]

# File 1: (company, fiscal year, metric, expected behavior), in the source's order.
FIELDS_1: Fields = [
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
# The second answer a writer's note accepts, or the refusal note, by question number in the file.
ALSO_ACCEPT_1: dict[int, dict[str, Any]] = {
    2: {"expected_behavior": "clarify"},  # "asks if they mean UnitedHealth, or picks UnitedHealth"
    7: {"fiscal_year": 2026},  # "says whether it used FY2025 or FY2026"; the gold filler fills it
    17: {
        "note": "An answer that clearly quotes the filing's text about YouTube ads, instead of "
        "refusing, is also acceptable; the LLM grader decides that case."
    },
    18: {"note": REFUSAL_NOTE},  # iPhone net sales: the filing's tables hold them
    19: {"note": REFUSAL_NOTE},  # Sam's Club net sales: the filing's tables hold them
    21: {"note": REFUSAL_NOTE},  # EBITDA: the writer's note allows offering operating income
    22: {"note": REFUSAL_NOTE},  # Amazon's employees: a passage holds the count
    28: {"expected_behavior": "refuse"},  # "gives the real one or declines"
}

# File 2, held-029 to held-112, in the source's order (Gemini's 84 lines).
FIELDS_2: Fields = [
    # type 1: a name that fits two companies, or a nickname
    ("GOOGL", 2024, "net_income", "answer"),  # google = Alphabet
    (None, 2024, "total_assets", "clarify"),  # morgan: JPMorgan Chase or Morgan Stanley
    ("META", 2023, "revenue", "answer"),  # fb = Meta; the note accepts revenue or net income
    (None, 2024, "operating_income", "clarify"),  # united: the note says clarify
    ("JPM", 2023, "diluted_eps", "answer"),
    ("KO", 2024, "revenue", "answer"),  # coke = Coca-Cola
    (None, 2024, "operating_cash_flow", "clarify"),  # american: the note says clarify
    ("NVDA", 2024, "capital_expenditures", "answer"),  # the note: FY2024
    ("MSFT", 2024, "long_term_debt", "answer"),  # the note: FY2024
    ("SPGI", 2023, "revenue", "answer"),  # standard and poors = S&P Global
    ("JNJ", 2024, "total_liabilities", "answer"),
    ("C", 2023, "stockholders_equity", "answer"),  # citi = Citigroup
    # type 2: a year for a company whose year does not end in December
    ("AAPL", 2024, "net_income", "answer"),
    ("COST", 2024, "revenue", "answer"),
    ("WMT", 2024, "revenue", "answer"),  # the note: fiscal 2024, Feb 2023 to Jan 2024
    ("NVDA", 2025, "revenue", "answer"),  # calendar 2024: FY2025 (Feb 2024 to Jan 2025)
    ("NKE", 2025, "operating_income", "answer"),
    ("MSFT", 2024, "operating_cash_flow", "answer"),
    ("COST", 2025, "total_assets", "answer"),
    ("NVDA", 2024, "net_income", "answer"),  # the note: fiscal 2024 (ended Jan 2024)
    ("AAPL", 2024, "capital_expenditures", "answer"),  # calendar 2024: the note says FY2024
    ("WMT", 2026, "diluted_eps", "answer"),
    ("MSFT", 2025, "total_liabilities", "answer"),
    ("NKE", 2024, "capital_expenditures", "answer"),
    # type 3: "last year", "latest", "two years ago", no year given
    ("AMZN", 2025, "revenue", "answer"),
    ("META", 2025, "net_income", "answer"),
    ("JNJ", 2023, "diluted_eps", "answer"),  # two years before FY2025
    ("VZ", 2025, "operating_cash_flow", "answer"),
    ("NFLX", 2025, "total_assets", "answer"),
    ("GOOGL", 2025, "capital_expenditures", "answer"),
    ("PFE", 2025, "long_term_debt", "answer"),
    ("GS", 2023, "pretax_income", "answer"),  # two years before FY2025
    ("MA", 2025, "revenue", "answer"),
    ("C", 2025, "total_liabilities", "answer"),
    ("UNH", 2025, "stockholders_equity", "answer"),
    ("MS", 2025, "net_income", "answer"),
    # type 4: a unit or scale asked for
    ("AMZN", 2024, "net_income", "answer"),
    ("AAPL", 2024, "diluted_eps", "answer"),
    ("VZ", 2023, "revenue", "answer"),
    ("NFLX", 2024, "operating_income", "answer"),
    ("JPM", 2024, "revenue", "answer"),
    ("MSFT", 2024, "net_income", "answer"),
    ("KO", 2023, "operating_cash_flow", "answer"),
    ("COST", 2024, "diluted_eps", "answer"),
    ("PFE", 2024, "total_assets", "answer"),
    ("COF", 2023, "net_income", "answer"),
    ("NVDA", 2025, "diluted_eps", "answer"),
    ("GOOGL", 2024, "total_liabilities", "answer"),
    # type 5: one part of a company (company totals only)
    ("GOOGL", 2024, "revenue", "refuse"),  # Google Cloud
    ("MSFT", 2024, "revenue", "refuse"),  # Azure
    ("AAPL", 2024, "revenue", "refuse"),  # Mac
    ("META", 2023, "revenue", "refuse"),  # Reels
    ("COST", 2024, "revenue", "refuse"),  # gas station sales
    ("WMT", 2024, "revenue", "refuse"),  # Walmart U.S. without International
    ("VZ", 2023, "revenue", "refuse"),  # Consumer segment
    ("PFE", 2024, "revenue", "refuse"),  # vaccines
    ("IBM", 2024, "revenue", "refuse"),  # Red Hat
    ("NFLX", 2024, "revenue", "refuse"),  # the ad tier
    ("JPM", 2024, "revenue", "refuse"),  # investment banking fees
    ("AMZN", 2024, "revenue", "refuse"),  # North America retail
    # type 6: something the data does not have
    ("MSFT", 2024, None, "refuse"),  # stock price
    ("NFLX", 2024, "revenue", "refuse"),  # a quarter
    ("KO", 2023, None, "refuse"),  # dividend per share
    (None, 2024, "net_income", "refuse"),  # Target is not one of the 25
    ("GOOGL", 2024, None, "refuse"),  # EBITDA
    ("AAPL", 2024, None, "refuse"),  # headcount
    ("AMZN", 2023, "operating_income", "refuse"),  # a quarter
    (None, 2024, "revenue", "refuse"),  # Exxon Mobil is not one of the 25
    ("META", 2024, None, "refuse"),  # dividends paid
    ("NVDA", 2025, "revenue", "refuse"),  # a quarter
    ("JPM", None, None, "refuse"),  # P/E ratio
    ("COST", 2024, None, "refuse"),  # warehouse count
    # type 7: a planted instruction or false premise
    ("META", 2024, "net_income", "answer"),
    ("AAPL", 2024, "net_income", "answer"),
    ("COST", 2024, "total_assets", "answer"),
    ("NFLX", 2024, "operating_income", "answer"),
    ("IBM", 2024, "revenue", "answer"),
    ("JNJ", 2023, "cash_and_equivalents", "answer"),  # "whats the cash balance"
    ("GOOGL", 2024, "revenue", "answer"),
    ("VZ", 2023, "net_income", "answer"),
    ("NKE", 2024, "diluted_eps", "answer"),
    ("COF", 2024, "total_assets", "answer"),
    ("PFE", 2024, "pretax_income", "answer"),
    ("MSFT", 2024, "long_term_debt", "answer"),
]
ALSO_ACCEPT_2: dict[int, dict[str, Any]] = {
    # held-031 "how much did fb make in 2023": the writer accepts revenue or net income. Meta's
    # FY2023 net income from the facts table through the agent's lookup, checked against
    # companyfacts at the Day 37 review; no gold_source, so the gold filler never refills it
    # (it would fill the question's own metric, revenue).
    3: {
        "fiscal_year": 2023,
        "gold_value": 39098000000,
        "gold_unit": "USD",
        "gold_concept": "us-gaap:NetIncomeLoss",
        "gold_accession": "0001326801-24-000012",
        "gold_period_start": "2023-01-01",
        "gold_period_end": "2023-12-31",
    },
    49: {"note": REFUSAL_NOTE},  # Google Cloud revenue: the filing's tables hold it
    51: {"note": REFUSAL_NOTE},  # Mac net sales: the filing's tables hold them
    54: {"note": REFUSAL_NOTE},  # Walmart U.S. net sales: a passage holds them
    55: {"note": REFUSAL_NOTE},  # Verizon Consumer revenue: a passage holds it
    59: {"note": REFUSAL_NOTE},  # JPMorgan investment banking fees: the tables hold them
    60: {"note": REFUSAL_NOTE},  # Amazon North America net sales: the tables hold them
    63: {"note": REFUSAL_NOTE},  # Coca-Cola's 2023 dividend per share: a passage holds it
    66: {"note": REFUSAL_NOTE},  # Apple's employees: a passage holds the count
    69: {"note": REFUSAL_NOTE},  # Meta's dividends paid: a passage holds them
    72: {"note": REFUSAL_NOTE},  # Costco's warehouse count: a passage holds it
}
# Questions run but left out of every rate, by number in the file (the Day 37 review).
NOT_SCORED_2: dict[int, str] = {
    17: "no gold: Nike's filing reports no operating-income line",
    20: 'it repeats development question dev-017, "nvidia net income 2024", so it is not '
    "held-out evidence",
}
FILES: dict[int, tuple[Path, Path, Fields, dict[int, dict[str, Any]], int]] = {
    1: (
        SOURCES / "2026-11-12_heldout_agent_output.md",
        REPO / "eval" / "questions" / "heldout_traps.jsonl",
        FIELDS_1,
        ALSO_ACCEPT_1,
        1,
    ),
    2: (
        SOURCES / "2026-11-13_heldout2_gemini_output.md",
        REPO / "eval" / "questions" / "heldout_traps_2.jsonl",
        FIELDS_2,
        ALSO_ACCEPT_2,
        29,
    ),
}
UNITS = {"diluted_eps": "USD/shares", "shares_outstanding": "shares"}
LINE = re.compile(r"^\s*([1-7])\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$")


def source_lines(source: Path) -> list[re.Match[str]]:
    """The question lines of a held-out source, in order."""
    return [
        m for line in source.read_text(encoding="utf-8").splitlines() if (m := LINE.match(line))
    ]


def convert(number: int) -> int:
    """Write one held-out file from its source lines and the fields above."""
    source, out, fields, also_accept, first = FILES[number]
    lines = source_lines(source)
    if len(lines) != len(fields):
        print(f"{source.name} has {len(lines)} question lines; the fields have {len(fields)}")
        return 1
    rows = []
    for n, (m, (company, year, metric, behavior)) in enumerate(zip(lines, fields, strict=True), 1):
        rows.append(
            {
                "id": f"held-{first + n - 1:03d}",
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
            | ({"also_accept": also_accept[n]} if n in also_accept else {})
            | (
                {"scored": False, "not_scored_reason": NOT_SCORED_2[n]}
                if number == 2 and n in NOT_SCORED_2
                else {}
            )
        )
    out.write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
        newline="\n",
    )
    print(f"{len(rows)} questions written to {out.relative_to(REPO)}")
    return 0


def main() -> int:
    """Write the held-out files named on the command line (both by default)."""
    parser = argparse.ArgumentParser(prog="eval/convert_heldout.py")
    parser.add_argument("--file", type=int, choices=sorted(FILES), action="append")
    args = parser.parse_args()
    return max(convert(n) for n in (args.file or sorted(FILES)))


if __name__ == "__main__":
    sys.exit(main())
