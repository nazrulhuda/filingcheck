"""Does a reference ("passage 1", "Item 7", "Note 8") change a stored outcome or label (Day 36 b)?

Run: `uv run python eval/reference_audit.py`; it prints the counts and writes
`eval/probes/<date>_reference-audit.md`. No model call, no database.

For every stored row with an answer, grade the answer as stored and with each reference's number
blanked, and compare the outcome. For labels, list every stored number label whose figure sits
inside a reference.
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from filingcheck.eval.grade import find_numbers, grade
from filingcheck.eval.questions import Question

REF = re.compile(
    r"\b(?:passages?|items?|notes?|exhibits?|pages?|sections?|parts?|schedules?|footnotes?|"
    r"articles?|rules?|tables?)\s+\d+[A-Za-z]?(?:(?:\s*(?:,|and|&|-|to)\s*)\d+[A-Za-z]?)*",
    re.IGNORECASE,
)


def blank(text: str) -> str:
    """The text with every reference's digits replaced by X."""
    return REF.sub(lambda m: re.sub(r"\d", "X", m.group(0)), text)


sets: dict[str, Question] = {}
for f in Path("eval/questions").glob("*.jsonl"):
    if f.name in ("retrieval.jsonl", "page_examples.jsonl"):
        continue
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            q = Question.model_validate_json(line)
            sets.setdefault(q.id, q)


def probe_question(row: dict[str, Any]) -> Question | None:
    """A probe row's number question, from its own company, year, metric and gold."""
    gold = row.get("gold")
    if not (row.get("question") and row.get("company") and row.get("fiscal_year")):
        return None
    return Question.model_validate(
        {
            "id": "probe-001",
            "set": "trap",
            "category": "wrong_fiscal_year",
            "question": row["question"],
            "company": row["company"],
            "fiscal_year": row["fiscal_year"],
            "metric": row.get("metric"),
            "expected_behavior": "answer",
            "gold_value": int(gold) if gold is not None else None,
            "gold_unit": "USD" if gold is not None else None,
        }
    )


rows_seen = 0
with_refs = 0
changed = []
label_hits = []
for folder in ("eval/results", "eval/probes"):
    for path in sorted(Path(folder).glob("*.jsonl")):
        if path.stem.endswith("_llm") or "regrade" in path.name:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            text = row.get("answer")
            if not isinstance(text, str) or not text:
                continue
            rows_seen += 1
            refs = list(REF.finditer(text))
            if not refs:
                continue
            with_refs += 1
            found: Question | None = (
                sets.get(row["id"]) if folder == "eval/results" else probe_question(row)
            )
            question = found or sets.get(row["id"])
            if question is not None:
                before = grade(row, question)
                after = grade({**row, "answer": blank(text)}, question)
                if (before.outcome, before.lenient_outcome, before.matched) != (
                    after.outcome,
                    after.lenient_outcome,
                    after.matched,
                ):
                    changed.append(
                        (path.name, row["id"], row.get("repeat", 1), before.outcome, after.outcome)
                    )
            for label in row.get("number_labels") or []:
                figure = str(label.get("figure", ""))
                for m in refs:
                    if (
                        figure
                        and figure in m.group(0)
                        and re.fullmatch(r"\d+[A-Za-z]?", figure.strip())
                    ):
                        label_hits.append(
                            (
                                path.name,
                                row["id"],
                                row.get("repeat", 1),
                                figure,
                                label.get("label"),
                                m.group(0),
                            )
                        )

# Do reference numbers ever come out as amounts?
amounts_in_refs = []
for folder in ("eval/results", "eval/probes"):
    for path in sorted(Path(folder).glob("*.jsonl")):
        if path.stem.endswith("_llm") or "regrade" in path.name:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            text = row.get("answer")
            if not isinstance(text, str):
                continue
            plain = {n.value for n in find_numbers(text) if n.amount}
            plain_blank = {n.value for n in find_numbers(blank(text)) if n.amount}
            if plain != plain_blank:
                amounts_in_refs.append(
                    (
                        path.name,
                        row["id"],
                        row.get("repeat", 1),
                        sorted(map(str, plain - plain_blank)),
                    )
                )

lines = [
    "# References read as figures: an audit of the stored rows",
    "",
    "Every stored answer in `eval/results/` and `eval/probes/` graded as stored and with each "
    'reference\'s digits blanked ("passage 1", "Item 7", "Note 8" and the like), and every '
    "stored number label checked for a figure inside a reference. Written by "
    "`eval/reference_audit.py`.",
    "",
    f"- Answers: {rows_seen}; with a reference: {with_refs}.",
    f"- Outcomes that change when the references are blanked: {len(changed)}.",
    f"- Answers where a reference number is read as an amount: {len(amounts_in_refs)}.",
    f"- Number labels whose figure is a reference number: {len(label_hits)}.",
    "",
    "A reference comes out of the reader as a plain number, which no grading or labelling rule "
    "uses, so the reader is left as it is (the labeler shares it). The case first blamed on "
    '"passage 1" (dev-050) fails for a different reason: the refusal quotes a percentage, '
    "and the refuse rule counts a percentage as an amount.",
]
today = datetime.now(UTC).date().isoformat()
out = Path(__file__).resolve().parents[1] / "eval" / "probes" / f"{today}_reference-audit.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"rows with an answer: {rows_seen}; with a reference: {with_refs}")
print(f"outcomes that change when references are blanked: {len(changed)}")
for c in changed:
    print("  ", c)
print(f"rows where a reference number is read as an amount: {len(amounts_in_refs)}")
for a in amounts_in_refs[:20]:
    print("  ", a)
print(f"number labels whose figure is a reference number: {len(label_hits)}")
for h in label_hits[:20]:
    print("  ", h)
