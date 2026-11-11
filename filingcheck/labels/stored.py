"""Label every stored agent answer in the repo, for the independent re-check of the labeler.

`python -m filingcheck.labels.stored` reads the agent rows in `eval/results/` and
`eval/probes/` and the page examples in `web/data/examples.json`, rebuilds each row's sources
from what the row recorded, labels its figures, and writes one line per figure to
`eval/labels/<date>_stored-answers.jsonl` with a summary page beside it. No model is called;
the passages' text and the filings' facts come from the local database, read-only.

Where a row did not record the facts its run returned (some probe rows kept only each call's
arguments), they are looked up again from those arguments: the arguments are the ones the
tool ran with, after any repair, and the facts and the lookup have not changed since. Such
rows are marked `facts_from: "looked up again"`.
"""

import argparse
import json
import sys
from collections import Counter
from collections.abc import Callable, Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv

from filingcheck.answer.citations import cited_numbers, parse_fact_citations
from filingcheck.console import use_utf8_output
from filingcheck.db import connect
from filingcheck.facts.lookup import FactResult, PostgresFacts, lookup
from filingcheck.labels.label import (
    FilingFacts,
    NumberLabel,
    SourceCalculation,
    SourceFact,
    SourcePassage,
    Sources,
    label_numbers,
)
from filingcheck.paths import REPO_ROOT
from filingcheck.tools.calculate import CalculateInput, CalculationError, calculate

FactsFrom = Literal["recorded", "looked up again", "none"]
PassageText = Callable[[list[int]], dict[int, str]]
LookupFact = Callable[[str, int, str], FactResult | None]

# The highest passage number a stored answer's markers are read up to.
MAX_PASSAGE = 100
COLUMNS = (
    ("verified", "fact"),
    ("verified", "fact_other_period"),
    ("verified", "calculation"),
    ("verified", "passage"),
    ("conflict", None),
    ("unverified", None),
)
HEADINGS = (
    "Verified, fact",
    "Verified, other period",
    "Verified, calculation",
    "Verified, passage",
    "Conflict",
    "Unverified",
)


def is_agent_answer(row: dict[str, Any]) -> bool:
    """An agent row with a final answer: the rows the labels are for."""
    answer = row.get("answer")
    return row.get("mode") == "agent" and isinstance(answer, str) and bool(answer.strip())


def page_example_rows(examples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The saved page examples as rows like the eval rows."""
    rows = []
    for n, example in enumerate(examples, 1):
        answer = example["answer"]
        rows.append(
            {
                "id": f"page-{n}",
                "repeat": 1,
                "question": example["question"],
                "mode": answer.get("mode"),
                "answer": answer.get("text"),
                "facts_used": answer.get("facts_used"),
                "citations": answer.get("citations", []),
                "tool_calls": answer.get("tool_calls", []),
                "grade": None,
            }
        )
    return rows


def _date(text: str | None) -> date | None:
    return date.fromisoformat(text) if text else None


def _source_fact(number: int, fact: dict[str, Any]) -> SourceFact:
    return SourceFact(
        number=number,
        concept=fact["concept"],
        value=Decimal(str(fact["value"])),
        unit=fact["unit"],
        period_start=_date(fact.get("period_start")),
        period_end=_date(fact.get("period_end")),
        instant=_date(fact.get("instant")),
        accession=fact["accession"],
    )


def _looked_up(row: dict[str, Any], lookup_fact: LookupFact) -> list[dict[str, Any]]:
    """The facts the run's successful lookups returned, each distinct fact once, in order."""
    found: list[dict[str, Any]] = []
    keys: list[tuple[Any, ...]] = []
    for call in row.get("tool_calls") or []:
        if call.get("name") != "get_financial_fact" or call.get("status") != "ok":
            continue
        arguments = call.get("arguments") or {}
        result = lookup_fact(arguments["ticker"], arguments["fiscal_year"], arguments["metric"])
        if result is None:
            continue
        fact = json.loads(result.model_dump_json())
        key = tuple(
            fact[k] for k in ("accession", "concept", "period_start", "period_end", "instant")
        )
        if key not in keys:
            keys.append(key)
            found.append(fact)
    return found


def _cited_chunks(row: dict[str, Any]) -> list[tuple[int, int]]:
    """(passage number, chunk id) for each passage the row records as cited."""
    answer = row["answer"]
    if isinstance(row.get("citations"), list):
        citations = row["citations"]
        if all("number" in c for c in citations):
            return [(c["number"], c["chunk_id"]) for c in citations]
        numbers = cited_numbers(answer, MAX_PASSAGE)
        return [(n, c["chunk_id"]) for n, c in zip(numbers, citations, strict=False)]
    chunks = row.get("cited_chunks")
    if isinstance(chunks, list):
        numbers = cited_numbers(answer, MAX_PASSAGE)
        if len(numbers) == len(chunks):
            return list(zip(numbers, chunks, strict=True))
    return []


def _unresolved(answer: str, passages: set[int], facts: int) -> list[str]:
    """Notes on the answer's markers that point to no recorded passage or fact."""
    notes = []
    missing = [n for n in cited_numbers(answer, MAX_PASSAGE) if n not in passages]
    if missing:
        notes.append(f"passage markers {missing} have no recorded passage")
    dead = [n for n in parse_fact_citations(answer, MAX_PASSAGE) if n > facts]
    if dead:
        names = ", ".join(f"F{n}" for n in dead)
        notes.append(f"fact markers [{names}] have no fact (the run has {facts})")
    return notes


def sources_for_row(
    row: dict[str, Any],
    *,
    passage_text: PassageText,
    lookup_fact: LookupFact,
    filing_facts: FilingFacts | None,
) -> tuple[Sources, FactsFrom, list[str]]:
    """The row's sources, where its facts came from, and notes on anything missing."""
    recorded = row.get("facts_used")
    facts_from: FactsFrom
    notes: list[str] = []
    if isinstance(recorded, list) and all(isinstance(f, dict) for f in recorded):
        facts, facts_from = recorded, "recorded"
    else:
        facts = _looked_up(row, lookup_fact)
        fact_calls = any(c.get("name") == "get_financial_fact" for c in row.get("tool_calls") or [])
        facts_from = "looked up again" if fact_calls else "none"
        if isinstance(recorded, list):  # only the values were recorded: they must agree
            found = [str(f["value"]) for f in facts]
            if [str(v) for v in recorded] != found:
                notes.append(
                    f"the facts looked up again ({', '.join(found)}) differ from the recorded "
                    f"values ({', '.join(str(v) for v in recorded)})"
                )
    cited = _cited_chunks(row)
    notes += _unresolved(row["answer"], {n for n, _ in cited}, len(facts))
    texts = passage_text([chunk for _, chunk in cited]) if cited else {}
    calculations = []
    for call in row.get("tool_calls") or []:
        if call.get("name") == "calculate" and call.get("status") == "ok":
            expression = (call.get("arguments") or {}).get("expression", "")
            try:
                value = calculate(CalculateInput(expression=expression)).value
            except (CalculationError, ValueError):
                continue
            calculations.append(SourceCalculation(expression=expression, value=value))
    sources = Sources(
        facts=[_source_fact(n, f) for n, f in enumerate(facts, 1)],
        passages=[SourcePassage(number=n, text=texts[chunk]) for n, chunk in cited],
        calculations=calculations,
        filing_facts=filing_facts,
    )
    return sources, facts_from, notes


def stored_rows(root: Path) -> Iterator[tuple[str, dict[str, Any]]]:
    """(file, row) for every stored agent answer, the eval results first."""
    for folder in ("eval/results", "eval/probes"):
        for path in sorted((root / folder).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    if is_agent_answer(row):
                        yield f"{folder}/{path.name}", row
    examples = json.loads((root / "web/data/examples.json").read_text(encoding="utf-8"))
    for row in page_example_rows(examples):
        if is_agent_answer(row):
            yield "web/data/examples.json", row


def _grade(row: dict[str, Any]) -> str:
    grade = row.get("grade")
    return grade["outcome"] if isinstance(grade, dict) and "outcome" in grade else "not graded"


def _line(file: str, row: dict[str, Any], facts_from: FactsFrom, label: NumberLabel) -> str:
    out = {
        "row": f"{file}:{row['id']}:{row.get('repeat', 1)}",
        "grade": _grade(row),
        "facts_from": facts_from,
        **json.loads(label.model_dump_json()),
    }
    return json.dumps(out, ensure_ascii=False)


def summary(lines: list[dict[str, Any]], answers: Counter[str], notes: list[str]) -> str:
    """The summary page: labels by the row's deterministic grade, and what was counted."""
    grades = sorted({line["grade"] for line in lines}, key=lambda g: (g == "not graded", g))
    table = ["| Grade of the row | " + " | ".join(HEADINGS) + " | Figures |"]
    table.append("|---|" + "---:|" * (len(HEADINGS) + 1))
    for grade in [*grades, "All"]:
        rows = [line for line in lines if grade in ("All", line["grade"])]
        counts = [sum(1 for r in rows if (r["label"], r["basis"]) == column) for column in COLUMNS]
        name = f"**{grade}**" if grade == "All" else grade
        table.append(f"| {name} | " + " | ".join(map(str, counts)) + f" | {len(rows)} |")
    looked_up = sum(1 for line in lines if line["facts_from"] == "looked up again")
    parts = [
        "# Number labels on the stored answers",
        "",
        "Written by `python -m filingcheck.labels.stored`; do not edit by hand. One line per "
        "figure is in the `.jsonl` file of the same name.",
        "",
        f"- **Answers labeled:** {answers['answers']}, from {answers['files']} files "
        f"(agent rows with a final answer; baseline rows are not labeled).",
        f"- **Answers with at least one figure:** {answers['with figures']}; "
        f"**figures:** {len(lines)}.",
        f"- **Figures whose facts were looked up again** from the recorded arguments, because the "
        f"row did not record them: {looked_up}.",
        "",
        *table,
        "",
        "Verified means the figure is in a cited SEC source; it does not prove the sentence uses "
        "it correctly. The grade column is the deterministic grade stored with the row.",
    ]
    if notes:
        parts += ["", "## Rows with something missing", "", *notes]
    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Label every stored agent answer and write the jsonl and its summary page."""
    use_utf8_output()
    parser = argparse.ArgumentParser(prog="python -m filingcheck.labels.stored")
    parser.add_argument("--out-dir", type=Path, default=REPO_ROOT / "eval" / "labels")
    parser.add_argument("--date", default=date.today().isoformat())
    args = parser.parse_args(argv)
    load_dotenv(REPO_ROOT / ".env")
    lines: list[str] = []
    answers: Counter[str] = Counter()
    files: set[str] = set()
    notes: list[str] = []
    with connect() as conn:
        facts_source = PostgresFacts(conn)

        def passage_text(ids: list[int]) -> dict[int, str]:
            rows = conn.execute("SELECT id, text FROM chunks WHERE id = ANY(%s)", (ids,))
            return {int(i): str(t) for i, t in rows.fetchall()}

        def lookup_fact(ticker: str, fiscal_year: int, metric: str) -> FactResult | None:
            return lookup(facts_source, ticker, fiscal_year, metric)

        for file, row in stored_rows(REPO_ROOT):
            sources, facts_from, row_notes = sources_for_row(
                row, passage_text=passage_text, lookup_fact=lookup_fact, filing_facts=facts_source
            )
            labels = label_numbers(row["answer"], sources)
            answers["answers"] += 1
            answers["with figures"] += bool(labels)
            files.add(file)
            notes += [f"- `{file}:{row['id']}:{row.get('repeat', 1)}`: {n}" for n in row_notes]
            lines += [_line(file, row, facts_from, label) for label in labels]
    answers["files"] = len(files)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    base = args.out_dir / f"{args.date}_stored-answers"
    base.with_suffix(".jsonl").write_text(
        "".join(line + "\n" for line in lines), encoding="utf-8", newline="\n"
    )
    page = summary([json.loads(line) for line in lines], answers, notes)
    base.with_suffix(".md").write_text(page, encoding="utf-8", newline="\n")
    print(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
